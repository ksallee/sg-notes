/**
 * The notes model: what the lead view reads, how notes fall under the record they
 * are about, and who a note is waiting on.
 *
 * Framework-neutral on purpose, so the rules are testable without a page, and so
 * the ones that survive can move to sg-widgets core when a second host wants them.
 */
import type { EntityRef, EntityRow, FilterGroup, SgClient } from '@sg-widgets/core';
import { condition, group, toApi3Hash } from '@sg-widgets/core';

/** What a note row carries in the list and the thread (entity_types/Note). */
export const NOTE_FIELDS = [
	'subject',
	'content',
	'created_at',
	'updated_at',
	'sg_status_list',
	'sg_note_type',
	'client_note',
	'read_by_current_user',
	'created_by',
	'note_links',
	'tasks',
	'addressings_to',
	'addressings_cc',
	'replies',
	'attachments'
];

/** What a reply carries. Its author is `user`, not `created_by` (get_entity_notes_id_thread_contents). */
export const REPLY_FIELDS = ['content', 'created_at', 'user', 'entity'];

/** The closed status of a Note, the one code every site ships (finding 061). */
export const CLOSED = 'clsd';

/** Rows the site does not cap a page at (finding 016 measured 500 answering 300, the whole set). */
const WIDE_PAGE = 500;

export function refKey(ref: EntityRef): string {
	return `${ref.type}:${ref.id}`;
}

export function refOf(row: EntityRow, path: string): EntityRef | null {
	const value = row.relationships[path]?.data;
	return value && !Array.isArray(value) ? value : null;
}

export function refsOf(row: EntityRow, path: string): EntityRef[] {
	const value = row.relationships[path]?.data;
	return Array.isArray(value) ? value : [];
}

export function text(row: EntityRow, path: string): string {
	const value = row.attributes[path];
	return typeof value === 'string' ? value : value == null ? '' : String(value);
}

/**
 * Types a note reaches a record through rather than being about. A Version or a
 * Task carries `entity`, the Shot, Asset, Sequence or whatever the site links it
 * to; the note is about that. Any other linked type is the record itself: the
 * site's preferences say which types take notes at all, and the Note schema's
 * `note_links` lists them as its `valid_types`.
 */
const THROUGH = new Set(['Version', 'Task']);

/**
 * The record a note is about. The first link that is not a Version or a Task;
 * else the `entity` of the first Version or Task whose row is known; else the
 * link itself until that row is read. A note on a Task alone falls under the
 * Task's entity the same way.
 */
export function recordOf(note: EntityRow, records?: ReadonlyMap<string, EntityRow>): EntityRef | null {
	const links = refsOf(note, 'note_links');
	const direct = links.find((ref) => !THROUGH.has(ref.type));
	if (direct) return direct;
	const through = [...links, ...refsOf(note, 'tasks')];
	for (const ref of through) {
		const row = records?.get(refKey(ref));
		const parent = row ? refOf(row, 'entity') : null;
		if (parent) return parent;
	}
	return through[0] ?? null;
}

/** The rows a record is reached through, so their `entity` can be read. */
export function throughRefs(note: EntityRow): EntityRef[] {
	return [...refsOf(note, 'note_links'), ...refsOf(note, 'tasks')].filter((ref) => THROUGH.has(ref.type));
}

/** The Version a note was written on, when it was. */
export function versionOf(note: EntityRow): EntityRef | null {
	return refsOf(note, 'note_links').find((ref) => ref.type === 'Version') ?? null;
}

/** What the list groups on: a way to a record, a link as such, a person, or a value. */
export type GroupBy = 'record' | 'link' | 'task' | 'version' | 'author' | 'addressee' | 'status' | 'type' | 'none';

export const GROUP_OPTIONS: ReadonlyArray<{ value: GroupBy; label: string }> = [
	{ value: 'record', label: 'Record' },
	{ value: 'link', label: 'Link' },
	{ value: 'task', label: 'Task' },
	{ value: 'version', label: 'Version' },
	{ value: 'author', label: 'Author' },
	{ value: 'addressee', label: 'Addressed to' },
	{ value: 'status', label: 'Status' },
	{ value: 'type', label: 'Note type' },
	{ value: 'none', label: 'Nothing' }
];

/** What a note falls under when it has no value for the grouping. */
const NO_VALUE: Record<GroupBy, string> = {
	record: 'Linked to nothing',
	link: 'Linked to nothing',
	task: 'No task',
	version: 'No version',
	author: 'Nobody',
	addressee: 'Addressed to nobody',
	status: 'No status',
	type: 'No type',
	none: 'All notes'
};

export interface NoteGroup {
	/** `Type:id` of an entity, `value:<code>` of a value, or `none`. */
	key: string;
	/** The entity the group is, when it is one. */
	record: EntityRef | null;
	/** The value the group is, when it is one: a status code, a note type. */
	value: string | null;
	/** What the header says when there is no entity to name. */
	label: string;
	notes: EntityRow[];
}

/** The entities or values one note falls under. Several for a multi-valued field. */
function groupsOf(note: EntityRow, by: GroupBy, records?: ReadonlyMap<string, EntityRow>): Array<{ record?: EntityRef; value?: string }> {
	switch (by) {
		case 'record': {
			const record = recordOf(note, records);
			return record ? [{ record }] : [];
		}
		case 'link':
			return refsOf(note, 'note_links').map((record) => ({ record }));
		case 'task':
			return refsOf(note, 'tasks').map((record) => ({ record }));
		case 'version':
			return refsOf(note, 'note_links').filter((ref) => ref.type === 'Version').map((record) => ({ record }));
		case 'author': {
			const author = refOf(note, 'created_by');
			return author ? [{ record: author }] : [];
		}
		case 'addressee':
			return addressees(note).map((record) => ({ record }));
		case 'status':
			return text(note, 'sg_status_list') ? [{ value: text(note, 'sg_status_list') }] : [];
		case 'type':
			return text(note, 'sg_note_type') ? [{ value: text(note, 'sg_note_type') }] : [];
		default:
			return [{ value: '' }];
	}
}

/**
 * Notes under what they are grouped on, groups in the order the rows arrived. A
 * note with two links, two tasks or two addressees is under each of them; a note
 * with none is under the group that says so, which comes last.
 */
export function groupNotes(rows: readonly EntityRow[], records?: ReadonlyMap<string, EntityRow>, by: GroupBy = 'record'): NoteGroup[] {
	const groups = new Map<string, NoteGroup>();
	const none: NoteGroup = { key: 'none', record: null, value: null, label: NO_VALUE[by], notes: [] };
	for (const note of rows) {
		const under = groupsOf(note, by, records);
		if (under.length === 0) {
			none.notes.push(note);
			continue;
		}
		for (const { record, value } of under) {
			const key = record ? refKey(record) : `value:${value}`;
			let bucket = groups.get(key);
			if (!bucket) {
				bucket = { key, record: record ?? null, value: value ?? null, label: record?.name ?? value ?? '', notes: [] };
				groups.set(key, bucket);
			}
			bucket.notes.push(note);
		}
	}
	const out = [...groups.values()];
	if (none.notes.length > 0) out.push(none);
	return out;
}

/** Everyone a note is addressed to, `to` first. */
export function addressees(note: EntityRow): EntityRef[] {
	const seen = new Set<string>();
	const out: EntityRef[] = [];
	for (const ref of [...refsOf(note, 'addressings_to'), ...refsOf(note, 'addressings_cc')]) {
		const key = refKey(ref);
		if (seen.has(key)) continue;
		seen.add(key);
		out.push(ref);
	}
	return out;
}

export type Waiting =
	| { kind: 'closed' }
	| { kind: 'nobody' }
	| { kind: 'author'; who: EntityRef }
	| { kind: 'addressees'; who: EntityRef[] };

/**
 * Who owes the next word. The last row of the thread is the note itself or its
 * newest reply. When an addressee wrote it, the ball is with the note's author;
 * otherwise it is with the addressees. A closed note waits on nobody, and so does
 * a note addressed to nobody, which is the forum's "note on the wrong record"
 * (research/03).
 */
export function waitingOn(note: EntityRow, replies: readonly EntityRow[]): Waiting {
	if (text(note, 'sg_status_list') === CLOSED) return { kind: 'closed' };
	const author = refOf(note, 'created_by');
	const to = addressees(note);
	if (to.length === 0) return { kind: 'nobody' };
	const last = replies.length > 0 ? refOf(replies[replies.length - 1]!, 'user') : author;
	const lastKey = last ? refKey(last) : '';
	if (to.some((ref) => refKey(ref) === lastKey)) {
		return author ? { kind: 'author', who: author } : { kind: 'nobody' };
	}
	return { kind: 'addressees', who: to };
}

/**
 * A search as the site runs it, over everything the list can group on: the
 * subject and content, the author's and the addressees' names, the note type,
 * a status whose label matches, the linked task's name and the name of any
 * linked record, one path per type the site lets a note link (the `valid_types`
 * of `note_links`, which the site's preferences decide). A dotted path through a
 * multi-entity field filters, though it will not read (finding 016). A record's
 * name is reached as `cached_display_name`, which filters through a link on every
 * type; `code` and `name` each fail on some (a Booking has no `code`, a Group no
 * `name`: measured on the operator's site, 2026-09-15).
 */
export function searchFilter(
	query: string,
	linkTypes: readonly string[],
	statuses: Readonly<Record<string, { name: string }>> = {},
	noteTypes: readonly string[] = []
): FilterGroup | null {
	const q = query.trim();
	if (!q) return null;
	const matches = (label: string): boolean => label.toLowerCase().includes(q.toLowerCase());
	const codes = Object.entries(statuses).filter(([, status]) => matches(status.name)).map(([code]) => code);
	// A list field takes `in`, not `contains` (measured: 400 on the operator's site).
	const types = noteTypes.filter(matches);
	return group('or', [
		condition('subject', 'contains', q),
		condition('content', 'contains', q),
		condition('created_by.HumanUser.name', 'contains', q),
		condition('addressings_to.HumanUser.name', 'contains', q),
		condition('addressings_cc.HumanUser.name', 'contains', q),
		condition('addressings_to.Group.code', 'contains', q),
		condition('tasks.Task.content', 'contains', q),
		...linkTypes.map((type) => condition(`note_links.${type}.cached_display_name`, 'contains', q)),
		...(codes.length > 0 ? [condition('sg_status_list', 'in', codes)] : []),
		...(types.length > 0 ? [condition('sg_note_type', 'in', types)] : [])
	]);
}

/** Rows in `created_at` order, oldest first, the order a thread reads in. */
export function byCreated(rows: readonly EntityRow[]): EntityRow[] {
	return [...rows].sort((a, b) => text(a, 'created_at').localeCompare(text(b, 'created_at')));
}

async function readAll(client: SgClient, entityType: string, filters: ReturnType<typeof toApi3Hash>, fields: string[], sort?: string): Promise<EntityRow[]> {
	const rows: EntityRow[] = [];
	for (let number = 1; ; number += 1) {
		const page = await client.search(entityType, { filters, fields, ...(sort ? { sort } : {}), page: { size: WIDE_PAGE, number } });
		rows.push(...page.data);
		if (!page.hasMore) return rows;
	}
}

/**
 * Every reply under the given notes, keyed by note id, oldest first. One read for
 * the page: `entity in [...]` takes full `{type, id}` hashes (finding 017).
 */
export async function readReplies(client: SgClient, notes: readonly EntityRow[]): Promise<Map<number, EntityRow[]>> {
	const out = new Map<number, EntityRow[]>();
	if (notes.length === 0) return out;
	const refs = notes.map((note) => ({ type: 'Note', id: note.id }));
	const rows = await readAll(client, 'Reply', toApi3Hash(group('and', [condition('entity', 'in', refs)])), REPLY_FIELDS, 'created_at');
	for (const reply of rows) {
		const note = refOf(reply, 'entity');
		if (!note) continue;
		const list = out.get(note.id) ?? [];
		list.push(reply);
		out.set(note.id, list);
	}
	return out;
}

/**
 * What the list shows of a record: its thumbnail and its status, and `entity` on
 * the types that reach a record through it. A name a type does not have is
 * dropped from the answer without a word (probe 004), so one list serves every type.
 */
const RECORD_FIELDS = ['code', 'image', 'sg_status_list', 'entity'];

/**
 * The records a set of notes point at, keyed `Type:id`. One read per type; a
 * dotted path through `note_links` reads back nothing (finding 016), so the rows
 * are asked for directly.
 */
export async function readRecords(client: SgClient, refs: readonly EntityRef[]): Promise<Map<string, EntityRow>> {
	const byType = new Map<string, number[]>();
	for (const ref of refs) {
		const ids = byType.get(ref.type) ?? [];
		if (!ids.includes(ref.id)) ids.push(ref.id);
		byType.set(ref.type, ids);
	}
	const out = new Map<string, EntityRow>();
	await Promise.all(
		[...byType].map(async ([type, ids]) => {
			const rows = await readAll(client, type, toApi3Hash(group('and', [condition('id', 'in', ids)])), RECORD_FIELDS);
			for (const row of rows) out.set(refKey(row), row);
		})
	);
	return out;
}

/** The people behind the avatars: `image` is the only thing a link does not carry. */
export async function readPeople(client: SgClient, refs: readonly EntityRef[]): Promise<Map<number, EntityRow>> {
	const ids = [...new Set(refs.filter((ref) => ref.type === 'HumanUser').map((ref) => ref.id))];
	const out = new Map<number, EntityRow>();
	if (ids.length === 0) return out;
	const rows = await readAll(client, 'HumanUser', toApi3Hash(group('and', [condition('id', 'in', ids)])), ['name', 'image', 'sg_status_list']);
	for (const row of rows) out.set(row.id, row);
	return out;
}
