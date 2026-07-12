import { error, fail, redirect } from '@sveltejs/kit';
import {
    getAccount,
    getEnvelopes,
    buildEnvelopeTree,
    getEnvelopeGroups,
    getUnallocatedTransactions,
    getUnallocatedWithdrawals,
    createEnvelope,
    createGroup,
    renameGroup,
    deleteGroup,
    setGroupTint,
    moveEnvelopeToGroup,
    allocateSplit,
    allocateWithdrawal,
    createWithdrawal,
    getSplitsWithStatus,
    createSplit,
    deleteSplit,
    setGoal,
    removeGoal,
    renameEnvelope,
    deleteEnvelope
} from '$lib/queries.js';
import {
    AlreadyAllocatedError,
    SplitValidationError,
    WithdrawalAlreadyAllocatedError,
    EnvelopeHasAllocationsError,
    type EnvelopeWithdrawal,
    type SplitWithStatus,
    type Transaction
} from '$lib/types.js';

export type QueueItem =
    | { kind: 'withdrawal'; withdrawal: EnvelopeWithdrawal }
    | { kind: 'transaction'; tx: Transaction; splits: SplitWithStatus[] };

export function load({ params, url }) {
    const accountId = parseInt(params.accountId, 10);

    const account = getAccount(accountId);
    if (!account) error(404, 'Account not found');

    const envelopes = getEnvelopes(accountId);
    const tree = buildEnvelopeTree(accountId);
    const groups = getEnvelopeGroups(accountId);

    const unallocatedWithdrawals = getUnallocatedWithdrawals(accountId);
    const unallocatedTransactions = getUnallocatedTransactions(accountId);

    const queue: QueueItem[] = [
        ...unallocatedWithdrawals.map((w): QueueItem => ({ kind: 'withdrawal', withdrawal: w })),
        ...unallocatedTransactions.map((tx): QueueItem => ({ kind: 'transaction', tx, splits: [] }))
    ];

    const mode = queue.length > 0 ? 'allocate' : 'clean';

    const txParam = url.searchParams.get('tx');
    const rawIndex = txParam !== null ? parseInt(txParam, 10) : 0;
    const currentItemIndex = queue.length > 0 ? Math.max(0, Math.min(rawIndex, queue.length - 1)) : 0;

    let currentItem: QueueItem | null = queue[currentItemIndex] ?? null;
    if (currentItem?.kind === 'transaction') {
        currentItem = {
            kind: 'transaction',
            tx: currentItem.tx,
            splits: getSplitsWithStatus(currentItem.tx.id)
        };
    }

    return { account, envelopes, tree, groups, queue, mode, currentItemIndex, currentItem };
}

export const actions = {
    allocate: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const splitId = parseInt(data.get('split_id') as string, 10);
        const currentIndex = parseInt((data.get('current_index') as string) ?? '0', 10);

        if (isNaN(envelopeId) || isNaN(splitId)) return fail(400, { error: 'Invalid input' });

        try {
            allocateSplit(envelopeId, splitId);
        } catch (err) {
            if (err instanceof AlreadyAllocatedError) return fail(409, { error: err.message });
            throw err;
        }

        const total = getUnallocatedWithdrawals(accountId).length + getUnallocatedTransactions(accountId).length;
        const nextIndex = Math.min(currentIndex, Math.max(0, total - 1));
        redirect(303, `/accounts/${accountId}?tx=${nextIndex}`);
    },

    allocate_withdrawal: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const withdrawalId = parseInt(data.get('withdrawal_id') as string, 10);
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const currentIndex = parseInt((data.get('current_index') as string) ?? '0', 10);

        if (isNaN(withdrawalId) || isNaN(envelopeId)) return fail(400, { error: 'Invalid input' });

        try {
            allocateWithdrawal(withdrawalId, envelopeId);
        } catch (err) {
            if (err instanceof WithdrawalAlreadyAllocatedError) return fail(409, { error: err.message });
            throw err;
        }

        const total = getUnallocatedWithdrawals(accountId).length + getUnallocatedTransactions(accountId).length;
        const nextIndex = Math.min(currentIndex, Math.max(0, total - 1));
        redirect(303, `/accounts/${accountId}?tx=${nextIndex}`);
    },

    withdraw: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const amount = (data.get('amount') as string)?.trim();
        const note = (data.get('note') as string)?.trim() || null;

        if (isNaN(envelopeId) || !amount) return fail(400, { error: 'Invalid input' });

        try {
            createWithdrawal(envelopeId, amount, note);
        } catch (err) {
            if (err instanceof SplitValidationError) return fail(422, { error: err.message });
            throw err;
        }

        redirect(303, `/accounts/${accountId}?tx=0`);
    },

    create_envelope: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const name = (data.get('name') as string)?.trim();
        const groupRaw = data.get('group_id') as string | null;
        const groupId = groupRaw ? parseInt(groupRaw, 10) : null;

        if (!name) return fail(400, { error: 'Envelope name is required' });

        try {
            createEnvelope(accountId, name, groupId != null && !isNaN(groupId) ? groupId : null);
        } catch (err) {
            const e = err as { code?: string };
            if (e?.code === 'SQLITE_CONSTRAINT_UNIQUE') {
                return fail(409, { error: `An envelope named "${name}" already exists` });
            }
            throw err;
        }

        redirect(303, `/accounts/${accountId}`);
    },

    create_group: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const name = (data.get('name') as string)?.trim();
        const parentRaw = data.get('parent_id') as string | null;
        const parentId = parentRaw ? parseInt(parentRaw, 10) : null;
        const tint = ((data.get('tint') as string) || 'budget').trim();

        if (!name) return fail(400, { error: 'Group name is required' });

        createGroup(accountId, name, parentId != null && !isNaN(parentId) ? parentId : null, tint);
        redirect(303, `/accounts/${accountId}`);
    },

    rename_group: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const groupId = parseInt(data.get('group_id') as string, 10);
        const name = (data.get('name') as string)?.trim();
        const tint = (data.get('tint') as string)?.trim();

        if (isNaN(groupId)) return fail(400, { error: 'Invalid input' });
        if (name) renameGroup(groupId, name);
        if (tint) setGroupTint(groupId, tint);
        redirect(303, `/accounts/${accountId}`);
    },

    delete_group: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const groupId = parseInt(data.get('group_id') as string, 10);
        if (isNaN(groupId)) return fail(400, { error: 'Invalid input' });
        deleteGroup(groupId);
        redirect(303, `/accounts/${accountId}`);
    },

    move_envelope: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const groupRaw = data.get('group_id') as string | null;
        const groupId = groupRaw ? parseInt(groupRaw, 10) : null;
        if (isNaN(envelopeId)) return fail(400, { error: 'Invalid input' });
        moveEnvelopeToGroup(envelopeId, groupId != null && !isNaN(groupId) ? groupId : null);
        redirect(303, `/accounts/${accountId}`);
    },

    create_split: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const txId = parseInt(data.get('tx_id') as string, 10);
        const amount = (data.get('amount') as string)?.trim();
        const note = (data.get('note') as string)?.trim() || null;
        const currentIndex = parseInt((data.get('current_index') as string) ?? '0', 10);

        if (isNaN(txId) || !amount) return fail(400, { error: 'Invalid input' });

        try {
            createSplit(txId, amount, note);
        } catch (err) {
            if (err instanceof SplitValidationError) return fail(422, { error: err.message });
            throw err;
        }

        redirect(303, `/accounts/${accountId}?tx=${currentIndex}`);
    },

    delete_split: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const splitId = parseInt(data.get('split_id') as string, 10);
        const currentIndex = parseInt((data.get('current_index') as string) ?? '0', 10);

        if (isNaN(splitId)) return fail(400, { error: 'Invalid input' });

        try {
            deleteSplit(splitId);
        } catch (err) {
            if (err instanceof SplitValidationError) return fail(422, { error: err.message });
            throw err;
        }

        redirect(303, `/accounts/${accountId}?tx=${currentIndex}`);
    },

    rename_envelope: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const name = (data.get('name') as string)?.trim();

        if (isNaN(envelopeId)) return fail(400, { error: 'Invalid input' });
        if (!name) return fail(400, { error: 'Envelope name is required' });

        renameEnvelope(envelopeId, name);
        redirect(303, `/accounts/${accountId}`);
    },

    delete_envelope: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);

        if (isNaN(envelopeId)) return fail(400, { error: 'Invalid input' });

        try {
            deleteEnvelope(envelopeId);
        } catch (err) {
            if (err instanceof EnvelopeHasAllocationsError) return fail(409, { error: err.message });
            throw err;
        }

        redirect(303, `/accounts/${accountId}`);
    },

    set_goal: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const envelopeId = parseInt(data.get('envelope_id') as string, 10);
        const goalType = data.get('goal_type') as string;
        const amount = (data.get('amount') as string)?.trim();

        if (isNaN(envelopeId)) return fail(400, { error: 'Invalid input' });

        if (goalType === 'none') {
            removeGoal(envelopeId);
            redirect(303, `/accounts/${accountId}`);
        }

        const parsedAmount = parseFloat(amount);
        if (!amount || isNaN(parsedAmount) || parsedAmount <= 0) {
            return fail(400, { error: 'A valid target amount is required' });
        }
        const normalizedAmount = parsedAmount.toFixed(2);

        if (goalType === 'recurring') {
            const rrule = (data.get('rrule') as string)?.trim() || null;
            const dtstart = (data.get('dtstart') as string)?.trim() || null;
            if (!rrule || !dtstart) return fail(400, { error: 'Recurrence rule and start date are required' });
            setGoal(envelopeId, { amount: normalizedAmount, rrule, dtstart, dueDate: null });
        } else if (goalType === 'one_off') {
            const dueDate = (data.get('due_date') as string)?.trim() || null;
            if (!dueDate) return fail(400, { error: 'A due date is required' });
            setGoal(envelopeId, { amount: normalizedAmount, rrule: null, dtstart: null, dueDate });
        } else if (goalType === 'open_ended') {
            setGoal(envelopeId, { amount: normalizedAmount, rrule: null, dtstart: null, dueDate: null });
        } else {
            return fail(400, { error: 'Invalid goal type' });
        }

        redirect(303, `/accounts/${accountId}`);
    }
};
