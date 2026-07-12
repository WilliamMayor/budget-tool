<script lang="ts">
    import { enhance } from '$app/forms';
    import Card from '$lib/components/Card.svelte';
    import Toggle from '$lib/components/Toggle.svelte';

    let { data } = $props();
    const account = $derived(data.account);
</script>

<svelte:head>
    <title>Settings — {account.institution_name} — EARMARK</title>
</svelte:head>

<main class="page">
    <Card padding="p-4">
        <form method="POST" action="?/toggle_round_up" use:enhance class="flex items-center justify-between gap-3">
            <div class="min-w-0">
                <div class="font-display text-base font-extrabold text-ink">Round Up</div>
                <div class="mt-0.5 text-xs font-bold text-ink/65">
                    Save the spare change from every transaction
                </div>
            </div>
            <input type="hidden" name="enabled" value={account.round_up_since !== null ? '0' : '1'} />
            <Toggle on={account.round_up_since !== null} label="Toggle round up" />
        </form>
    </Card>
</main>
