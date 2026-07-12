<script lang="ts">
    // Cartoon ink-stroke icon set. Paths lifted from the Earmark design system.
    let {
        name,
        size = 18,
        stroke = 2.5
    }: { name: string; size?: number; stroke?: number } = $props();

    const paths: Record<string, string> = {
        chevR: 'm9 5 7 7-7 7',
        chevD: 'm6 9 6 6 6-6',
        chevU: 'm18 15-6-6-6 6',
        plus: 'M12 5v14M5 12h14',
        arrowUp: 'M12 19V5 M5 12l7-7 7 7',
        edit: 'M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z M15 5l4 4',
        sticker: 'M15.5 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V8.5L15.5 3Z M15 3v6h6',
        folder: 'M4 4h5l2 3h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z',
        flag: 'M4 22V4 M4 4h13l-2.5 4 2.5 4H4',
        refresh: 'M21 12a9 9 0 1 1-2.64-6.36 M21 3v6h-6',
        move: 'M5 9l-3 3 3 3 M9 5l3-3 3 3 M15 19l-3 3-3-3 M19 9l3 3-3 3 M2 12h20 M12 2v20',
        trash: 'M4 7h16 M10 11v6 M14 11v6 M6 7l1 13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-13 M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3'
    };
</script>

<svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    stroke-width={stroke}
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
>
    {#each (paths[name] ?? '').split(' M') as seg, i}
        <path d={i === 0 ? seg : 'M' + seg} />
    {/each}
</svg>
