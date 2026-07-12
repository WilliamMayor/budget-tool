<script lang="ts">
    let {
        label,
        name,
        type = 'text',
        value = $bindable(''),
        placeholder = '',
        required = false,
        id = name,
        class: klass = '',
        ...rest
    }: {
        label?: string;
        name?: string;
        type?: string;
        value?: string;
        placeholder?: string;
        required?: boolean;
        id?: string;
        class?: string;
        [key: string]: unknown;
    } = $props();

    const inputCls =
        'block w-full font-body text-base text-ink bg-white px-4 py-3 border-[3px] border-ink rounded-chunk shadow-rest outline-none transition-[transform,box-shadow] duration-[180ms] ease-bounce focus:-translate-x-0.5 focus:-translate-y-0.5 focus:shadow-hover placeholder:text-fg-subtle';
</script>

<div class="flex flex-col gap-1">
    {#if label}
        <label for={id} class="font-body font-extrabold text-xs tracking-wide uppercase text-fg-muted">{label}</label>
    {/if}
    <input {id} {name} {type} {placeholder} {required} bind:value class="{inputCls} {klass}" {...rest} />
</div>
