<!--
	The lead view: the filter bar, the notes under their records, and the thread of
	the one chosen. Built once per project; the site bar reloads the page to change it.
-->
<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import type { EntityRef, EntityRow, FilterGroup, SgClient, SgContext, StatusRecord, WireGroup } from '@sg-widgets/core';
	import { condition, createEntitySource, emptyFilter, entityDetailUrl, group, isEmptyFilter, toApi3Hash } from '@sg-widgets/core';
	import FilterBar from '$lib/components/filter-bar.svelte';
	import { addressees, GROUP_OPTIONS, NOTE_FIELDS, readPeople, readRecords, readReplies, refKey, refOf, refsOf, searchFilter, text, throughRefs, type GroupBy } from '$lib/notes';
	import { createReply } from '$lib/writes';
	import NotesList from './notes-list.svelte';
	import Palette, { type Job } from './palette.svelte';
	import ThreadPane from './thread-pane.svelte';
	import ThreadStack from './thread-stack.svelte';

	let { context, writer, projectId }: { context: SgContext; writer: SgClient; projectId: number } = $props();

	/** The pills the bar offers, in the order a lead reaches for them. */
	const FACETS = ['sg_status_list', 'addressings_to', 'created_by', 'sg_note_type', 'client_note', 'read_by_current_user'];
	// The project and the context are what this component was built for; the page rebuilds it to change them.
	const PROJECT = condition('project', 'is', { type: 'Project', id: untrack(() => projectId) });
	const scope = (tree: FilterGroup, search: FilterGroup | null = null): FilterGroup => group('and', [PROJECT, tree, ...(search ? [search] : [])]);

	let filter = $state<FilterGroup>(emptyFilter());
	/** A search is a filter the site runs, so it reaches every page, not the ones loaded. */
	let query = $state('');
	const GROUP_KEY = 'sg-notes:group';
	const storedGroup = ((): GroupBy => {
		try {
			const value = localStorage.getItem(GROUP_KEY);
			return GROUP_OPTIONS.some((option) => option.value === value) ? (value as GroupBy) : 'record';
		} catch {
			return 'record';
		}
	})();
	let groupBy = $state<GroupBy>(storedGroup);
	$effect(() => {
		try {
			localStorage.setItem(GROUP_KEY, groupBy);
		} catch {
			/* A remembered grouping is a convenience. */
		}
	});

	/** What the Note schema says a note may link and what types it may be, so a search reaches them. */
	let linkTypes = $state<string[]>([]);
	let noteTypes = $state<string[]>([]);
	let noteStatuses = $state<string[]>([]);
	onMount(() => {
		void context.client.fields('Note').then((fields) => {
			linkTypes = fields.note_links?.validTypes ?? [];
			noteTypes = fields.sg_note_type?.validValues ?? [];
			noteStatuses = fields.sg_status_list?.validValues ?? [];
		});
	});

	const source = createEntitySource({
		client: untrack(() => context).client,
		entityType: 'Note',
		fields: NOTE_FIELDS,
		filters: scope(untrack(() => filter)),
		sort: [{ path: 'created_at', descending: true }],
		pageSize: 100,
		mode: 'infinite'
	});
	let snapshot = $state(source.snapshot());
	$effect(() => source.subscribe(() => (snapshot = source.snapshot())));
	onMount(() => void source.load());

	/* What the rows point at, read once per row and kept. */
	let replies = $state<Map<number, EntityRow[]>>(new Map());
	let records = $state<Map<string, EntityRow>>(new Map());
	let people = $state<Map<number, EntityRow>>(new Map());
	let statuses = $state<Record<string, StatusRecord>>({});

	onMount(() => {
		void context.statuses.byCode().then((table) => (statuses = Object.fromEntries(table)));
	});

	// Keystrokes settle before the set is read again; an unchanged tree is not re-read.
	const wire = $derived(JSON.stringify(toApi3Hash(scope(filter, searchFilter(query, linkTypes, statuses, noteTypes)))));
	$effect(() => {
		const next = wire;
		const timer = setTimeout(() => {
			if (JSON.stringify(source.filters) !== next) void source.setFilters(JSON.parse(next) as WireGroup | null);
		}, 250);
		return () => clearTimeout(timer);
	});


	$effect(() => {
		const rows = snapshot.rows;
		untrack(() => void enrich(rows));
	});

	async function enrich(rows: EntityRow[]): Promise<void> {
		const newNotes = rows.filter((note) => !replies.has(note.id));
		// Every link is read: a Version or a Task is the way to the record, the rest are records.
		const unknown = (refs: EntityRef[]): EntityRef[] => refs.filter((ref) => !records.has(refKey(ref)));
		const newLinks = unknown(rows.flatMap((note) => [...refsOf(note, 'note_links'), ...refsOf(note, 'tasks')]));
		const [threads, linked] = await Promise.all([readReplies(context.client, newNotes), readRecords(context.client, newLinks)]);
		if (newNotes.length > 0) {
			const next = new Map(replies);
			for (const note of newNotes) next.set(note.id, threads.get(note.id) ?? []);
			replies = next;
		}
		if (linked.size > 0) records = new Map([...records, ...linked]);
		// Then the records those links reach, so their thumbnails and statuses head the groups.
		const parents = unknown(
			rows.flatMap(throughRefs).map((ref) => records.get(refKey(ref))).flatMap((row) => (row ? (refOf(row, 'entity') ?? []) : []))
		);
		if (parents.length > 0) records = new Map([...records, ...(await readRecords(context.client, parents))]);
		const faces: EntityRef[] = [];
		for (const note of rows) {
			const author = refOf(note, 'created_by');
			if (author) faces.push(author);
			faces.push(...addressees(note));
			for (const reply of threads.get(note.id) ?? []) {
				const user = refOf(reply, 'user');
				if (user) faces.push(user);
			}
		}
		const strangers = faces.filter((ref) => !people.has(ref.id));
		if (strangers.length > 0) people = new Map([...people, ...(await readPeople(context.client, strangers))]);
	}

	/* The selection: what the pane shows and what an action applies to. */

	const selection = new SvelteSet<number>();
	/** The notes the pane shows in full when several are selected: the last one selected, until lines are pressed. */
	const expanded = new SvelteSet<number>();
	let list = $state<NotesList | null>(null);
	let paletteOpen = $state(false);
	let job = $state<Job | null>(null);

	function setSelection(ids: number[], last: number | null): void {
		selection.clear();
		for (const id of ids) selection.add(id);
		for (const id of expanded) if (!selection.has(id)) expanded.delete(id);
		if (last !== null) {
			expanded.clear();
			expanded.add(last);
		}
	}

	/** The selected notes as the source holds them, so a write shows without a re-pick. */
	const selectedRows = $derived(snapshot.rows.filter((row) => selection.has(row.id)));
	const single = $derived(selectedRows.length === 1 ? selectedRows[0]! : null);
	const targets = $derived(selectedRows);

	function onKeydown(event: KeyboardEvent): void {
		if (event.key.toLowerCase() === 'k' && (event.metaKey || event.ctrlKey)) {
			event.preventDefault();
			paletteOpen = !paletteOpen;
		}
	}

	/** One write per note, in order, each failure named; then everything is read again. */
	async function runJob(label: string, notes: EntityRow[], write: (note: EntityRow) => Promise<void>): Promise<void> {
		job = { label, done: 0, total: notes.length, failures: [] };
		for (const note of notes) {
			try {
				await write(note);
			} catch (error) {
				const title = text(note, 'subject') || `Note ${note.id}`;
				job = { ...job, failures: [...job.failures, `${title}: ${error instanceof Error ? error.message : String(error)}`] };
			}
			job = { ...job, done: job.done + 1 };
		}
		context.invalidate();
		const fresh = await readReplies(context.client, notes);
		replies = new Map([...replies, ...fresh]);
		await source.refresh();
	}

	function bulkStatus(notes: EntityRow[], code: string): void {
		const name = statuses[code]?.name ?? code;
		void runJob(`Setting ${notes.length} to ${name}`, notes, (note) => source.updateRow({ type: 'Note', id: note.id }, { sg_status_list: code }).then(() => undefined));
	}

	/** `read_by_current_user` takes a PUT as the person whose state it is (README, "What surprised"). */
	function bulkRead(notes: EntityRow[], read: boolean): void {
		void runJob(`Marking ${notes.length} ${read ? 'read' : 'unread'}`, notes, (note) =>
			source.updateRow({ type: 'Note', id: note.id }, { read_by_current_user: read ? 'read' : 'unread' }).then(() => undefined)
		);
	}

	function bulkReply(notes: EntityRow[], content: string): void {
		void runJob(`Replying to ${notes.length}`, notes, (note) => createReply(writer, { type: 'Note', id: note.id }, content).then(() => undefined));
	}

	function openInWebApp(notes: EntityRow[]): void {
		for (const note of notes) {
			const url = entityDetailUrl(context.siteUrl, { type: 'Note', id: note.id });
			if (url) window.open(url, '_blank', 'noopener');
		}
	}

	async function replyTo(note: EntityRow, content: string): Promise<void> {
		await createReply(writer, { type: 'Note', id: note.id }, content);
		// The thread is read from Reply rows, and the note's own `replies` list moved too.
		const fresh = await readReplies(context.client, [note]);
		replies = new Map([...replies, [note.id, fresh.get(note.id) ?? []]]);
		context.invalidate();
		await source.refresh();
	}
</script>

<svelte:window onkeydown={onKeydown} />

{#snippet pane(note: EntityRow)}
	<ThreadPane
		{context}
		{writer}
		{note}
		replies={replies.get(note.id) ?? []}
		{records}
		{statuses}
		{projectId}
		onStatus={(code) => source.updateRow({ type: 'Note', id: note.id }, { sg_status_list: code }).then(() => undefined)}
		onReply={(content) => replyTo(note, content)}
	/>
{/snippet}

<div class="flex min-h-0 flex-1 flex-col" data-slot="workbench">
	<div class="border-border flex shrink-0 items-center gap-2 border-b px-3 py-2">
		<FilterBar entityType="Note" {context} facets={FACETS} baseFilter={group('and', [PROJECT])} bind:value={filter} size="sm" class="min-w-0 flex-1" />
		<span class="text-muted-foreground shrink-0 font-mono text-xs tabular-nums" data-slot="row-count">
			{snapshot.rows.length}{snapshot.hasMore ? '+' : ''} notes
		</span>
	</div>
	<div class="flex min-h-0 flex-1">
		<NotesList
			bind:this={list}
			{context}
			rows={snapshot.rows}
			status={snapshot.status}
			error={snapshot.error}
			hasMore={snapshot.hasMore}
			filtered={!isEmptyFilter(filter)}
			onLoadMore={() => void source.loadMore()}
			onRetry={() => void (snapshot.rows.length === 0 ? source.load() : source.loadMore())}
			{replies}
			{records}
			{people}
			{statuses}
			selected={selection}
			onSelectionChange={setSelection}
			bind:groupBy
			bind:query
			onActions={() => (paletteOpen = true)}
		/>
		<aside class="border-border bg-background w-[32rem] shrink-0 overflow-auto border-l" data-slot="thread">
			{#if selectedRows.length > 1}
				<ThreadStack
					notes={selectedRows}
					{statuses}
					{expanded}
					onExpand={(ids) => {
						expanded.clear();
						for (const id of ids) expanded.add(id);
					}}
					{pane}
				/>
			{:else if single}
				{#key single.id}
					{@render pane(single)}
				{/key}
			{:else}
				<p class="text-muted-foreground flex items-center justify-center px-4 py-10 text-sm">Pick a note to read its thread.</p>
			{/if}
		</aside>
	</div>
</div>

<Palette
	bind:open={paletteOpen}
	{targets}
	several={selectedRows.length > 1}
	{statuses}
	{noteStatuses}
	{groupBy}
	{job}
	onStatus={bulkStatus}
	onRead={bulkRead}
	onReply={bulkReply}
	onGroupBy={(value) => (groupBy = value)}
	onSelectAll={() => setSelection(snapshot.rows.map((row) => row.id), null)}
	onClearSelection={() => setSelection([], null)}
	onCollapseAll={() => list?.collapseAll()}
	onExpandAll={() => list?.expandAll()}
	onOpen={openInWebApp}
	onJobRead={() => (job = null)}
/>
