<script lang="ts">
    import type { Snippet } from 'svelte';

    let {
        interactive = false,
        stitched = false,
        href = undefined,
        bg = 'bg-white',
        radius = 'rounded-card',
        padding = 'p-4',
        class: klass = '',
        children,
        ...rest
    }: {
        /** Adds hover-lift + press-clunk (for clickable cards). */
        interactive?: boolean;
        /** Dashed inner "stitch" border for passive info cards. */
        stitched?: boolean;
        href?: string;
        /** Tailwind background utility, e.g. bg-white / bg-tomato. */
        bg?: string;
        radius?: string;
        padding?: string;
        class?: string;
        children: Snippet;
        [key: string]: unknown;
    } = $props();

    const base = 'relative block border-[3px] border-ink shadow-rest text-ink';
    const lift =
        'cursor-pointer transition-[transform,box-shadow] duration-[180ms] ease-bounce hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-hover active:translate-x-1 active:translate-y-1 active:shadow-press no-underline';

    const cls = $derived(
        [base, radius, bg, padding, interactive ? lift : '', klass].filter(Boolean).join(' ')
    );
</script>

{#snippet inner()}
    {#if stitched}
        <span
            class="pointer-events-none absolute inset-[5px] rounded-[calc(var(--radius-card)-6px)] border-[1.5px] border-dashed border-ink/40"
        ></span>
    {/if}
    {@render children()}
{/snippet}

{#if href}
    <a {href} class={cls} {...rest}>{@render inner()}</a>
{:else}
    <div class={cls} {...rest}>{@render inner()}</div>
{/if}
