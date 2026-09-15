<!--
	Several ticked notes in the one pane: each a line, the last ticked open. A press
	on a line opens that one and folds the rest, so the pane is an accordion of
	threads rather than a wall of them.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { EntityRow, StatusRecord } from '@sg-widgets/core';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import StatusBadge from '$lib/components/status-badge.svelte';
	import { cn } from '$lib/utils.js';
	import { refOf, text } from '$lib/notes';
	import { ago } from './time';

	type Props = {
		notes: EntityRow[];
		statuses: Record<string, StatusRecord>;
		/** The note shown in full. */
		expanded: number | null;
		onExpand: (id: number | null) => void;
		/** Draws one note's thread. */
		pane: Snippet<[EntityRow]>;
	};

	let { notes, statuses, expanded, onExpand, pane }: Props = $props();
</script>

<div class="flex flex-col" data-slot="thread-stack">
	{#each notes as note (note.id)}
		{@const open = expanded === note.id}
		{@const code = text(note, 'sg_status_list')}
		<section class="border-border border-b" data-slot="thread-stack-item" data-state={open ? 'open' : 'closed'}>
			<button
				type="button"
				aria-expanded={open}
				onclick={() => onExpand(open ? null : note.id)}
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
				<span class="text-muted-foreground shrink-0 text-xs tabular-nums">{ago(text(note, 'created_at'))}</span>
			</button>
			{#if open}
				{@render pane(note)}
			{/if}
		</section>
	{/each}
</div>
