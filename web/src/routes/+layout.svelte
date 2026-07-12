<script lang="ts">
    import "../app.css";
    import { page } from "$app/state";
    import type { Snippet } from "svelte";

    let { children }: { children: Snippet } = $props();

    const accountsActive = $derived(page.url.pathname.startsWith("/accounts"));
    const settingsActive = $derived(page.url.pathname.startsWith("/settings"));

    const navLink =
        "font-body text-[13px] font-extrabold uppercase tracking-[0.06em] no-underline pb-1 border-b-2 transition-colors";
</script>

<div class="relative mx-auto min-h-screen max-w-[440px]">
    <header class="sticky top-0 z-30 flex items-center justify-between border-b-[3px] border-ink bg-ink px-5 py-3.5">
        <a href="/accounts" class="flex items-center gap-2.5 font-display text-[22px] font-black uppercase leading-none tracking-[0.08em] text-paper no-underline">
            <img src="/logo-mark.svg" alt="" class="h-[30px] w-[30px]" />
            Earmark
        </a>

        <nav class="flex gap-[18px]" aria-label="Global">
            <a href="/accounts" aria-current={accountsActive ? "page" : undefined}
                class="{navLink} {accountsActive ? 'text-paper border-sun' : 'text-paper/55 border-transparent hover:text-paper'}">Accounts</a>
            <a href="/settings" aria-current={settingsActive ? "page" : undefined}
                class="{navLink} {settingsActive ? 'text-paper border-sun' : 'text-paper/55 border-transparent hover:text-paper'}">Settings</a>
        </nav>
    </header>

    {@render children()}
</div>
