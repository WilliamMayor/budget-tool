<script lang="ts">
	import { enhance } from '$app/forms';
	import { formatDate, formatCurrency } from '$lib/format.js';
	import Card from '$lib/components/Card.svelte';
	import Button from '$lib/components/Button.svelte';
	import Modal from '$lib/components/Modal.svelte';
	import Field from '$lib/components/Field.svelte';
	import Badge from '$lib/components/Badge.svelte';
	import Icon from '$lib/components/Icon.svelte';

	let { data, form } = $props();
	let syncing = $state(false);
	let newAccountOpen = $state(false);
</script>

<svelte:head>
	<title>Accounts — EARMARK</title>
</svelte:head>

<main class="page">
	<Button variant="secondary" onclick={() => (newAccountOpen = true)}>+ New account</Button>

	<Modal bind:open={newAccountOpen} title="New account">
		<form method="POST" action="?/create_account" use:enhance={() => async ({ update }) => { await update(); newAccountOpen = false; }} class="flex flex-col gap-4">
			<!-- svelte-ignore a11y_autofocus -->
			<Field label="Institution name" name="institution_name" placeholder="e.g. Cash" required autofocus />
			<Field label="Account name (optional)" name="name" placeholder="e.g. Wallet" />
			<Field label="Currency" name="currency" value="GBP" required />
			<div class="flex gap-3">
				<Button type="submit" variant="success" fullWidth>Create</Button>
				<Button type="button" variant="secondary" fullWidth onclick={() => (newAccountOpen = false)}>Cancel</Button>
			</div>
		</form>
	</Modal>

	<form method="POST" action="?/sync" use:enhance={() => { syncing = true; return async ({ update }) => { syncing = false; await update(); }; }}>
		<Button type="submit" variant="info" fullWidth disabled={syncing}>
			<Icon name="refresh" size={18} />
			{syncing ? 'Syncing…' : 'Sync Now'}
		</Button>
	</form>

	{#if form?.synced === true}
		<div class="rounded-chunk border-[3px] border-ink bg-grass px-3.5 py-2.5 text-sm font-bold text-ink shadow-rest">
			{form.total} transaction(s) synced across {form.accounts} account(s).{#if form.errors.length > 0}
				{' '}{form.errors.length} account(s) failed.{/if}
		</div>
	{:else if form?.synced === false}
		<div class="rounded-chunk border-[3px] border-ink bg-tomato px-3.5 py-2.5 text-sm font-bold text-white shadow-rest">{form.error}</div>
	{/if}

	{#if data.accounts.length === 0}
		<p class="py-12 text-center font-display text-xl font-bold text-fg-muted">No accounts synced yet.</p>
	{:else}
		{#each data.accounts as account (account.id)}
			{@const bal = parseFloat(account.balance)}
			<Card interactive href="/accounts/{account.id}" padding="px-[18px] py-4" data-testid="account-card">
				<div class="flex items-start justify-between gap-3">
					<div class="min-w-0">
						<div class="font-display text-lg font-extrabold leading-tight text-ink">{account.institution_name}</div>
						{#if account.name}<div class="mt-0.5 text-xs font-bold text-ink/65">{account.name}</div>{/if}
						<div class="mt-0.5 text-xs font-bold text-ink/65">
							{account.currency}{#if account.last_synced_at} · Synced {formatDate(account.last_synced_at.slice(0, 10))}{/if}
						</div>
					</div>
					<div class="flex shrink-0 flex-col items-end gap-1">
						<span class="num text-xl {bal < 0 ? 'text-tomato-ink' : 'text-ink'}" data-testid="account-balance">{formatCurrency(account.balance, account.currency)}</span>
						{#if account.unallocated_count > 0}
							<Badge variant="danger" data-testid="unallocated-badge">{account.unallocated_count} to allocate</Badge>
						{/if}
					</div>
				</div>
			</Card>
		{/each}
	{/if}
</main>
