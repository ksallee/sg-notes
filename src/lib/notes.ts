/**
 * The notes model: what the lead view reads, how notes fall under the record they
 * are about, and who a note is waiting on.
 *
 * Framework-neutral on purpose, so the rules are testable without a page, and so
 * the ones that survive can move to sg-widgets core when a second host wants them.
 */
import type { EntityRef, EntityRow, SgClient } from '@sg-widgets/core';
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
 * The record a note is about. A note written from a Version links the Version and
 * the Shot or Asset it belongs to (`note_links` carries both, finding 067); the
 * Shot or Asset is the record, the Version is where it was said. A note on a
 * Version alone falls under that Version.
 */
export function recordOf(note: EntityRow): EntityRef | null {
	const links = refsOf(note, 'note_links');
	return links.find((ref) => ref.type !== 'Version') ?? links[0] ?? null;
}

/** The Version a note was written on, when it was. */
export function versionOf(note: EntityRow): EntityRef | null {
	return refsOf(note, 'note_links').find((ref) => ref.type === 'Version') ?? null;
}

export interface NoteGroup {
	/** `Type:id` of the record, or `none` for notes linked to nothing. */
	key: string;
	record: EntityRef | null;
	notes: EntityRow[];
}

/** Notes under the record they are about, groups in the order the rows arrived. */
export function groupNotes(rows: readonly EntityRow[]): NoteGroup[] {
	const groups = new Map<string, NoteGroup>();
	for (const note of rows) {
		const record = recordOf(note);
		const key = record ? refKey(record) : 'none';
		let bucket = groups.get(key);
		if (!bucket) {
			bucket = { key, record, notes: [] };
			groups.set(key, bucket);
		}
		bucket.notes.push(note);
	}
	return [...groups.values()];
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

/** What the list shows of a record: its thumbnail and its status. Names come with the link. */
const RECORD_FIELDS = ['code', 'image', 'sg_status_list'];

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
