<script lang="ts">
	import { enhance } from '$app/forms';
	import { formatDate, formatSignedCurrency } from '$lib/format.js';
	import Button from '$lib/components/Button.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import Field from '$lib/components/Field.svelte';

	let { data } = $props();
	let addOpen = $state(false);
</script>

<svelte:head>
	<title>Transactions — {data.account.institution_name} — EARMARK</title>
</svelte:head>

<main class="page">
	<Button variant="secondary" onclick={() => (addOpen = true)}>+ Add transaction</Button>

	<Modal bind:open={addOpen} title="Add transaction">
		<form method="POST" action="?/add_transaction" use:enhance={() => async ({ update }) => { await update(); addOpen = false; }} class="flex flex-col gap-4">
			<!-- svelte-ignore a11y_autofocus -->
			<Field label="Description" name="description" placeholder="e.g. Weekly shop" required autofocus />
			<Field label="Amount (negative = expense)" name="amount" placeholder="e.g. -12.50 or 50.00" class="font-mono" required />
			<Field label="Merchant (optional)" name="merchant" placeholder="e.g. Tesco" />
			<Field label="Date (optional, defaults to today)" name="date" type="date" />
			<div class="flex gap-3">
				<Button type="submit" variant="success" fullWidth>Add</Button>
				<Button type="button" variant="secondary" fullWidth onclick={() => (addOpen = false)}>Cancel</Button>
			</div>
		</form>
	</Modal>

	{#if data.transactions.length === 0}
		<p class="py-8 text-center font-display text-xl font-bold text-fg-muted">No transactions yet.</p>
	{:else}
		<div class="overflow-hidden rounded-card border-[3px] border-ink bg-white shadow-rest">
			<table class="w-full table-fixed border-collapse text-sm">
				<tbody>
					{#each data.transactions as tx, i (tx.id)}
						{@const debit = tx.credit_debit_indicator === 'DBIT'}
						<tr class="{i > 0 ? 'border-t-2 border-ink/10' : ''}" data-testid="transaction-row">
							<td class="overflow-hidden px-3 py-2 align-middle">
								<div class="truncate font-body font-extrabold text-ink">{tx.merchant ?? tx.description}</div>
								{#if tx.merchant && tx.description}<div class="truncate text-[11px] font-bold text-ink/55">{tx.description}</div>{/if}
							</td>
							<td class="w-[92px] px-1 py-2 text-right align-middle text-[11px] font-bold text-ink/55">{formatDate(tx.date)}</td>
							<td class="w-[96px] whitespace-nowrap px-3 py-2 text-right align-middle">
								<span class="num {debit ? 'text-tomato-ink' : 'text-grass-ink'}" data-testid="transaction-amount">{formatSignedCurrency(tx.amount, tx.currency, tx.credit_debit_indicator)}</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</main>
