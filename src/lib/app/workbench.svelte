<!--
	The lead view: the filter bar, the notes under their records, and the thread of
	the one chosen. Built once per project; the site bar reloads the page to change it.
-->
<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import type { EntityRef, EntityRow, FilterGroup, SgClient, SgContext, StatusRecord, WireGroup } from '@sg-widgets/core';
	import { condition, createEntitySource, emptyFilter, group, isEmptyFilter, toApi3Hash } from '@sg-widgets/core';
	import FilterBar from '$lib/components/filter-bar.svelte';
	import { addressees, NOTE_FIELDS, readPeople, readRecords, readReplies, refKey, refOf, refsOf, throughRefs } from '$lib/notes';
	import { createReply } from '$lib/writes';
	import NotesList from './notes-list.svelte';
	import ThreadPane from './thread-pane.svelte';

	let { context, writer, projectId }: { context: SgContext; writer: SgClient; projectId: number } = $props();

	/** The pills the bar offers, in the order a lead reaches for them. */
	const FACETS = ['sg_status_list', 'addressings_to', 'created_by', 'sg_note_type', 'client_note', 'read_by_current_user'];
	// The project and the context are what this component was built for; the page rebuilds it to change them.
	const PROJECT = condition('project', 'is', { type: 'Project', id: untrack(() => projectId) });
	const scope = (tree: FilterGroup): FilterGroup => group('and', [PROJECT, tree]);

	let filter = $state<FilterGroup>(emptyFilter());

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

	// Keystrokes settle before the set is read again; an unchanged tree is not re-read.
	const wire = $derived(JSON.stringify(toApi3Hash(scope(filter))));
	$effect(() => {
		const next = wire;
		const timer = setTimeout(() => {
			if (JSON.stringify(source.filters) !== next) void source.setFilters(JSON.parse(next) as WireGroup | null);
		}, 250);
		return () => clearTimeout(timer);
	});

	/* What the rows point at, read once per row and kept. */
	let replies = $state<Map<number, EntityRow[]>>(new Map());
	let records = $state<Map<string, EntityRow>>(new Map());
	let people = $state<Map<number, EntityRow>>(new Map());
	let statuses = $state<Record<string, StatusRecord>>({});

	onMount(() => {
		void context.statuses.byCode().then((table) => (statuses = Object.fromEntries(table)));
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

	let selectedRef = $state<EntityRef | null>(null);
	/** The chosen note as the source now holds it, so a status write shows without a re-pick. */
	const selected = $derived(selectedRef ? (snapshot.rows.find((row) => row.id === selectedRef!.id) ?? null) : null);

	async function setStatus(code: string): Promise<void> {
		if (!selected) return;
		await source.updateRow({ type: 'Note', id: selected.id }, { sg_status_list: code });
	}

	async function reply(content: string): Promise<void> {
		if (!selected) return;
		const note = selected;
		await createReply(writer, { type: 'Note', id: note.id }, content);
		// The thread is read from Reply rows, and the note's own `replies` list moved too.
		const fresh = await readReplies(context.client, [note]);
		replies = new Map([...replies, [note.id, fresh.get(note.id) ?? []]]);
		context.invalidate();
		await source.refresh();
	}
</script>

<div class="flex min-h-0 flex-1 flex-col" data-slot="workbench">
	<div class="border-border flex shrink-0 items-center gap-2 border-b px-3 py-2">
		<FilterBar entityType="Note" {context} facets={FACETS} baseFilter={group('and', [PROJECT])} bind:value={filter} size="sm" class="min-w-0 flex-1" />
		<span class="text-muted-foreground shrink-0 text-xs tabular-nums" data-slot="row-count">
			{snapshot.rows.length}{snapshot.hasMore ? '+' : ''} notes
		</span>
	</div>
	<div class="flex min-h-0 flex-1">
		<NotesList
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
			selected={selectedRef}
			onSelect={(note) => (selectedRef = { type: 'Note', id: note.id })}
		/>
		<aside class="border-border bg-background w-[32rem] shrink-0 overflow-auto border-l" data-slot="thread">
			{#if selected}
				{#key selected.id}
					<ThreadPane {context} {writer} note={selected} replies={replies.get(selected.id) ?? []} {records} {statuses} {projectId} onStatus={setStatus} onReply={reply} />
				{/key}
			{:else}
				<p class="text-muted-foreground flex items-center justify-center px-4 py-10 text-sm">Pick a note to read its thread.</p>
			{/if}
		</aside>
	</div>
</div>
