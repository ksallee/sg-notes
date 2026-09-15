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
-->
<script lang="ts">
	import type { EntityRef, EntityRow, SgContext, StatusRecord } from '@sg-widgets/core';
	import { cellValue, formatDateTime, preferencesOf } from '@sg-widgets/core';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ChevronsDownUp from '@lucide/svelte/icons/chevrons-down-up';
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	import SearchIcon from '@lucide/svelte/icons/search';
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
	import { GROUP_OPTIONS, groupNotes, isClientFacing, refKey, refOf, refsOf, text, waitingOn, type GroupBy, type Waiting } from '$lib/notes';
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
		selected: EntityRef | null;
		onSelect: (note: EntityRow) => void;
		/** What the rows are grouped on, two-way. */
		groupBy?: GroupBy;
		/** The search the page applies, two-way. The list draws the box; the page reads. */
		query?: string;
		/** Ids of the ticked notes, for a bulk action. */
		ticked: ReadonlySet<number>;
		onTickChange: (ids: number[], on: boolean) => void;
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
		onSelect,
		groupBy = $bindable('record'),
		query = $bindable(''),
		ticked,
		onTickChange,
		onActions
	}: Props = $props();

	export function collapseAll(): void {
		setShut(groups.map((group) => group.key));
	}

	export function expandAll(): void {
		setShut([]);
	}

	const groups = $derived(groupNotes(rows, records, groupBy));
	const groupLabel = $derived(GROUP_OPTIONS.find((option) => option.value === groupBy)?.label ?? '');
	const grouped = $derived(groupBy !== 'none');

	/** The last row ticked, so a shift-click ticks the run between. */
	let lastTick = $state<number | null>(null);
	let shiftHeld = false;

	/** Every note id in the order the list shows them, across groups. */
	const order = $derived(groups.flatMap((group) => group.notes.map((note) => note.id)));

	function tick(note: EntityRow, on: boolean): void {
		let ids = [note.id];
		if (shiftHeld && lastTick !== null) {
			const a = order.indexOf(lastTick);
			const b = order.indexOf(note.id);
			if (a !== -1 && b !== -1) ids = order.slice(Math.min(a, b), Math.max(a, b) + 1);
		}
		lastTick = note.id;
		onTickChange([...new Set(ids)], on);
	}

	function groupTick(group: { notes: EntityRow[] }): 'all' | 'some' | 'none' {
		const on = group.notes.filter((note) => ticked.has(note.id)).length;
		return on === 0 ? 'none' : on === group.notes.length ? 'all' : 'some';
	}

	const selectedKey = $derived(selected ? refKey(selected) : '');
	const prefs = $derived(preferencesOf(context));
	/** The first read, with nothing to show yet. A later read keeps the rows and dims them. */
	const firstRead = $derived((status === 'loading' || status === 'idle') && rows.length === 0);
	const rereading = $derived(status === 'loading' && rows.length > 0);

	/** What is shut, per grouping, so switching away and back finds the groups as they were left. */
	let shutBy = $state<Partial<Record<GroupBy, string[]>>>({});
	const shut = $derived(shutBy[groupBy] ?? []);
	let list = $state<HTMLElement | null>(null);

	function setShut(keys: string[]): void {
		shutBy = { ...shutBy, [groupBy]: keys };
	}

	function toggle(key: string): void {
		setShut(shut.includes(key) ? shut.filter((k) => k !== key) : [...shut, key]);
	}

	/** Arrow keys walk the rows, Home and End jump, so a lead reads the list without a mouse. */
	function onKeydown(event: KeyboardEvent): void {
		if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key) || !list) return;
		const buttons = [...list.querySelectorAll<HTMLButtonElement>('[data-slot="notes-row"] button')];
		if (buttons.length === 0) return;
		const at = buttons.indexOf(document.activeElement as HTMLButtonElement);
		let next = at;
		if (event.key === 'ArrowDown') next = Math.min(buttons.length - 1, at + 1);
		else if (event.key === 'ArrowUp') next = Math.max(0, at - 1);
		else if (event.key === 'Home') next = 0;
		else next = buttons.length - 1;
		if (next === at && at !== -1) return;
		event.preventDefault();
		buttons[next === -1 ? 0 : next]?.focus({ preventScroll: false });
	}

	/** The row a link resolves to, when it has been read. */
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

	function waitingLabel(waiting: Waiting): string {
		switch (waiting.kind) {
			case 'closed':
				return '';
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
			<SearchIcon aria-hidden="true" class="text-muted-foreground pointer-events-none absolute top-1/2 left-2 size-3.5 -translate-y-1/2" />
			<Input type="search" bind:value={query} placeholder="Search" aria-label="Search notes" class="h-7 pl-7 text-sm" />
		</div>
		<Select.Root type="single" value={groupBy} onValueChange={(value) => (groupBy = value as GroupBy)}>
			<Select.Trigger size="sm" aria-label="Group by" class="ml-auto">
				<span data-slot="select-value"><span class="text-muted-foreground">Group by</span> {groupLabel}</span>
			</Select.Trigger>
			<Select.Content>
				{#each GROUP_OPTIONS as option (option.value)}
					<Select.Item value={option.value} label={option.label} />
				{/each}
			</Select.Content>
		</Select.Root>
		<Button size="icon-xs" variant="ghost" aria-label="Collapse all" title="Collapse all" disabled={!grouped} onclick={collapseAll}>
			<ChevronsDownUp aria-hidden="true" />
		</Button>
		<Button size="icon-xs" variant="ghost" aria-label="Expand all" title="Expand all" disabled={!grouped} onclick={expandAll}>
			<ChevronsUpDown aria-hidden="true" />
		</Button>
		<Button size="sm" variant={ticked.size > 0 ? 'default' : 'outline'} onclick={onActions} data-slot="actions-button">
			{ticked.size > 0 ? `${ticked.size} ticked` : 'Actions'}
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
	{:else if rows.length === 0}
		<StateLine state="empty" pad="table" icon={Inbox} label={filtered || query ? 'No note matches this filter' : 'No notes in this project yet'} />
	{:else}
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -- the handler only moves focus between the row buttons -->
		<div
			bind:this={list}
			class={cn('min-h-0 flex-1 overflow-auto transition-opacity duration-150', rereading && 'pointer-events-none opacity-50')}
			role="region"
			aria-label="Notes"
			aria-busy={rereading ? 'true' : undefined}
			onkeydown={onKeydown}
		>
			{#each groups as group (group.key)}
				{@const record = group.record ? records.get(group.key) : undefined}
				{@const closed = grouped && shut.includes(group.key)}
				<section data-slot="notes-group" data-group-key={group.key}>
					{#if grouped}
						{@const tickState = groupTick(group)}
						<div class="border-border sticky top-0 z-10 flex items-center gap-2 border-b bg-[color-mix(in_oklab,var(--muted)_70%,var(--background))] px-2 py-1.5 text-sm">
							<button
								type="button"
								aria-expanded={!closed}
								aria-label={closed ? 'Show these notes' : 'Hide these notes'}
								onclick={() => toggle(group.key)}
								class="focus-visible:ring-ring focus-visible:ring-offset-background text-muted-foreground hover:text-foreground -m-1 flex size-6 shrink-0 items-center justify-center rounded-md outline-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-offset-2"
							>
								<ChevronRight aria-hidden="true" class={cn('size-4 transition-transform duration-150 ease-out motion-reduce:transition-none', !closed && 'rotate-90')} />
							</button>
							<Checkbox
								checked={tickState === 'all'}
								indeterminate={tickState === 'some'}
								aria-label="Tick every note in this group"
								onCheckedChange={(on) => onTickChange(group.notes.map((note) => note.id), on === true)}
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
								{@const chosen = selectedKey === `Note:${note.id}`}
								{@const when = text(note, 'created_at')}
								{@const links = otherLinks(note, [group.record, parentOf(group.record)])}
								{@const isTicked = ticked.has(note.id)}
								<li
									data-slot="notes-row"
									data-row-key="Note:{note.id}"
									data-state={chosen ? 'selected' : undefined}
									data-unread={unread ? 'true' : undefined}
									data-ticked={isTicked ? 'true' : undefined}
									class={cn(
										'border-border/50 flex items-stretch border-b transition-colors duration-150 motion-safe:animate-in motion-safe:fade-in motion-safe:duration-150',
										chosen ? 'bg-accent text-accent-foreground' : isTicked ? 'bg-accent/40' : 'hover:bg-muted/50'
									)}
								>
									<span class="flex shrink-0 items-start pt-2 pl-2">
										<Checkbox
											checked={isTicked}
											aria-label="Tick {firstLine(note)}"
											onclick={(event: MouseEvent) => (shiftHeld = event.shiftKey)}
											onCheckedChange={(on) => tick(note, on === true)}
										/>
									</span>
									<button
										type="button"
										aria-pressed={chosen}
										onclick={() => onSelect(note)}
										class="focus-visible:ring-ring focus-visible:ring-offset-background flex min-w-0 flex-1 items-start gap-2 px-2 py-1.5 text-left text-sm outline-none focus-visible:ring-2 focus-visible:ring-inset"
									>
										<span class="flex h-5 shrink-0 items-center">
											<UserAvatar name={author?.name ?? '?'} image={personImage(author)} size="sm" />
										</span>
										<span class="flex min-w-0 flex-1 flex-col">
											<span class="flex items-center gap-1.5">
												{#if unread}
													<span class="bg-primary size-1.5 shrink-0 rounded-full" role="img" aria-label="Unread"></span>
												{/if}
												<span class={cn('min-w-0 truncate', unread && 'font-medium')} title={firstLine(note)}>{firstLine(note)}</span>
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
											<span class="text-muted-foreground min-w-0 truncate text-xs" title={text(note, 'content')}>
												{author?.name ?? ''}{text(note, 'content') ? ` · ${text(note, 'content')}` : ''}
											</span>
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
										<span class="flex shrink-0 flex-col items-end gap-0.5 text-xs">
											<span class="text-muted-foreground tabular-nums" title={formatDateTime(when, prefs)}>{ago(when)}</span>
											{#if waiting === null}
												<Skeleton class="h-3 w-20" />
											{:else if waiting.kind !== 'closed'}
												<span class="text-muted-foreground max-w-40 truncate" title={waitingLabel(waiting)}>{waitingLabel(waiting)}</span>
											{/if}
										</span>
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</section>
			{/each}
			{#if hasMore || status === 'loadingMore'}
				<div class="flex justify-center px-2 py-2">
					<Button size="sm" variant="ghost" onclick={onLoadMore} disabled={status === 'loadingMore'}>
						{status === 'loadingMore' ? 'Reading more…' : 'Load more'}
					</Button>
				</div>
			{/if}
		</div>
	{/if}
</div>
