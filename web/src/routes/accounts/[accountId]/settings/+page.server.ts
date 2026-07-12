import { redirect } from '@sveltejs/kit';
import { setAccountRoundUp } from '$lib/queries.js';

export const actions = {
    toggle_round_up: async ({ request, params }) => {
        const accountId = parseInt(params.accountId, 10);
        const data = await request.formData();
        const enabled = data.get('enabled') === '1';
        const since = enabled ? new Date().toISOString().slice(0, 10) : null;
        setAccountRoundUp(accountId, since);
        redirect(303, `/accounts/${accountId}/settings`);
    }
};
