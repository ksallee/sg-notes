<!--
	The top of the page: what site this is, who is reading it, and which project.

	One row. The project is the one pick that changes what the page reads, and a
	change reloads the page: the source and every cache under it were built for the
	old one (the docs site's Connect panel follows the same rule).
-->
<script lang="ts">
	import type { EntityRef, SgContext } from '@sg-widgets/core';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import ProjectPicker from '$lib/components/project-picker.svelte';
	import Wordmark from './wordmark.svelte';
	import { setProject, setSiteUrl, signIn, signOut, type LiveState } from '$lib/live';

	let { live, context }: { live: LiveState; context: SgContext } = $props();

	let editingSite = $state(false);
	let siteDraft = $state('');
	let approving = $state(false);
	let refusal = $state<string | null>(null);

	/** The site as the bar names it: the studio, without the suffix every Flow PT host carries. */
	function shortHost(siteUrl: string): string {
		try {
			return new URL(siteUrl).hostname.replace(/^www\./, '').replace(/\.(?:shotgrid\.autodesk\.com|shotgunstudio\.com)$/, '');
		} catch {
			return siteUrl;
		}
	}

	const editing = $derived(editingSite || live.siteUrl === '');
	const project = $derived<EntityRef | null>(live.project ? { type: 'Project', id: live.project.id, name: live.project.name } : null);

	function useSite(): void {
		const value = siteDraft.trim();
		if (!value) return;
		setSiteUrl(value);
		location.reload();
	}

	async function onSignIn(): Promise<void> {
		refusal = null;
		approving = true;
		try {
			// The launcher hands the token out once, so one poll runs and it runs here.
			await signIn(live.siteUrl, (url) => window.open(url, '_blank', 'noopener'));
			location.reload();
		} catch (error) {
			refusal = error instanceof Error ? error.message : String(error);
		} finally {
			approving = false;
		}
	}

	function onSignOut(): void {
		signOut();
		location.reload();
	}

	function pickProject(value: EntityRef | null): void {
		// The picker resolves a bare `{type, id}` on mount and reports it: the same project, now
		// with its name, is not a change, and reloading on it would reload forever.
		if (value?.id === live.project?.id) {
			if (value && value.name !== live.project?.name) setProject({ id: value.id, name: value.name });
			return;
		}
		setProject(value ? { id: value.id, name: value.name } : null);
		location.reload();
	}
</script>

<header class="border-border bg-background flex h-12 shrink-0 items-center gap-5 border-b px-4" data-slot="site-bar">
	<a href="/" class="focus-visible:ring-ring rounded-md text-sm outline-none focus-visible:ring-2" aria-label="SG Notes, home">
		<Wordmark />
	</a>

	<div class="flex min-w-0 flex-1 items-center gap-2">
		{#if editing}
			<Input
				class="h-8 max-w-sm"
				type="url"
				placeholder="https://studio.shotgrid.autodesk.com"
				bind:value={siteDraft}
				onkeydown={(event) => event.key === 'Enter' && useSite()}
			/>
			<Button size="sm" variant="outline" onclick={useSite}>Use site</Button>
			{#if live.siteUrl}
				<Button size="sm" variant="ghost" onclick={() => (editingSite = false)}>Cancel</Button>
			{/if}
		{:else}
			<span class="text-muted-foreground truncate text-sm" title={live.siteUrl}><span class="text-xs">Site</span> {shortHost(live.siteUrl)}</span>
			<Button size="sm" variant="ghost" onclick={() => ((siteDraft = live.siteUrl), (editingSite = true))}>Change</Button>
			{#if live.problem === null}
				<div class="w-64">
					<ProjectPicker {context} value={project} onValueChange={pickProject} size="sm" placeholder="Pick a project" />
				</div>
			{/if}
		{/if}
	</div>

	<div class="flex shrink-0 items-center gap-2 text-sm">
		{#if live.session}
			<span class="text-muted-foreground truncate" title={live.session.login}>{live.session.login}</span>
			<Button size="sm" variant="ghost" onclick={onSignOut}>Sign out</Button>
		{:else if live.siteUrl}
			{#if refusal}
				<span class="text-destructive truncate" title={refusal}>{refusal}</span>
			{:else if approving}
				<span class="text-muted-foreground">Approve the request in the tab that opened.</span>
			{:else if live.devToken}
				<span class="text-muted-foreground text-xs">Dev key</span>
			{/if}
			<Button size="sm" variant={live.devToken ? 'outline' : 'default'} onclick={onSignIn} disabled={approving}>{live.devToken ? 'Sign in as yourself' : 'Sign in'}</Button>
		{/if}
	</div>
</header>
