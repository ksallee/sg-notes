<!--
	Several ticked notes in the one pane: each a line, the last ticked open. A press
	on a line opens or folds that one; expand all and collapse all do the lot, so the
	pane can be a wall of threads when a lead wants to read them all, and a list of
	lines when they want to scan.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { EntityRow, StatusRecord } from 'sg-widgets-core';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ChevronsDownUp from '@lucide/svelte/icons/chevrons-down-up';
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	import { Button } from '$lib/components/ui/button/index.js';
	import StatusBadge from '$lib/components/status-badge.svelte';
	import { cn } from '$lib/utils.js';
	import { formatDateTime, preferencesOf } from 'sg-widgets-core';
	import type { SgContext } from 'sg-widgets-core';
	import { refOf, text } from '$lib/notes';

	type Props = {
		context: SgContext;
		notes: EntityRow[];
		statuses: Record<string, StatusRecord>;
		/** The notes shown in full. */
		expanded: ReadonlySet<number>;
		onExpand: (ids: number[]) => void;
		/** Draws one note's thread. */
		pane: Snippet<[EntityRow]>;
	};

	let { context, notes, statuses, expanded, onExpand, pane }: Props = $props();
	const prefs = $derived(preferencesOf(context));
</script>

<div class="flex flex-col" data-slot="thread-stack">
	<div class="border-border flex items-center gap-2 border-b px-4 py-1.5">
		<span class="text-muted-foreground font-mono text-xs tabular-nums">{notes.length} selected</span>
		<Button size="icon-xs" variant="ghost" class="ml-auto" aria-label="Collapse all" title="Collapse all" onclick={() => onExpand([])}>
			<ChevronsDownUp aria-hidden="true" />
		</Button>
		<Button size="icon-xs" variant="ghost" aria-label="Expand all" title="Expand all" onclick={() => onExpand(notes.map((note) => note.id))}>
			<ChevronsUpDown aria-hidden="true" />
		</Button>
	</div>
	{#each notes as note (note.id)}
		{@const open = expanded.has(note.id)}
		{@const code = text(note, 'sg_status_list')}
		<section class="border-border border-b" data-slot="thread-stack-item" data-state={open ? 'open' : 'closed'}>
			<button
				type="button"
				aria-expanded={open}
				onclick={() => onExpand(open ? [...expanded].filter((id) => id !== note.id) : [...expanded, note.id])}
				class={cn(
					'focus-visible:ring-ring flex w-full items-center gap-2 px-4 py-2 text-left text-sm outline-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-inset',
					open ? 'bg-muted/50' : 'hover:bg-muted/50'
				)}
			>
				<ChevronRight aria-hidden="true" class={cn('text-muted-foreground size-4 shrink-0 transition-transform duration-150 ease-out motion-reduce:transition-none', open && 'rotate-90')} />
				<span class="min-w-0 flex-1 truncate font-medium" title={text(note, 'subject')}>{text(note, 'subject') || 'No subject'}</span>
				{#if code}
					<StatusBadge {code} status={statuses[code] ?? null} variant="icon" size="xs" />
				{/if}
				<span class="text-muted-foreground max-w-32 truncate text-xs">{refOf(note, 'created_by')?.name ?? ''}</span>
				<span class="text-muted-foreground shrink-0 font-mono text-xs tabular-nums">{formatDateTime(text(note, 'created_at'), prefs)}</span>
			</button>
			{#if open}
				{@render pane(note)}
			{/if}
		</section>
	{/each}
</div>
