<script lang="ts">
    import type { Snippet } from 'svelte';

    let {
        open = $bindable(false),
        title = '',
        children
    }: {
        open?: boolean;
        title?: string;
        children: Snippet;
    } = $props();

    let dialog = $state<HTMLDialogElement>();

    // Native <dialog>: drive showModal/close from the bound `open` flag.
    $effect(() => {
        if (!dialog) return;
        if (open && !dialog.open) dialog.showModal();
        else if (!open && dialog.open) dialog.close();
    });

    function onClose() {
        open = false;
    }

    // Close when the backdrop (the dialog element itself) is clicked.
    function onClick(e: MouseEvent) {
        if (e.target === dialog) open = false;
    }
</script>

<dialog
    bind:this={dialog}
    onclose={onClose}
    onclick={onClick}
    class="m-auto w-[min(92vw,26rem)] rounded-card border-[3px] border-ink bg-white p-0 text-ink shadow-lg backdrop:bg-ink/40 backdrop:backdrop-blur-[1px]"
>
    <div class="flex flex-col gap-4 p-5">
        {#if title}
            <div class="flex items-center justify-between gap-3">
                <h2 class="font-display text-2xl">{title}</h2>
                <button
                    type="button"
                    onclick={onClose}
                    aria-label="Close"
                    class="flex h-8 w-8 items-center justify-center rounded-full border-[3px] border-ink bg-white shadow-[2px_2px_0_var(--color-ink)]"
                >
                    <svg class="ink-icon h-4 w-4" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                </button>
            </div>
        {/if}
        {@render children()}
    </div>
</dialog>
