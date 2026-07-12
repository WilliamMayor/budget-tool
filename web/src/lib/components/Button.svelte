<script lang="ts">
    import type { Snippet } from 'svelte';

    let {
        variant = 'primary',
        size = 'md',
        href = undefined,
        type = 'button',
        fullWidth = false,
        disabled = false,
        class: klass = '',
        children,
        ...rest
    }: {
        variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'info' | 'ink';
        size?: 'md' | 'sm' | 'xs';
        href?: string;
        type?: 'button' | 'submit' | 'reset';
        fullWidth?: boolean;
        disabled?: boolean;
        class?: string;
        children: Snippet;
        [key: string]: unknown;
    } = $props();

    const base =
        'inline-flex items-center justify-center gap-2 font-body font-extrabold border-[3px] border-ink rounded-pill cursor-pointer shadow-rest transition-[transform,box-shadow] duration-[180ms] ease-bounce hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-hover active:translate-x-1 active:translate-y-1 active:shadow-press disabled:opacity-50 disabled:cursor-not-allowed disabled:!translate-x-0 disabled:!translate-y-0 disabled:!shadow-rest no-underline';
    const sizes = { md: 'px-5 py-3 text-base', sm: 'px-3.5 py-2 text-sm', xs: 'px-3 py-1.5 text-[11px]' };
    const variants = {
        primary: 'bg-sun text-ink',
        secondary: 'bg-white text-ink',
        success: 'bg-grass text-ink',
        danger: 'bg-tomato text-white',
        info: 'bg-sky text-ink',
        ink: 'bg-ink text-paper'
    };

    const cls = $derived(
        [base, sizes[size], variants[variant], fullWidth ? 'w-full' : '', klass].filter(Boolean).join(' ')
    );
</script>

{#if href}
    <a {href} class={cls} {...rest}>{@render children()}</a>
{:else}
    <button {type} {disabled} class={cls} {...rest}>{@render children()}</button>
{/if}
