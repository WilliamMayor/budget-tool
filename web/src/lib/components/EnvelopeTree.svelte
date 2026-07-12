<script lang="ts">
    import { enhance } from '$app/forms';
    import { formatCurrency, formatDate } from '$lib/format.js';
    import {
        inferGoalType,
        getDaysRemaining,
        getRates,
        getMilestones,
        formatGoalDescription
    } from '$lib/goal-utils.js';
    import type { EnvelopeTreeNode, EnvelopeGroup, EnvelopeWithStats } from '$lib/types.js';
    import Icon from './Icon.svelte';
    import Button from './Button.svelte';
    import GoalEditor from './GoalEditor.svelte';
    import SelectField from './SelectField.svelte';

    let {
        nodes,
        groups,
        currency,
        accountId,
        allocateMode = false,
        allocAmount = 0,
        allocSign = 1,
        allocKind = null,
        allocSplitId = null,
        withdrawalId = null,
        currentItemIndex = 0,
        onAddEnvelope = () => {},
        onAddGroup = () => {}
    }: {
        nodes: EnvelopeTreeNode[];
        groups: EnvelopeGroup[];
        currency: string;
        accountId: number;
        allocateMode?: boolean;
        allocAmount?: number;
        allocSign?: 1 | -1;
        allocKind?: 'split' | 'withdrawal' | null;
        allocSplitId?: number | null;
        withdrawalId?: number | null;
        currentItemIndex?: number;
        onAddEnvelope?: (groupId: number | null) => void;
        onAddGroup?: (parentId: number | null) => void;
    } = $props();

    // Expansion + per-row drawer form state
    let open = $state<Record<string, boolean>>({});
    let drawerForm = $state<Record<number, 'withdraw' | 'goal' | 'move' | 'edit' | 'delete' | null>>({});
    // Per-row goal-progress summary drawer (toggled from the "To go" stat tile)
    let goalOpen = $state<Record<number, boolean>>({});

    const keyFor = (n: EnvelopeTreeNode) => (n.kind === 'group' ? 'g' + n.group.id : 'e' + n.envelope.id);
    const isOpen = (n: EnvelopeTreeNode) => open[keyFor(n)] ?? n.kind === 'group';
    const toggle = (n: EnvelopeTreeNode) => (open[keyFor(n)] = !isOpen(n));

    const PALETTE = ['grass', 'sun', 'bubble', 'sky', 'grape', 'tomato'];
    const colorFor = (e: EnvelopeWithStats) => PALETTE[e.id % PALETTE.length];
    const swatch: Record<string, string> = {
        grass: 'bg-grass', sun: 'bg-sun', bubble: 'bg-bubble', sky: 'bg-sky', grape: 'bg-grape', tomato: 'bg-tomato'
    };
    const tint: Record<string, string> = {
        budget: 'bg-[#fff4d9]', monthly: 'bg-[#e3f3ff]', savings: 'bg-[#e2f5e0]', fun: 'bg-[#fde6f1]'
    };

    const money = (n: number) => formatCurrency(n.toFixed(2), currency);
    const sym = $derived(currency === 'GBP' ? '£' : currency + ' ');
    function moneyShort(n: number): string {
        if (Math.abs(n) >= 1_000_000) return sym + (n / 1_000_000).toFixed(2) + 'M';
        return money(n);
    }
    const signedAlloc = $derived((allocSign > 0 ? '+ ' : '− ') + money(Math.abs(allocAmount)));

    const goalOf = (e: EnvelopeWithStats) => (e.goal_amount ? parseFloat(e.goal_amount) : 0);
    const pctOf = (e: EnvelopeWithStats) => (goalOf(e) > 0 ? Math.round((e.goal_balance / goalOf(e)) * 100) : 0);

    type Totals = { balance: number; goal: number; count: number };
    function totalsOf(node: EnvelopeTreeNode): Totals {
        if (node.kind === 'envelope') return { balance: node.envelope.goal_balance, goal: goalOf(node.envelope), count: 1 };
        return node.children.reduce<Totals>(
            (a, c) => { const t = totalsOf(c); return { balance: a.balance + t.balance, goal: a.goal + t.goal, count: a.count + t.count }; },
            { balance: 0, goal: 0, count: 0 }
        );
    }

    const actionBtn =
        'flex flex-col items-center gap-1.5 rounded-chunk border-[2.5px] border-ink bg-white px-1.5 pb-2 pt-2.5 text-[11px] font-extrabold leading-tight text-ink text-center no-underline shadow-[2px_2px_0_var(--color-ink)] transition-[transform,box-shadow] duration-[180ms] ease-bounce hover:-translate-x-px hover:-translate-y-px hover:shadow-[3px_3px_0_var(--color-ink)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none cursor-pointer';
    // Highlight for the action whose form is currently open.
    const actionActive = '!bg-sun !translate-x-0.5 !translate-y-0.5 !shadow-none';
</script>

{#snippet stat(labelText: string, valueText: string, danger = false, expandable = false, expanded = false)}
    <div class="relative h-full rounded-chunk border-[2.5px] border-ink bg-paper-2 px-2.5 py-2 {expandable ? 'transition-colors hover:bg-white' : ''}">
        <span class="pointer-events-none absolute inset-1 rounded-[10px] border-[1.25px] border-dashed border-ink/40"></span>
        <div class="flex items-center gap-1">
            <div class="text-[10px] font-bold uppercase tracking-wide text-ink/60">{labelText}</div>
            {#if expandable}
                <svg class="h-3 w-3 shrink-0 text-ink/45 transition-transform duration-[180ms] ease-bounce {expanded ? 'rotate-180' : ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
            {/if}
        </div>
        <div class="num mt-0.5 text-[13.5px] {danger ? 'text-tomato-ink' : 'text-ink'}">{valueText}</div>
    </div>
{/snippet}

{#snippet envelopeNode(node: Extract<EnvelopeTreeNode, { kind: 'envelope' }>)}
    {@const env = node.envelope}
    {@const color = colorFor(env)}
    {@const goal = goalOf(env)}
    {@const pct = pctOf(env)}
    {@const remaining = Math.max(0, goal - env.goal_balance)}
    {@const expanded = isOpen(node)}
    {@const showPill = allocateMode && !expanded}
    {@const dform = drawerForm[env.id] ?? null}
    <div
        data-testid="envelope-card"
        class="overflow-hidden rounded-chunk border-[3px] border-ink bg-white shadow-[3px_3px_0_var(--color-ink)] transition-[transform,box-shadow] duration-[180ms] ease-bounce {expanded ? '' : 'hover:-translate-x-px hover:-translate-y-px hover:shadow-[4px_4px_0_var(--color-ink)]'}"
    >
        <div class="relative flex min-h-[40px] items-center gap-3 px-2.5 pb-2.5 pt-1.5">
            <button class="flex min-w-0 flex-1 items-center gap-3 bg-transparent text-left" onclick={() => toggle(node)} aria-expanded={expanded}>
                <span class="h-[26px] w-2.5 shrink-0 rounded-md border-[2.5px] border-ink {swatch[color]}"></span>
                <span class="flex min-w-0 flex-1 flex-col">
                    <span class="truncate font-body text-[13.5px] font-extrabold leading-tight text-ink {expanded ? 'whitespace-normal' : ''}">{env.name}</span>
                </span>
                <span class="flex shrink-0 flex-col items-end whitespace-nowrap text-right">
                    <span class="num text-[13.5px]">{moneyShort(env.goal_balance)}</span>
                    {#if goal > 0}<span class="num text-[10.5px] font-medium text-ink/55">of {moneyShort(goal)}</span>{/if}
                    {#if allocateMode}<span class="num text-[10.5px] font-medium text-ink/55">→ {moneyShort(env.goal_balance + allocSign * allocAmount)}</span>{/if}
                </span>
                {#if !showPill}<span class="flex h-[22px] w-[22px] shrink-0 items-center justify-center opacity-50 transition-transform duration-[180ms] ease-bounce {expanded ? 'rotate-180 opacity-100' : ''}"><Icon name="chevD" size={16} /></span>{/if}
            </button>

            {#if showPill}
                <form method="POST" action={allocKind === 'withdrawal' ? '?/allocate_withdrawal' : '?/allocate'} use:enhance>
                    {#if allocKind === 'withdrawal'}
                        <input type="hidden" name="withdrawal_id" value={withdrawalId} />
                        <input type="hidden" name="envelope_id" value={env.id} />
                    {:else}
                        <input type="hidden" name="envelope_id" value={env.id} />
                        <input type="hidden" name="split_id" value={allocSplitId} />
                    {/if}
                    <input type="hidden" name="current_index" value={currentItemIndex} />
                    <button
                        type="submit"
                        data-testid={allocKind === 'withdrawal' ? 'allocate-withdrawal-btn' : 'allocate-btn'}
                        class="inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-full border-[2.5px] border-ink bg-grass px-2.5 py-1 font-mono text-xs font-bold text-ink shadow-[2px_2px_0_var(--color-ink)] transition-[transform,box-shadow] duration-[180ms] ease-bounce hover:-translate-x-px hover:-translate-y-px hover:shadow-[3px_3px_0_var(--color-ink)] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
                    >{signedAlloc}</button>
                </form>
            {/if}

            {#if goal > 0}
                <span class="absolute inset-x-0 bottom-0 h-[5px] overflow-hidden border-t-2 border-ink bg-ink/[0.08]">
                    <i class="block h-full {pct >= 100 ? 'bg-grass' : swatch[color]}" style="width: {Math.min(100, Math.max(0, pct))}%"></i>
                </span>
            {/if}
        </div>

        {#if expanded}
            <div class="flex flex-col gap-3 border-t-[2.5px] border-dashed border-ink/25 bg-ink/[0.03] p-3.5">
                {#if goal > 0}
                    {@const gtype = inferGoalType(env)}
                    {@const summaryOpen = goalOpen[env.id] ?? false}
                    <div class="text-[11px] font-bold uppercase tracking-wider text-ink/50">{Math.min(100, Math.max(0, pct))}% saved</div>
                    <div class="grid grid-cols-3 gap-2">
                        {@render stat('Saved', money(env.goal_balance))}
                        {@render stat('Goal', money(goal))}
                        <button type="button" class="block h-full text-left" aria-expanded={summaryOpen}
                            onclick={() => (goalOpen[env.id] = !summaryOpen)}>
                            {@render stat(pct >= 100 ? 'Reached' : 'To go', money(remaining), pct < 100, true, summaryOpen)}
                        </button>
                    </div>

                    {#if summaryOpen}
                        {@const days = getDaysRemaining(env)}
                        {@const rates = getRates(env)}
                        {@const miles = getMilestones(env)}
                        <div class="flex flex-col gap-2.5 rounded-chunk border-[2.5px] border-ink bg-paper-2 p-3" data-testid="goal-summary">
                            <p class="text-[13px] font-semibold text-ink">{formatGoalDescription(env)}</p>
                            {#if gtype !== 'open_ended' && days !== null}
                                <p class="text-[11px] font-bold text-fg-muted">
                                    {#if days > 0}{days} day{days === 1 ? '' : 's'} remaining
                                    {:else if days === 0}Due today
                                    {:else}Overdue by {Math.abs(days)} day{Math.abs(days) === 1 ? '' : 's'}{/if}
                                </p>
                            {/if}
                            {#if rates}
                                <div>
                                    <p class="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-ink/50">To reach goal on time</p>
                                    <div class="grid grid-cols-3 gap-2 text-center">
                                        <div><p class="num text-sm">{money(rates.perDay)}</p><p class="mt-0.5 text-[10px] font-bold text-fg-muted">per day</p></div>
                                        <div><p class="num text-sm">{money(rates.perWeek)}</p><p class="mt-0.5 text-[10px] font-bold text-fg-muted">per week</p></div>
                                        <div><p class="num text-sm">{money(rates.perMonth)}</p><p class="mt-0.5 text-[10px] font-bold text-fg-muted">per month</p></div>
                                    </div>
                                </div>
                            {/if}
                            {#if miles}
                                <div>
                                    <p class="mb-1.5 text-[10px] font-bold uppercase tracking-wide text-ink/50">Reach your goal in…</p>
                                    <div class="flex flex-col gap-1.5">
                                        {#each miles as m, i}
                                            {#if i > 0}<div class="border-t-2 border-ink/10"></div>{/if}
                                            <div class="flex items-center justify-between">
                                                <div><span class="num text-[13px]">{money(m.monthlyAmount)}</span><span class="text-[11px] font-bold text-fg-muted"> / month</span></div>
                                                <div class="text-right text-[11px] font-bold"><span class="text-ink">{m.months} months</span><span class="text-fg-muted"> · {new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric' }).format(m.targetDate)}</span></div>
                                            </div>
                                        {/each}
                                    </div>
                                </div>
                            {/if}
                        </div>
                    {/if}
                {:else}
                    <div class="grid grid-cols-1 gap-2">{@render stat('Balance', money(env.goal_balance))}</div>
                {/if}

                {#if allocateMode}
                    <form method="POST" action={allocKind === 'withdrawal' ? '?/allocate_withdrawal' : '?/allocate'} use:enhance>
                        {#if allocKind === 'withdrawal'}
                            <input type="hidden" name="withdrawal_id" value={withdrawalId} />
                            <input type="hidden" name="envelope_id" value={env.id} />
                        {:else}
                            <input type="hidden" name="envelope_id" value={env.id} />
                            <input type="hidden" name="split_id" value={allocSplitId} />
                        {/if}
                        <input type="hidden" name="current_index" value={currentItemIndex} />
                        <Button type="submit" variant="success" fullWidth>Allocate {signedAlloc}</Button>
                    </form>
                {/if}

                <div class="grid gap-2 [grid-template-columns:repeat(auto-fill,minmax(66px,1fr))]">
                    <button type="button" class="{actionBtn} {dform === 'withdraw' ? actionActive : ''}" onclick={() => (drawerForm[env.id] = dform === 'withdraw' ? null : 'withdraw')}>
                        <Icon name="arrowUp" size={20} />Withdraw
                    </button>
                    <button type="button" class="{actionBtn} {dform === 'goal' ? actionActive : ''}" onclick={() => (drawerForm[env.id] = dform === 'goal' ? null : 'goal')}>
                        <Icon name="flag" size={20} />Goal
                    </button>
                    <button type="button" class="{actionBtn} {dform === 'move' ? actionActive : ''}" onclick={() => (drawerForm[env.id] = dform === 'move' ? null : 'move')}>
                        <Icon name="move" size={20} />Move
                    </button>
                    <button type="button" class="{actionBtn} {dform === 'edit' ? actionActive : ''}" onclick={() => (drawerForm[env.id] = dform === 'edit' ? null : 'edit')}>
                        <Icon name="edit" size={20} />Edit
                    </button>
                    <button type="button" class="{actionBtn} {dform === 'delete' ? actionActive : ''}" onclick={() => (drawerForm[env.id] = dform === 'delete' ? null : 'delete')}>
                        <Icon name="trash" size={20} />Delete
                    </button>
                </div>

                {#if dform === 'withdraw'}
                    <form method="POST" action="?/withdraw" use:enhance={() => async ({ update }) => { await update(); drawerForm[env.id] = null; }} class="flex flex-col gap-2">
                        <input type="hidden" name="envelope_id" value={env.id} />
                        <input name="amount" type="text" aria-label="Amount" placeholder="Amount e.g. 50.00" required
                            class="block w-full rounded-chunk border-[2.5px] border-ink bg-white px-3 py-2 font-mono text-sm outline-none" />
                        <input name="note" type="text" aria-label="Note (optional)" placeholder="Note (optional)"
                            class="block w-full rounded-chunk border-[2.5px] border-ink bg-white px-3 py-2 text-sm outline-none" />
                        <div class="flex gap-2">
                            <Button type="submit" variant="danger" size="xs" class="flex-1">Withdraw</Button>
                            <Button type="button" variant="secondary" size="xs" class="flex-1" onclick={() => (drawerForm[env.id] = null)}>Cancel</Button>
                        </div>
                    </form>
                {:else if dform === 'goal'}
                    <GoalEditor envelope={env} {currency}
                        onDone={() => (drawerForm[env.id] = null)} />
                {:else if dform === 'move' && groups.length > 0}
                    <form method="POST" action="?/move_envelope" use:enhance>
                        <input type="hidden" name="envelope_id" value={env.id} />
                        <SelectField label="Move to group" name="group_id" value={env.group_id == null ? '' : String(env.group_id)}
                            onchange={(e: Event) => (e.target as HTMLSelectElement).form?.requestSubmit()}>
                            <option value="">— Top level —</option>
                            {#each groups as g (g.id)}<option value={g.id}>{g.name}</option>{/each}
                        </SelectField>
                    </form>
                {:else if dform === 'edit'}
                    <form method="POST" action="?/rename_envelope" use:enhance={() => async ({ update }) => { await update(); drawerForm[env.id] = null; }} class="flex flex-col gap-2">
                        <input type="hidden" name="envelope_id" value={env.id} />
                        <!-- svelte-ignore a11y_autofocus -->
                        <input name="name" type="text" aria-label="Envelope name" value={env.name} required autofocus
                            class="block w-full rounded-chunk border-[2.5px] border-ink bg-white px-3 py-2 font-body text-sm font-extrabold outline-none" />
                        <div class="flex gap-2">
                            <Button type="submit" variant="success" size="xs" class="flex-1">Save</Button>
                            <Button type="button" variant="secondary" size="xs" class="flex-1" onclick={() => (drawerForm[env.id] = null)}>Cancel</Button>
                        </div>
                    </form>
                {:else if dform === 'delete'}
                    <form method="POST" action="?/delete_envelope" use:enhance={() => async ({ update }) => { await update(); drawerForm[env.id] = null; }} class="flex flex-col gap-2 rounded-chunk border-[2.5px] border-ink bg-tomato/15 p-3">
                        <input type="hidden" name="envelope_id" value={env.id} />
                        <p class="text-[13px] font-bold text-ink">Delete “{env.name}”? This can’t be undone.</p>
                        <div class="flex gap-2">
                            <Button type="submit" variant="danger" size="xs" class="flex-1">Confirm delete</Button>
                            <Button type="button" variant="secondary" size="xs" class="flex-1" onclick={() => (drawerForm[env.id] = null)}>Cancel</Button>
                        </div>
                    </form>
                {/if}
            </div>
        {/if}
    </div>
{/snippet}

{#snippet groupNode(node: Extract<EnvelopeTreeNode, { kind: 'group' }>)}
    {@const t = totalsOf(node)}
    {@const expanded = isOpen(node)}
    <div class="overflow-hidden rounded-card border-[3px] border-ink shadow-rest {tint[node.group.tint] ?? 'bg-white'}">
        <button class="flex w-full items-center gap-3 px-3.5 py-2.5 text-left" aria-expanded={expanded} onclick={() => toggle(node)}>
            <span class="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border-[2.5px] border-ink bg-white transition-transform duration-[180ms] ease-bounce {expanded ? 'rotate-90' : ''}"><Icon name="chevR" size={12} /></span>
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
                <span class="font-display text-base font-extrabold leading-tight text-ink">{node.group.name}</span>
                <span class="font-body text-[11px] font-bold text-ink/55">{t.count} {t.count === 1 ? 'envelope' : 'envelopes'}</span>
            </span>
            <span class="shrink-0 text-right">
                <div class="num text-sm">{moneyShort(t.balance)}</div>
                {#if t.goal > 0}<div class="num text-[10.5px] font-medium text-ink/55">of {moneyShort(t.goal)}</div>{/if}
            </span>
        </button>
        {#if expanded}
            <div class="flex flex-col gap-2 px-2.5 pb-2.5 pt-1">
                {#each node.children as child (keyFor(child))}
                    {#if child.kind === 'group'}{@render groupNode(child)}{:else}{@render envelopeNode(child)}{/if}
                {/each}
                <div class="flex gap-2">
                    <button type="button" onclick={() => onAddEnvelope(node.group.id)} class="flex-1 rounded-chunk border-[2.5px] border-dashed border-ink/70 py-2 text-center text-[13px] font-extrabold text-ink/75 hover:bg-white/60 hover:text-ink">+ Envelope</button>
                    <button type="button" onclick={() => onAddGroup(node.group.id)} class="flex-1 rounded-chunk border-[2.5px] border-dashed border-ink/70 py-2 text-center text-[13px] font-extrabold text-ink/75 hover:bg-white/60 hover:text-ink">+ Group</button>
                </div>
            </div>
        {/if}
    </div>
{/snippet}

<div class="flex flex-col gap-2.5">
    {#each nodes as node (keyFor(node))}
        {#if node.kind === 'group'}{@render groupNode(node)}{:else}{@render envelopeNode(node)}{/if}
    {/each}
    {#if nodes.length === 0}
        <p class="py-12 text-center font-display text-xl font-bold text-fg-muted">No envelopes yet.</p>
    {/if}
</div>
