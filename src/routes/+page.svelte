<script lang="ts">
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import SiteBar from '$lib/app/site-bar.svelte';
	import Workbench from '$lib/app/workbench.svelte';
	import { liveContext, liveWriter, prepareLive } from '$lib/live';
</script>

<svelte:head><title>sg-notes</title></svelte:head>

<div class="bg-background text-foreground flex h-dvh flex-col">
	{#await prepareLive()}
		<div class="border-border flex h-12 shrink-0 items-center gap-4 border-b px-3" aria-busy="true" aria-label="Reaching the site">
			<span class="flex items-center gap-1.5 text-sm"><span class="font-medium">sg</span><span class="text-muted-foreground">notes</span></span>
			<Skeleton class="h-4 w-24" />
			<Skeleton class="h-8 w-64" />
		</div>
	{:then state}
		{@const context = liveContext()}
		<SiteBar live={state} {context} />
		{#if state.problem}
			<p class="text-muted-foreground flex flex-1 items-center justify-center text-sm">{state.problem}</p>
		{:else if !state.project}
			<p class="text-muted-foreground flex flex-1 items-center justify-center text-sm">Pick a project to read its notes.</p>
		{:else}
			<Workbench {context} writer={liveWriter()} projectId={state.project.id} />
		{/if}
	{:catch error}
		<p class="text-destructive p-4 text-sm">{error.message}</p>
	{/await}
</div>
