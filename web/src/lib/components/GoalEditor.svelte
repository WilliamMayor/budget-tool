<script lang="ts">
    import { enhance } from '$app/forms';
    import { buildRrule, inferGoalType } from '$lib/goal-utils.js';
    import type { EnvelopeWithStats } from '$lib/types.js';
    import Button from './Button.svelte';
    import SelectField from './SelectField.svelte';

    let {
        envelope,
        currency,
        action = '?/set_goal',
        onDone = () => {}
    }: {
        envelope: EnvelopeWithStats;
        currency: string;
        /** Form action to POST to (defaults to the local set_goal action). */
        action?: string;
        onDone?: () => void;
    } = $props();

    const existing = inferGoalType(envelope);

    let type = $state<'recurring' | 'one_off' | 'open_ended' | 'none'>(existing ?? 'open_ended');
    let amount = $state(envelope.goal_amount ?? '');
    let freq = $state<'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY'>('MONTHLY');
    let byDay = $state('MO');
    let byMonthDay = $state(1);
    let byMonth = $state(1);
    let dueDate = $state(existing === 'one_off' ? (envelope.goal_due_date ?? '') : '');

    const built = $derived.by(() => {
        if (type !== 'recurring') return { rrule: '', dtstart: '' };
        try {
            return buildRrule(freq, {
                byDay: freq === 'WEEKLY' ? byDay : undefined,
                byMonthDay: freq === 'MONTHLY' || freq === 'YEARLY' ? byMonthDay : undefined,
                byMonth: freq === 'YEARLY' ? byMonth : undefined,
                dtstart: new Date()
            });
        } catch {
            return { rrule: '', dtstart: '' };
        }
    });

    const sym = $derived(currency === 'GBP' ? '£' : currency);
    const DAYS = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];
    const DAY_LABELS: Record<string, string> = {
        SU: 'Sunday', MO: 'Monday', TU: 'Tuesday', WE: 'Wednesday', TH: 'Thursday', FR: 'Friday', SA: 'Saturday'
    };
    const inputCls =
        'block w-full font-body text-base text-ink bg-white px-4 py-3 border-[3px] border-ink rounded-chunk shadow-rest outline-none focus:-translate-x-0.5 focus:-translate-y-0.5 focus:shadow-hover transition-[transform,box-shadow] duration-[180ms] ease-bounce';
</script>

<form method="POST" {action} use:enhance={() => async ({ update }) => { await update(); onDone(); }} class="flex flex-col gap-3">
    <input type="hidden" name="envelope_id" value={envelope.id} />
    <SelectField label="Goal type" id="goal-type-{envelope.id}" value={type}
        onchange={(e: Event) => (type = (e.target as HTMLSelectElement).value as typeof type)}>
        <option value="recurring">Recurring</option>
        <option value="one_off">One-off</option>
        <option value="open_ended">Open-ended</option>
        <option value="none">No goal</option>
    </SelectField>

    <input type="hidden" name="goal_type" value={type} />

    {#if type === 'none'}
        <p class="text-[13px] font-semibold text-fg-muted">Saving will remove this envelope’s goal.</p>
    {:else}
    <!-- Amount -->
    <div class="flex flex-col gap-1">
        <label class="font-body text-xs font-extrabold uppercase tracking-wide text-fg-muted" for="goal-amount">Target amount</label>
        <div class="relative">
            <span class="pointer-events-none absolute left-4 top-1/2 z-10 -translate-y-1/2 font-mono font-bold text-fg-muted">{sym}</span>
            <input id="goal-amount" name="amount" type="number" min="0.01" step="0.01" bind:value={amount} placeholder="0.00" required class="{inputCls} pl-8 font-mono" />
        </div>
    </div>

    {#if type === 'recurring'}
        <SelectField label="Repeats" bind:value={freq}>
            <option value="DAILY">Daily</option>
            <option value="WEEKLY">Weekly</option>
            <option value="MONTHLY">Monthly</option>
            <option value="YEARLY">Yearly</option>
        </SelectField>

        {#if freq === 'WEEKLY'}
            <SelectField label="On" bind:value={byDay}>
                {#each DAYS as day}<option value={day}>{DAY_LABELS[day]}</option>{/each}
            </SelectField>
        {/if}
        {#if freq === 'MONTHLY'}
            <SelectField label="On the" value={String(byMonthDay)} onchange={(e: Event) => (byMonthDay = +(e.target as HTMLSelectElement).value)}>
                {#each Array.from({ length: 28 }, (_, i) => i + 1) as day}
                    <option value={day}>{day}{day === 1 ? 'st' : day === 2 ? 'nd' : day === 3 ? 'rd' : 'th'}</option>
                {/each}
            </SelectField>
        {/if}
        {#if freq === 'YEARLY'}
            <div class="grid grid-cols-2 gap-2">
                <SelectField label="Month" value={String(byMonth)} onchange={(e: Event) => (byMonth = +(e.target as HTMLSelectElement).value)}>
                    {#each ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] as m, i}<option value={i + 1}>{m}</option>{/each}
                </SelectField>
                <SelectField label="Day" value={String(byMonthDay)} onchange={(e: Event) => (byMonthDay = +(e.target as HTMLSelectElement).value)}>
                    {#each Array.from({ length: 28 }, (_, i) => i + 1) as day}<option value={day}>{day}</option>{/each}
                </SelectField>
            </div>
        {/if}

        <input type="hidden" name="rrule" value={built.rrule} />
        <input type="hidden" name="dtstart" value={built.dtstart} />
        <p class="rounded-chunk border-2 border-ink bg-sky px-2 py-1 font-mono text-xs">{built.rrule}</p>
    {/if}

    {#if type === 'one_off'}
        <div class="flex flex-col gap-1">
            <label class="font-body text-xs font-extrabold uppercase tracking-wide text-fg-muted" for="goal-due">Save by</label>
            <input id="goal-due" name="due_date" type="date" bind:value={dueDate} required class={inputCls} />
        </div>
    {/if}
    {/if}

    <div class="mt-1 flex gap-2">
        <Button type="submit" variant={type === 'none' ? 'danger' : 'success'} size="xs" class="flex-1">{type === 'none' ? 'Remove goal' : 'Save goal'}</Button>
        <Button type="button" variant="secondary" size="xs" class="flex-1" onclick={onDone}>Cancel</Button>
    </div>
</form>
