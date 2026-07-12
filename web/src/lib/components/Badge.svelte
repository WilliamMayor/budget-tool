<script lang="ts">
    import type { Snippet } from 'svelte';

    let {
        variant = 'danger',
        class: klass = '',
        children,
        ...rest
    }: {
        variant?: 'sun' | 'danger' | 'success' | 'info';
        class?: string;
        children: Snippet;
        [key: string]: unknown;
    } = $props();

    const variants = {
        sun: 'bg-sun text-ink',
        danger: 'bg-tomato text-white',
        success: 'bg-grass text-ink',
        info: 'bg-sky text-ink'
    };
</script>

<span
    class="inline-flex items-center gap-1.5 rounded-pill border-[3px] border-ink px-2.5 py-0.5 text-xs font-extrabold {variants[
        variant
    ]} {klass}"
    {...rest}
>
    {@render children()}
</span>
