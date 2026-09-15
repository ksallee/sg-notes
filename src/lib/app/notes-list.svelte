<!--
	Every note in the project, under the record it is about.

	A group is one Shot, Asset or Version: its thumbnail, its name and its status,
	then the notes on it newest first. A row is who wrote it, what it says, who it
	is waiting on and when. The source behind it is the page's; this draws rows.

	Grouping is the app's own (`$lib/notes`), not the grouped-list widget's: that
	widget groups on a sorted path, and `note_links` is a multi-entity field the
	site will not sort on. The row and header anatomy follow it all the same.

	States. A first read stands behind skeletons shaped like rows; a re-read after
	a filter change keeps the rows on screen, dimmed, so the list does not flash;
	an error is a line with a retry; empty says whether the filter or the project
	is the reason. A row's "waiting on" is not claimed until its replies are known.

	Selection is one thing, the way Mail, Finder and Linear treat it: a press selects
	that row alone and the pane shows it; ⌘ toggles a row in or out; shift extends the
	run from the anchor; arrows move it, shift-arrows extend it, ⌘A takes every loaded
	row. The checkboxes are the same selection for a mouse with no modifier: they show
	on hover and stay while anything is selected.
-->
<script lang="ts">
	import type { EntityRef, EntityRow, SgContext, StatusRecord } from '@sg-widgets/core';
	import { cellValue, formatDateTime, preferencesOf } from '@sg-widgets/core';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ChevronsDownUp from '@lucide/svelte/icons/chevrons-down-up';
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	import SearchIcon from '@lucide/svelte/icons/search';
	import X from '@lucide/svelte/icons/x';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import Inbox from '@lucide/svelte/icons/inbox';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Paperclip from '@lucide/svelte/icons/paperclip';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Kbd } from '$lib/components/ui/kbd/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import EntityChip from '$lib/components/entity-chip.svelte';
	import StateLine from '$lib/components/state-line.svelte';
	import StatusBadge from '$lib/components/status-badge.svelte';
	import Thumbnail from '$lib/components/thumbnail.svelte';
	import UserAvatar from '$lib/components/user-avatar.svelte';
	import { cn } from '$lib/utils.js';
	import { GROUP_OPTIONS, groupNotes, isClientFacing, lastActivity, refKey, refOf, refsOf, runsOf, SORT_OPTIONS, text, WAITING_OPTIONS, waitingOn, type GroupBy, type SortBy, type Waiting, type WaitingKind } from '$lib/notes';
	import { ago } from './time';

	type Props = {
		context: SgContext;
		rows: EntityRow[];
		status: 'idle' | 'loading' | 'loadingMore' | 'ready' | 'error';
		error: Error | null;
		hasMore: boolean;
		/** True when a filter narrows the set, so an empty list can say so. */
		filtered: boolean;
		onLoadMore: () => void;
		onRetry: () => void;
		/** Replies by note id, oldest first. A note absent from the map has not been read yet. */
		replies: Map<number, EntityRow[]>;
		/** The linked records, keyed `Type:id`, for thumbnails and statuses. */
		records: Map<string, EntityRow>;
		/** People by id, for avatars. */
		people: Map<number, EntityRow>;
		statuses: Record<string, StatusRecord>;
		/** Ids of the selected notes. */
		selected: ReadonlySet<number>;
		/** The whole next selection, and the row the press or key landed on. */
		onSelectionChange: (ids: number[], last: number | null) => void;
		/** What the rows are grouped on, two-way. */
		groupBy?: GroupBy;
		/** How the rows are ordered, two-way. The site orders the first two; the rest order what is loaded. */
		sortBy?: SortBy;
		/** The search the page applies, two-way. The list draws the box; the page reads. */
		query?: string;
		onClearFilters: () => void;
		onActions: () => void;
	};

	let {
		context,
		rows,
		status,
		error,
		hasMore,
		filtered,
		onLoadMore,
		onRetry,
		replies,
		records,
		people,
		statuses,
		selected,
		onSelectionChange,
		groupBy = $bindable('record'),
		sortBy = $bindable('newest'),
		query = $bindable(''),
		onClearFilters,
		onActions
	}: Props = $props();

	/** Who a note has to be waiting on to be shown. Decided on the loaded rows. */
	let waitingFilter = $state<WaitingKind | 'any'>('any');

	/** Reads the next page whenever the foot of the list scrolls into view. */
	function sentinel(node: HTMLElement): () => void {
		const root = node.closest('[data-slot="notes-scroll"]');
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting)) onLoadMore();
			},
			{ root, rootMargin: '0px 0px 240px 0px' }
		);
		observer.observe(node);
		return () => observer.disconnect();
	}

	/** The `x` key: the row the selection last landed on, in or out. */
	export function toggleAnchor(): void {
		const id = anchor ?? order[0];
		if (id !== undefined) toggle(id);
	}

	export function collapseAll(): void {
		setShut({ all: true, except: [] });
	}

	export function expandAll(): void {
		setShut({ all: false, except: [] });
	}

	const shown = $derived.by(() => {
		const kept = waitingFilter === 'any' ? rows : rows.filter((note) => waitingOn(note, replies.get(note.id) ?? null)?.kind === waitingFilter);
		if (sortBy === 'replies') return [...kept].sort((a, b) => (replies.get(b.id)?.length ?? 0) - (replies.get(a.id)?.length ?? 0));
		if (sortBy === 'waiting') {
			// The notes still owed a word, the one quiet longest first; closed and unaddressed after.
			const owed = (note: EntityRow): number => (['author', 'addressees'].includes(waitingOn(note, replies.get(note.id) ?? null)?.kind ?? '') ? 0 : 1);
			return [...kept].sort((a, b) => owed(a) - owed(b) || lastActivity(a, replies.get(a.id) ?? null).localeCompare(lastActivity(b, replies.get(b.id) ?? null)));
		}
		return kept;
	});
	const groups = $derived(groupNotes(shown, records, groupBy));
	const groupLabel = $derived(GROUP_OPTIONS.find((option) => option.value === groupBy)?.label ?? '');
	const grouped = $derived(groupBy !== 'none');
	const anySelected = $derived(selected.size > 0);
	const prefs = $derived(preferencesOf(context));
	/** The first read, with nothing to show yet. A later read keeps the rows and dims them. */
	const firstRead = $derived((status === 'loading' || status === 'idle') && rows.length === 0);
	const rereading = $derived(status === 'loading' && rows.length > 0);

	/** Where a run starts: the last row selected on its own. */
	let anchor = $state<number | null>(null);
	let shiftHeld = false;

	/** Every note id in the order the list shows them, across groups, shut ones included. */
	const order = $derived(groups.flatMap((group) => group.notes.map((note) => note.id)));

	function run(from: number | null, to: number): number[] {
		const a = from === null ? -1 : order.indexOf(from);
		const b = order.indexOf(to);
		if (a === -1 || b === -1) return [to];
		return order.slice(Math.min(a, b), Math.max(a, b) + 1);
	}

	/** This row alone. */
	function selectOne(id: number): void {
		anchor = id;
		onSelectionChange([id], id);
	}

	/** This row in or out of what is selected. */
	function toggle(id: number): void {
		anchor = id;
		const next = selected.has(id) ? [...selected].filter((other) => other !== id) : [...selected, id];
		onSelectionChange(next, selected.has(id) ? null : id);
	}

	/** The run from the anchor to this row, replacing the selection, as Mail does. */
	function extend(id: number): void {
		onSelectionChange(run(anchor, id), id);
	}

	function setMany(ids: number[], on: boolean, last: number): void {
		const next = on ? [...new Set([...selected, ...ids])] : [...selected].filter((id) => !ids.includes(id));
		onSelectionChange(next, on ? last : null);
	}

	/** A plain press selects the row alone; shift extends the run; ⌘, ctrl or option toggles it. */
	function rowClick(note: EntityRow, event: MouseEvent): void {
		if (event.shiftKey) extend(note.id);
		else if (event.metaKey || event.ctrlKey || event.altKey) toggle(note.id);
		else selectOne(note.id);
	}

	/** The checkbox is the toggle for a mouse with no modifier; shift still makes a run. */
	function boxChange(note: EntityRow, on: boolean): void {
		if (shiftHeld && on) extend(note.id);
		else if (on !== selected.has(note.id)) toggle(note.id);
	}

	function groupState(group: { notes: EntityRow[] }): 'all' | 'some' | 'none' {
		const on = group.notes.filter((note) => selected.has(note.id)).length;
		return on === 0 ? 'none' : on === group.notes.length ? 'all' : 'some';
	}

	let list = $state<HTMLElement | null>(null);

	/**
	 * Arrows move the selection and the focus with it; shift-arrows extend the run; Home
	 * and End jump; ⌘A takes every loaded row. A row shut in its group is skipped.
	 */
	function onKeydown(event: KeyboardEvent): void {
		if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'a') {
			event.preventDefault();
			onSelectionChange(order, anchor);
			return;
		}
		if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key) || !list) return;
		const buttons = [...list.querySelectorAll<HTMLButtonElement>('[data-slot="notes-row"] button[aria-pressed]')];
		if (buttons.length === 0) return;
		const ids = buttons.map((button) => Number(button.closest<HTMLElement>('[data-slot="notes-row"]')?.dataset.noteId));
		const current = anchor !== null ? ids.indexOf(anchor) : -1;
		let next = current;
		if (event.key === 'ArrowDown') next = Math.min(buttons.length - 1, current + 1);
		else if (event.key === 'ArrowUp') next = Math.max(0, current - 1);
		else if (event.key === 'Home') next = 0;
		else next = buttons.length - 1;
		event.preventDefault();
		const id = ids[next]!;
		buttons[next]?.focus({ preventScroll: false });
		if (event.shiftKey) {
			// The run grows from the anchor's far end: shift-down from a lone row selects two.
			const from = anchor ?? id;
			onSelectionChange(run(from, id), id);
		} else {
			selectOne(id);
		}
	}

	/** Reads the next page whenever the foot of the list scrolls into view. */
	interface Shut {
		all: boolean;
		except: string[];
	}
	let shutBy = $state<Partial<Record<GroupBy, Shut>>>({});
	const shut = $derived(shutBy[groupBy] ?? { all: false, except: [] });
	const isShut = (key: string): boolean => shut.all !== shut.except.includes(key);

	function setShut(next: Shut): void {
		shutBy = { ...shutBy, [groupBy]: next };
	}

	function toggleGroup(key: string): void {
		setShut({ ...shut, except: shut.except.includes(key) ? shut.except.filter((k) => k !== key) : [...shut.except, key] });
	}

	/** Arrow keys walk the rows, Home and End jump, so a lead reads the list without a mouse. */
	function rowOf(ref: EntityRef | null | undefined): EntityRow | undefined {
		return ref ? records.get(refKey(ref)) : undefined;
	}

	function statusOf(ref: EntityRef | null | undefined): string {
		const row = rowOf(ref);
		return row ? String(cellValue(row, 'sg_status_list') ?? '') : '';
	}

	/** What a linked row belongs to: a Task's or a Version's entity, a Shot's sequence, whatever the row carries as `entity`. */
	function parentOf(ref: EntityRef | null | undefined): EntityRef | null {
		const row = rowOf(ref);
		return row ? refOf(row, 'entity') : null;
	}

	/** The note's links beyond what the group already names, so a row says where else it sits. */
	function otherLinks(note: EntityRow, shown: Array<EntityRef | null>): EntityRef[] {
		const hide = new Set(shown.filter((ref): ref is EntityRef => ref !== null).map(refKey));
		return [...refsOf(note, 'note_links'), ...refsOf(note, 'tasks')].filter((ref) => !hide.has(refKey(ref)));
	}

	function imageOf(row: EntityRow | undefined): string | null {
		const value = row ? cellValue(row, 'image') : null;
		return typeof value === 'string' ? value : null;
	}

	function personImage(ref: EntityRef | null): string | null {
		return ref ? imageOf(people.get(ref.id)) : null;
	}

	/** The people a note waits on, for the column's avatars. */
	function waitingWho(waiting: Waiting): EntityRef[] {
		return waiting.kind === 'author' ? [waiting.who] : waiting.kind === 'addressees' ? waiting.who : [];
	}

	function waitingLabel(waiting: Waiting): string {
		switch (waiting.kind) {
			case 'closed':
				return 'Closed';
			case 'nobody':
				return 'Addressed to nobody';
			case 'author':
				return `Waiting on ${waiting.who.name ?? 'the author'}`;
			default:
				return `Waiting on ${waiting.who.map((ref) => ref.name ?? '').filter(Boolean).join(', ')}`;
		}
	}

	function firstLine(note: EntityRow): string {
		const subject = text(note, 'subject').trim();
		if (subject) return subject;
		return text(note, 'content').trim().split('\n')[0] ?? '';
	}
</script>

{#snippet runs(value: string)}
	{#each runsOf(value, query) as run, index (index)}
		{#if run.hit}<span class="text-foreground font-semibold">{run.text}</span>{:else}{run.text}{/if}
	{/each}
{/snippet}

{#snippet glyph(ref: EntityRef | null)}
	{@const code = statusOf(ref)}
	{#if code}
		<StatusBadge {code} status={statuses[code] ?? null} variant="icon" size="xs" />
	{/if}
{/snippet}

{#snippet link(ref: EntityRef, muted: boolean)}
	<span class="flex min-w-0 items-center gap-1">
		<EntityChip entity={ref} variant="text" {context} size="xs" class={cn('min-w-0 truncate', muted && 'text-muted-foreground')} />
		{@render glyph(ref)}
	</span>
{/snippet}

<div class="flex min-h-0 flex-1 flex-col" data-slot="notes-list" data-state={status} data-group-by={groupBy}>
	<div class="border-border flex shrink-0 items-center gap-2 border-b px-2 py-1.5" data-slot="notes-tools">
		<div class="relative min-w-0 flex-1 max-w-xs">
			<SearchIcon aria-hidden="true" class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
			<Input type="text" bind:value={query} placeholder="Search" aria-label="Search notes" class="h-8 pr-8 pl-8 text-sm" data-slot="search" />
			{#if query}
				<Button size="icon-xs" variant="ghost" aria-label="Clear the search" class="absolute top-1/2 right-1 -translate-y-1/2" onclick={() => (query = '')}>
					<X aria-hidden="true" />
				</Button>
			{/if}
		</div>
		<Select.Root type="single" value={waitingFilter} onValueChange={(value) => (waitingFilter = value as WaitingKind | 'any')}>
			<Select.Trigger aria-label="Waiting on" class="ml-auto" data-slot="waiting-filter">
				<span data-slot="select-value"><span class="text-muted-foreground">Waiting on</span> {WAITING_OPTIONS.find((option) => option.value === waitingFilter)?.label ?? ''}</span>
			</Select.Trigger>
			<Select.Content>
				{#each WAITING_OPTIONS as option (option.value)}
					<Select.Item value={option.value} label={option.label} />
				{/each}
			</Select.Content>
		</Select.Root>
		<Select.Root type="single" value={sortBy} onValueChange={(value) => (sortBy = value as SortBy)}>
			<Select.Trigger aria-label="Sort by" data-slot="sort-by">
				<span data-slot="select-value"><span class="text-muted-foreground">Sort</span> {SORT_OPTIONS.find((option) => option.value === sortBy)?.label ?? ''}</span>
			</Select.Trigger>
			<Select.Content>
				{#each SORT_OPTIONS as option (option.value)}
					<Select.Item value={option.value} label={option.label} />
				{/each}
			</Select.Content>
		</Select.Root>
		<Select.Root type="single" value={groupBy} onValueChange={(value) => (groupBy = value as GroupBy)}>
			<Select.Trigger aria-label="Group by">
				<span data-slot="select-value"><span class="text-muted-foreground">Group by</span> {groupLabel}</span>
			</Select.Trigger>
			<Select.Content>
				{#each GROUP_OPTIONS as option (option.value)}
					<Select.Item value={option.value} label={option.label} />
				{/each}
			</Select.Content>
		</Select.Root>
		<Button size="icon" variant="ghost" aria-label="Collapse all" title={grouped ? 'Collapse all' : 'Nothing to collapse without a grouping'} disabled={!grouped} onclick={collapseAll}>
			<ChevronsDownUp aria-hidden="true" />
		</Button>
		<Button size="icon" variant="ghost" aria-label="Expand all" title={grouped ? 'Expand all' : 'Nothing to expand without a grouping'} disabled={!grouped} onclick={expandAll}>
			<ChevronsUpDown aria-hidden="true" />
		</Button>
		<Button variant={selected.size > 1 ? 'default' : 'outline'} onclick={onActions} data-slot="actions-button">
			{selected.size > 1 ? `${selected.size} selected` : 'Actions'}
			<Kbd>⌘K</Kbd>
		</Button>
	</div>
	{#if status === 'error'}
		<StateLine state="error" pad="table" icon={CircleAlert} label={error?.message ?? 'The read failed.'}>
			<Button size="sm" variant="outline" onclick={onRetry}>Try again</Button>
		</StateLine>
	{:else if firstRead}
		<div class="flex flex-col" aria-busy="true" aria-label="Reading the notes">
			<div class="border-border bg-muted/50 flex items-center gap-2 border-b px-2 py-1.5"><Skeleton class="h-6 w-9" /><Skeleton class="h-4 w-40" /></div>
			{#each { length: 3 } as _, index (index)}
				<div class="border-border/50 flex items-start gap-2 border-b px-2 py-1.5">
					<Skeleton class="size-6 shrink-0 rounded-full" />
					<div class="flex flex-1 flex-col gap-1"><Skeleton class="h-4 w-2/3" /><Skeleton class="h-3 w-1/2" /></div>
					<Skeleton class="h-3 w-8" />
				</div>
			{/each}
			<div class="border-border bg-muted/50 flex items-center gap-2 border-b px-2 py-1.5"><Skeleton class="h-6 w-9" /><Skeleton class="h-4 w-32" /></div>
			{#each { length: 4 } as _, index (index)}
				<div class="border-border/50 flex items-start gap-2 border-b px-2 py-1.5">
					<Skeleton class="size-6 shrink-0 rounded-full" />
					<div class="flex flex-1 flex-col gap-1"><Skeleton class="h-4 w-1/2" /><Skeleton class="h-3 w-3/5" /></div>
					<Skeleton class="h-3 w-8" />
				</div>
			{/each}
		</div>
	{:else if rows.length === 0 || shown.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 px-4 py-10 text-center" data-slot="notes-empty">
			<Inbox aria-hidden="true" class="text-muted-foreground size-6" />
			<p class="text-muted-foreground text-sm">
				{#if rows.length === 0 && query.trim()}
					No note matches “{query.trim()}”{filtered ? ' with these filters' : ''}.
				{:else if rows.length === 0 && filtered}
					No note matches these filters.
				{:else if rows.length === 0}
					No notes in this project yet.
				{:else}
					No loaded note is waiting on {WAITING_OPTIONS.find((option) => option.value === waitingFilter)?.label.toLowerCase()}.
				{/if}
			</p>
			{#if rows.length === 0 && (query.trim() || filtered)}
				<Button size="sm" variant="outline" onclick={onClearFilters}>Clear the search and filters</Button>
			{:else if rows.length > 0}
				<Button size="sm" variant="outline" onclick={() => (waitingFilter = 'any')}>Show every note</Button>
			{/if}
		</div>
	{:else}
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -- the handler only moves focus between the row buttons -->
		<div
			bind:this={list}
			class={cn('group/list min-h-0 flex-1 overflow-auto transition-opacity duration-150', rereading && 'pointer-events-none opacity-50')}
			role="region"
			aria-label="Notes"
			data-slot="notes-scroll"
			data-selecting={anySelected ? 'true' : undefined}
			aria-busy={rereading ? 'true' : undefined}
			onkeydown={onKeydown}
		>
			{#each groups as group (group.key)}
				{@const record = group.record ? records.get(group.key) : undefined}
				{@const closed = grouped && isShut(group.key)}
				<section data-slot="notes-group" data-group-key={group.key}>
					{#if grouped}
						{@const tickState = groupState(group)}
						<div class="group/header border-border sticky top-0 z-10 flex items-center gap-2 border-b bg-[color-mix(in_oklab,var(--muted)_70%,var(--background))] px-2 py-1.5 text-sm">
							<button
								type="button"
								aria-expanded={!closed}
								aria-label={closed ? 'Show these notes' : 'Hide these notes'}
								onclick={() => toggleGroup(group.key)}
								class="focus-visible:ring-ring focus-visible:ring-offset-background text-muted-foreground hover:text-foreground -m-1 flex size-6 shrink-0 items-center justify-center rounded-md outline-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-offset-2"
							>
								<ChevronRight aria-hidden="true" class={cn('size-4 transition-transform duration-150 ease-out motion-reduce:transition-none', !closed && 'rotate-90')} />
							</button>
							<Checkbox
								checked={tickState === 'all'}
								indeterminate={tickState === 'some'}
								aria-label="Select every note in this group"
								tabindex={-1}
								class={cn(
									'transition-opacity duration-150 group-hover/header:opacity-100 focus-visible:opacity-100 group-data-[selecting]/list:opacity-100',
									tickState === 'none' && 'opacity-0'
								)}
								onCheckedChange={(on) => setMany(group.notes.map((note) => note.id), on === true, group.notes[group.notes.length - 1]!.id)}
							/>
							{#if group.record?.type === 'HumanUser'}
								<UserAvatar name={group.record.name ?? '?'} image={imageOf(people.get(group.record.id))} size="sm" />
								<span class="min-w-0 truncate font-medium" title={group.record.name}>{group.record.name}</span>
							{:else if group.record}
								{@const parent = parentOf(group.record)}
								<Thumbnail src={imageOf(record)} alt="" size="sm" />
								<EntityChip entity={group.record} variant="text" {context} class="min-w-0 truncate font-medium" />
								{@render glyph(group.record)}
								{#if parent}
									<span class="text-muted-foreground text-xs">on</span>
									{@render link(parent, false)}
								{/if}
							{:else if group.value !== null && groupBy === 'status'}
								<StatusBadge code={group.value} status={statuses[group.value] ?? null} size="xs" />
							{:else}
								<span class={cn('min-w-0 truncate font-medium', group.value === null && 'text-muted-foreground')}>{group.label}</span>
							{/if}
							<span class="text-muted-foreground ml-auto font-mono text-xs tabular-nums">{group.notes.length}</span>
						</div>
					{/if}
					{#if !closed}
						<ul class="flex flex-col">
							{#each group.notes as note (note.id)}
								{@const author = refOf(note, 'created_by')}
								{@const unread = text(note, 'read_by_current_user') === 'unread'}
								{@const code = text(note, 'sg_status_list')}
								{@const thread = replies.get(note.id)}
								{@const waiting = thread ? waitingOn(note, thread) : null}
								{@const chosen = selected.has(note.id)}
								{@const when = text(note, 'created_at')}
								{@const links = otherLinks(note, [group.record, parentOf(group.record)])}
								<li
									data-slot="notes-row"
									data-row-key="Note:{note.id}"
									data-note-id={note.id}
									data-state={chosen ? 'selected' : undefined}
									data-unread={unread ? 'true' : undefined}
									class={cn(
										'group/row border-border flex items-stretch border-b border-l-2 transition-colors duration-150 motion-safe:animate-in motion-safe:fade-in motion-safe:duration-150',
										chosen ? 'bg-primary/12 border-l-primary' : 'border-l-transparent hover:bg-foreground/4',
										code === 'clsd' && !chosen && 'opacity-60'
									)}
								>
									<span class="flex shrink-0 items-start pt-2 pl-2">
										<Checkbox
											checked={chosen}
											aria-label="Select {firstLine(note)}"
											tabindex={-1}
											class={cn(
												'transition-opacity duration-150 group-hover/row:opacity-100 focus-visible:opacity-100 group-data-[selecting]/list:opacity-100',
												!chosen && 'opacity-0'
											)}
											onclick={(event: MouseEvent) => (shiftHeld = event.shiftKey)}
											onCheckedChange={(on) => boxChange(note, on === true)}
										/>
									</span>
									<button
										type="button"
										aria-pressed={chosen}
										onclick={(event) => rowClick(note, event)}
										class="focus-visible:ring-ring focus-visible:ring-offset-background flex min-w-0 flex-1 select-none items-start gap-2 px-2 py-1.5 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-inset"
									>
										<span class="flex h-5 shrink-0 items-center">
											<UserAvatar name={author?.name ?? '?'} image={personImage(author)} size="sm" />
										</span>
										<span class="flex min-w-0 flex-1 flex-col">
											<span class="flex items-center gap-1.5">
												{#if unread}
													<span class="bg-primary size-1.5 shrink-0 rounded-full" role="img" aria-label="Unread"></span>
												{/if}
												<span class={cn('min-w-0 truncate', unread && 'font-medium')} title={firstLine(note)}>{@render runs(firstLine(note))}</span>
												{#if code}
													<StatusBadge {code} status={statuses[code] ?? null} variant="icon" size="xs" />
												{/if}
												{#if cellValue(note, 'client_note') === true}
													<span class="text-muted-foreground shrink-0 text-xs">client</span>
												{/if}
												{#if refsOf(note, 'attachments').length > 0}
													<Paperclip role="img" aria-label="Has attachments" class="text-muted-foreground size-3.5 shrink-0" />
												{/if}
												{#if thread && thread.length > 0}
													<span class="text-muted-foreground flex shrink-0 items-center gap-1 text-xs tabular-nums" title="{thread.length} replies">
														<MessageSquare aria-hidden="true" class="size-3.5" />{thread.length}
													</span>
												{/if}
											</span>
											<span class="text-muted-foreground min-w-0 truncate text-xs" title={text(note, 'content')}>{@render runs(text(note, 'content'))}</span>
											{#if links.length > 0}
												<span class="flex min-w-0 items-center gap-2 text-xs" data-slot="notes-row-links">
													{#each links.slice(0, 3) as ref (refKey(ref))}
														{@render link(ref, true)}
													{/each}
													{#if links.length > 3}
														<span class="text-muted-foreground tabular-nums">+{links.length - 3}</span>
													{/if}
												</span>
											{/if}
										</span>
										<span class="flex w-44 shrink-0 items-center gap-1.5 text-xs" data-slot="waiting-on" data-waiting={waiting?.kind ?? 'pending'}>
											{#if waiting === null}
												<span class="text-muted-foreground" aria-label="Reading the thread">…</span>
											{:else if waiting.kind === 'closed'}
												<span class="text-muted-foreground">Closed</span>
											{:else if waiting.kind === 'nobody'}
												<span class="text-muted-foreground">Addressed to nobody</span>
											{:else}
												{@const who = waitingWho(waiting)}
												<span class="flex shrink-0 -space-x-1">
													{#each who.slice(0, 3) as ref (ref.id)}
														<UserAvatar name={ref.name ?? '?'} image={personImage(ref)} size="sm" class="ring-background ring-1" />
													{/each}
												</span>
												<span class="min-w-0 truncate" title={waitingLabel(waiting)}>{who.map((ref) => ref.name ?? '').filter(Boolean).join(', ')}</span>
											{/if}
										</span>
										<span class="text-muted-foreground w-14 shrink-0 text-right font-mono text-xs tabular-nums" title={formatDateTime(when, prefs)}>{ago(when)}</span>
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/each}
			{#if status === 'loadingMore'}
				<div class="flex flex-col" aria-busy="true" aria-label="Reading more notes">
					{#each { length: 3 } as _, index (index)}
						<div class="border-border/50 flex items-start gap-2 border-b px-2 py-1.5">
							<Skeleton class="size-4 shrink-0 rounded-sm" />
							<Skeleton class="size-6 shrink-0 rounded-full" />
							<div class="flex flex-1 flex-col gap-1"><Skeleton class="h-4 w-1/2" /><Skeleton class="h-3 w-3/5" /></div>
						</div>
					{/each}
				</div>
			{:else if hasMore}
				<!-- The next page reads itself in when this comes into view; the button is for a reader with no scroll. -->
				<div class="flex justify-center px-2 py-2" {@attach sentinel}>
					<Button size="sm" variant="ghost" onclick={onLoadMore}>Load more</Button>
				</div>
			{/if}
		</div>
	{/if}
</div>
