<script lang="ts">
    import type { Snippet } from 'svelte';

    let {
        label,
        name,
        value = $bindable(''),
        id = name,
        class: klass = '',
        children,
        ...rest
    }: {
        label?: string;
        name?: string;
        value?: string;
        id?: string;
        class?: string;
        children: Snippet;
        [key: string]: unknown;
    } = $props();

    const selectCls =
        'block w-full font-body text-base text-ink bg-white pl-4 pr-11 py-3 border-[3px] border-ink rounded-chunk shadow-rest outline-none appearance-none focus:-translate-x-0.5 focus:-translate-y-0.5 focus:shadow-hover transition-[transform,box-shadow] duration-[180ms] ease-bounce';
</script>

<div class="flex flex-col gap-1">
    {#if label}
        <label for={id} class="font-body font-extrabold text-xs tracking-wide uppercase text-fg-muted">{label}</label>
    {/if}
    <div class="relative">
        <select {id} {name} bind:value class="{selectCls} {klass}" {...rest}>
            {@render children()}
        </select>
        <svg
            class="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
        >
            <path d="m6 9 6 6 6-6" />
        </svg>
    </div>
</div>
