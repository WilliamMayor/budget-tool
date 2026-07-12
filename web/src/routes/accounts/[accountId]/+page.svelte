<script lang="ts">
    import { enhance } from '$app/forms';
    import { goto } from '$app/navigation';
    import { formatCurrency, formatDate, formatSignedCurrency } from '$lib/format.js';
    import EnvelopeTree from '$lib/components/EnvelopeTree.svelte';
    import Card from '$lib/components/Card.svelte';
    import Button from '$lib/components/Button.svelte';
    import Modal from '$lib/components/Modal.svelte';
    import Field from '$lib/components/Field.svelte';
    import SelectField from '$lib/components/SelectField.svelte';

    let { data } = $props();
    const account = $derived(data.account);

    const earmarked = $derived(data.envelopes.reduce((sum, e) => sum + e.goal_balance, 0));

    // ---- Create modals -------------------------------------------------------
    let envModalOpen = $state(false);
    let envModalGroup = $state<number | null>(null);
    let grpModalOpen = $state(false);
    let grpModalParent = $state<number | null>(null);

    function addEnvelope(groupId: number | null = null) {
        envModalGroup = groupId;
        envModalOpen = true;
    }
    function addGroup(parentId: number | null = null) {
        grpModalParent = parentId;
        grpModalOpen = true;
    }

    // ---- Allocation queue ----------------------------------------------------
    let selectedSplitId = $state<number | null>(null);
    let showAddSplitForm = $state(false);

    const currentSplits = $derived(data.currentItem?.kind === 'transaction' ? data.currentItem.splits : []);
    const activeSplitId = $derived.by(() => {
        if (selectedSplitId !== null && currentSplits.some((s) => s.id === selectedSplitId && !s.is_allocated)) return selectedSplitId;
        return currentSplits.find((s) => !s.is_allocated)?.id ?? null;
    });
    const activeSplit = $derived(currentSplits.find((s) => s.id === activeSplitId) ?? null);

    const allocKind = $derived(
        data.currentItem?.kind === 'withdrawal' ? ('withdrawal' as const)
            : data.currentItem?.kind === 'transaction' ? ('split' as const) : null
    );
    const withdrawalId = $derived(data.currentItem?.kind === 'withdrawal' ? data.currentItem.withdrawal.id : null);
    const allocAmount = $derived.by(() => {
        if (data.currentItem?.kind === 'withdrawal') return parseFloat(data.currentItem.withdrawal.amount);
        if (activeSplit) return parseFloat(activeSplit.amount);
        return 0;
    });
    // Credits and withdrawals add to an envelope; debits subtract.
    const allocSign = $derived.by<1 | -1>(() => {
        if (data.currentItem?.kind === 'transaction') return data.currentItem.tx.credit_debit_indicator === 'CRDT' ? 1 : -1;
        return 1;
    });

    let dockHeight = $state(0);
    let touchStartX = $state(0);
    function handleTouchStart(e: TouchEvent) { touchStartX = e.touches[0].clientX; }
    function handleTouchEnd(e: TouchEvent) {
        const delta = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(delta) < 50 || data.queue.length === 0) return;
        const next = delta < 0 ? Math.min(data.currentItemIndex + 1, data.queue.length - 1) : Math.max(data.currentItemIndex - 1, 0);
        if (next !== data.currentItemIndex) goto(`?tx=${next}`, { replaceState: true });
    }

    const arrowBtn =
        'flex h-9 w-9 items-center justify-center rounded-full border-[3px] border-ink bg-white shadow-[3px_3px_0_var(--color-ink)] transition-[transform,box-shadow] duration-[180ms] ease-bounce hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[5px_5px_0_var(--color-ink)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none disabled:opacity-40 disabled:!translate-x-0 disabled:!translate-y-0';
</script>

<svelte:head>
    <title>{account.name ?? account.institution_name} — EARMARK</title>
</svelte:head>

<main class="page" style:padding-bottom={data.mode === 'allocate' ? dockHeight + 24 + 'px' : undefined}>
    <!-- Summary cells -->
    <div class="grid grid-cols-3 gap-2">
        {#snippet cell(labelText: string, valueText: string, warn = false)}
            <div class="relative rounded-chunk border-[3px] border-ink px-3 py-2.5 {warn ? 'bg-tomato text-white' : 'bg-paper-2 text-ink'}">
                <span class="pointer-events-none absolute inset-1 rounded-[10px] border-[1.5px] border-dashed {warn ? 'border-white/55' : 'border-ink/40'}"></span>
                <div class="text-[10px] font-extrabold uppercase tracking-wide opacity-70">{labelText}</div>
                <div class="num mt-0.5 text-[15px] leading-tight">{valueText}</div>
            </div>
        {/snippet}
        {@render cell('Balance', formatCurrency(account.balance, account.currency))}
        {@render cell('Earmarked', formatCurrency(earmarked.toFixed(2), account.currency))}
        {@render cell('To earmark', String(data.queue.length), data.queue.length > 0)}
    </div>

    <!-- Add envelope / group -->
    <div class="grid grid-cols-2 gap-3">
        <Button variant="secondary" onclick={() => addEnvelope(null)}>+ New envelope</Button>
        <Button variant="secondary" onclick={() => addGroup(null)}>+ New group</Button>
    </div>

    <EnvelopeTree
        nodes={data.tree}
        groups={data.groups}
        currency={account.currency}
        accountId={account.id}
        allocateMode={data.mode === 'allocate'}
        {allocAmount}
        {allocSign}
        {allocKind}
        allocSplitId={activeSplitId}
        {withdrawalId}
        currentItemIndex={data.currentItemIndex}
        onAddEnvelope={addEnvelope}
        onAddGroup={addGroup}
    />
</main>

<!-- Create-envelope modal -->
<Modal bind:open={envModalOpen} title="New envelope">
    <form method="POST" action="?/create_envelope" use:enhance={() => async ({ update }) => { await update(); envModalOpen = false; }} class="flex flex-col gap-4">
        <input type="hidden" name="group_id" value={envModalGroup ?? ''} />
        <!-- svelte-ignore a11y_autofocus -->
        <Field label="Envelope name" name="name" placeholder="e.g. Groceries" required autofocus />
        <div class="flex gap-3">
            <Button type="submit" variant="success" fullWidth>Create</Button>
            <Button type="button" variant="secondary" fullWidth onclick={() => (envModalOpen = false)}>Cancel</Button>
        </div>
    </form>
</Modal>

<!-- Create-group modal -->
<Modal bind:open={grpModalOpen} title="New group">
    <form method="POST" action="?/create_group" use:enhance={() => async ({ update }) => { await update(); grpModalOpen = false; }} class="flex flex-col gap-4">
        <input type="hidden" name="parent_id" value={grpModalParent ?? ''} />
        <!-- svelte-ignore a11y_autofocus -->
        <Field label="Group name" name="name" placeholder="e.g. Savings" required autofocus />
        <SelectField label="Colour" name="tint">
            <option value="budget">Budget (yellow)</option>
            <option value="monthly">Monthly (blue)</option>
            <option value="savings">Savings (green)</option>
            <option value="fun">Fun (pink)</option>
        </SelectField>
        <div class="flex gap-3">
            <Button type="submit" variant="success" fullWidth>Create</Button>
            <Button type="button" variant="secondary" fullWidth onclick={() => (grpModalOpen = false)}>Cancel</Button>
        </div>
    </form>
</Modal>

<!-- Allocation dock -->
{#if data.mode === 'allocate' && data.currentItem}
    {@const item = data.currentItem}
    <div
        role="region"
        aria-label="Allocation queue"
        data-testid="allocation-dock"
        bind:clientHeight={dockHeight}
        ontouchstart={handleTouchStart}
        ontouchend={handleTouchEnd}
        class="fixed inset-x-0 bottom-0 z-20 mx-auto max-w-[440px] border-t-[3px] border-ink bg-sun px-4 pb-[18px] pt-3.5 shadow-[0_-4px_0_var(--color-ink)]"
    >
        <div class="mb-2 flex items-center justify-between">
            <button class={arrowBtn} onclick={() => goto(`?tx=${Math.max(0, data.currentItemIndex - 1)}`, { replaceState: true })} disabled={data.currentItemIndex === 0} aria-label="Previous item">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m15 19-7-7 7-7" /></svg>
            </button>
            <span class="rounded-full border-[3px] border-ink bg-white px-3.5 py-1 font-mono text-[13px] font-bold text-ink">{data.currentItemIndex + 1} of {data.queue.length}</span>
            <button class={arrowBtn} onclick={() => goto(`?tx=${Math.min(data.queue.length - 1, data.currentItemIndex + 1)}`, { replaceState: true })} disabled={data.currentItemIndex === data.queue.length - 1} aria-label="Next item">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m9 5 7 7-7 7" /></svg>
            </button>
        </div>

        {#if item.kind === 'withdrawal'}
            <div class="flex items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                    <div class="truncate font-display text-lg font-extrabold text-ink">Withdrawal from {item.withdrawal.from_envelope_name}</div>
                    {#if item.withdrawal.note}<div class="truncate text-xs font-bold text-ink/65">{item.withdrawal.note}</div>{/if}
                    <div class="text-xs font-bold text-ink/65">{formatDate(item.withdrawal.created_at.slice(0, 10))}</div>
                </div>
                <div class="num text-xl">{formatCurrency(parseFloat(item.withdrawal.amount).toFixed(2), account.currency)}</div>
            </div>
            <p class="mt-2 text-xs font-bold text-ink/70">Tap an envelope to earmark this.</p>
        {:else}
            {@const tx = item.tx}
            {@const splits = currentSplits}
            {@const unallocatedSplits = splits.filter((s) => !s.is_allocated)}
            <div class="flex items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                    <div class="truncate font-display text-lg font-extrabold text-ink">{tx.merchant ?? 'Unknown merchant'}</div>
                    {#if tx.description}<div class="truncate text-xs font-bold text-ink/65">{tx.description}</div>{/if}
                    <div class="text-xs font-bold text-ink/65">{formatDate(tx.date)}</div>
                </div>
                <div class="num text-xl {tx.credit_debit_indicator === 'DBIT' ? 'text-tomato-ink' : 'text-ink'}">{formatSignedCurrency(tx.amount, tx.currency, tx.credit_debit_indicator)}</div>
            </div>

            {#if splits.length > 1}
                <p class="mt-2 text-xs font-bold text-ink/60">✂ Split ({unallocatedSplits.length} part{unallocatedSplits.length === 1 ? '' : 's'} left)</p>
            {/if}

            <div class="mt-2 flex flex-col gap-2">
                {#each splits as split (split.id)}
                    {@const isActive = !split.is_allocated && split.id === activeSplitId}
                    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
                    <div
                        class="flex items-center justify-between gap-2 rounded-chunk border-[2.5px] p-2 text-sm {isActive ? 'border-ink bg-white' : 'border-ink/25'} {split.is_allocated ? '' : 'cursor-pointer'}"
                        role={split.is_allocated ? undefined : 'button'}
                        tabindex={split.is_allocated ? undefined : 0}
                        onclick={() => { if (!split.is_allocated) selectedSplitId = split.id; }}
                        onkeydown={(e) => { if (!split.is_allocated && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); selectedSplitId = split.id; } }}
                    >
                        <div class="flex min-w-0 items-center gap-2">
                            {#if !split.is_allocated}
                                <span data-testid="split-radio" class="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full border-2 {isActive ? 'border-ink' : 'border-ink/35'}">
                                    {#if isActive}<span class="h-1.5 w-1.5 rounded-full bg-ink"></span>{/if}
                                </span>
                            {/if}
                            {#if split.is_round_up}<span class="shrink-0 text-xs font-extrabold text-grape-ink">Round Up</span>{/if}
                            <span class="num {tx.credit_debit_indicator === 'DBIT' ? 'text-tomato-ink' : 'text-ink'}">{formatSignedCurrency(split.amount, tx.currency, tx.credit_debit_indicator)}</span>
                            {#if split.note}<span class="truncate text-ink/50">— {split.note}</span>{/if}
                            {#if split.is_allocated && split.envelope_name}<span class="ml-1 shrink-0 truncate font-bold text-grass-ink">{split.envelope_name}</span>{/if}
                        </div>
                        <div class="flex shrink-0 items-center gap-1">
                            {#if split.is_default && !split.is_round_up}
                                <button type="button" data-testid="split-btn" class="rounded-full border-2 border-ink bg-white px-2 py-1 text-xs font-bold" onclick={(e) => { e.stopPropagation(); showAddSplitForm = !showAddSplitForm; }}>✂ Split</button>
                            {/if}
                            {#if !split.is_default && !split.is_round_up}
                                <form method="POST" action="?/delete_split" use:enhance>
                                    <input type="hidden" name="split_id" value={split.id} />
                                    <input type="hidden" name="current_index" value={data.currentItemIndex} />
                                    <button type="submit" data-testid="delete-split-btn" class="px-2 py-1 text-xs font-bold text-tomato-ink" onclick={(e) => { e.stopPropagation(); if (!confirm('Delete this split?')) e.preventDefault(); }}>Delete</button>
                                </form>
                            {/if}
                        </div>
                    </div>
                {/each}

                {#if showAddSplitForm}
                    <form method="POST" action="?/create_split" use:enhance={() => async ({ update }) => { await update(); showAddSplitForm = false; }} class="flex flex-col gap-2 rounded-chunk border-[2.5px] border-ink p-3">
                        <input type="hidden" name="tx_id" value={item.kind === 'transaction' ? item.tx.id : ''} />
                        <input type="hidden" name="current_index" value={data.currentItemIndex} />
                        <div class="flex gap-2">
                            <input name="amount" type="text" aria-label="Amount" placeholder="Amount" required class="block w-full rounded-chunk border-[3px] border-ink bg-white px-3 py-2 font-mono text-sm outline-none" />
                            <input name="note" type="text" aria-label="Note (optional)" placeholder="Note" class="block w-full rounded-chunk border-[3px] border-ink bg-white px-3 py-2 text-sm outline-none" />
                        </div>
                        <div class="flex gap-2">
                            <Button type="submit" variant="success" size="sm" fullWidth>Add split</Button>
                            <Button type="button" variant="secondary" size="sm" fullWidth onclick={() => (showAddSplitForm = false)}>Cancel</Button>
                        </div>
                    </form>
                {/if}
            </div>
        {/if}
    </div>
{/if}
