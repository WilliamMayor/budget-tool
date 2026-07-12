<script lang="ts">
    let {
        on = false,
        label = 'Toggle',
        ...rest
    }: {
        /** Current on/off state. */
        on?: boolean;
        label?: string;
        [key: string]: unknown;
    } = $props();
</script>

<button
    type="submit"
    role="switch"
    aria-checked={on}
    aria-label={label}
    class="relative h-8 w-[58px] shrink-0 rounded-pill border-[3px] border-ink shadow-[3px_3px_0_var(--color-ink)] transition-colors duration-200 {on
        ? 'bg-grass'
        : 'bg-paper-2'}"
    {...rest}
>
    <span
        class="absolute top-0.5 h-[22px] w-[22px] rounded-full bg-ink transition-[left] duration-[180ms] ease-bounce {on
            ? 'left-[28px]'
            : 'left-0.5'}"
    ></span>
</button>
