<script lang="ts">
    import { page } from "$app/state";
    import type { Snippet } from "svelte";
    import type { AccountWithStats } from "$lib/types.js";
    import { formatCurrency } from "$lib/format.js";
    import Button from "$lib/components/Button.svelte";
    import Card from "$lib/components/Card.svelte";

    let {
        data,
        children,
    }: { data: { account: AccountWithStats }; children: Snippet } = $props();

    const accountBase = $derived(`/accounts/${data.account.id}`);

    const path = $derived(page.url.pathname);
    const onTransactions = $derived(path.startsWith(accountBase + "/transactions"));
    const onSettings = $derived(path.startsWith(accountBase + "/settings"));
    const onEnvelopes = $derived(!onTransactions && !onSettings);
</script>

<div class="flex flex-col gap-3 px-4 pt-4" data-testid="account-tab-bar">
    <Card stitched padding="px-[18px] py-3.5">
        <div class="font-display text-3xl font-black leading-[0.95] text-ink">{data.account.institution_name}</div>
        <div class="mt-0.5 text-sm font-bold text-fg-muted">
            {#if data.account.name}{data.account.name} · {/if}{formatCurrency(
                data.account.balance,
                data.account.currency,
            )}
        </div>
    </Card>

    <nav class="flex gap-2" aria-label="Account">
        <Button
            href={accountBase}
            variant={onEnvelopes ? "primary" : "secondary"}
            size="sm"
            class="flex-1"
            aria-current={onEnvelopes ? "page" : undefined}
            data-testid="tab-envelopes"
        >
            Envelopes
        </Button>
        <Button
            href={accountBase + "/transactions"}
            variant={onTransactions ? "primary" : "secondary"}
            size="sm"
            class="flex-1"
            aria-current={onTransactions ? "page" : undefined}
            data-testid="tab-transactions"
        >
            Transactions
        </Button>
        <Button
            href={accountBase + "/settings"}
            variant={onSettings ? "primary" : "secondary"}
            size="sm"
            class="flex-1"
            aria-current={onSettings ? "page" : undefined}
        >
            Settings
        </Button>
    </nav>
</div>

{@render children()}
