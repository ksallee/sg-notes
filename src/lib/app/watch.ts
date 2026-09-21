/**
 * What changed on the site since the page last looked, from the event log.
 *
 * The event log is the one place a change made elsewhere shows up promptly: an entry lands
 * 0.3 to 0.4 s after the write, a web-app write always logs, and a script's logs while its
 * ApiUser has `generate_event_log_entries` on (corpus findings 025, 049). The activity
 * stream is not used: status changes made over the API were absent from every stream
 * twenty minutes later (findings 066, 067).
 *
 * The watcher reads the project's Note and Reply events newer than a cursor, on a timer
 * while the tab is visible and at once when it comes back, and hands the page what to do:
 * which loaded notes to read again, which threads to re-read, and which new notes exist.
 * It never writes and never touches the page itself.
 */
import type { EntityRef, EventLogEntry, SgClient } from 'sg-widgets-core';

/** The event types that can change what the page shows. */
export const NOTE_EVENTS = [
	'Shotgun_Note_New',
	'Shotgun_Note_Change',
	'Shotgun_Note_Retirement',
	'Shotgun_Reply_New',
	'Shotgun_Reply_Change',
	'Shotgun_Reply_Retirement'
] as const;

export interface Changes {
	/** Notes created, by id. Whether one matches the page's filter is for the page to ask. */
	created: number[];
	/** Notes whose own fields changed, by id. */
	changed: number[];
	/** Notes retired, by id. `entity` is null on those events; the id comes from `meta`. */
	retired: number[];
	/** Replies created, changed or retired, by id. The note they belong to is not in the event. */
	replies: number[];
}

/** The row an event is about: `entity`, or `meta.entity_id` once the row is gone (finding 025). */
function subject(event: EventLogEntry): { type: string; id: number } | null {
	if (event.entity) return { type: event.entity.type, id: event.entity.id };
	const meta = event.meta;
	const type = meta?.['entity_type'];
	const id = meta?.['entity_id'];
	return typeof type === 'string' && typeof id === 'number' ? { type, id } : null;
}

/**
 * Sort events into what the page has to do. Events by `skipUser` are left out: the page
 * already re-read what it wrote itself. Each id appears once per bucket, oldest first.
 */
export function classify(events: readonly EventLogEntry[], skipUser: number | null = null): Changes {
	const created = new Set<number>();
	const changed = new Set<number>();
	const retired = new Set<number>();
	const replies = new Set<number>();
	for (const event of [...events].sort((a, b) => a.id - b.id)) {
		if (skipUser !== null && event.user?.id === skipUser) continue;
		const about = subject(event);
		if (!about) continue;
		switch (event.eventType) {
			case 'Shotgun_Note_New':
				created.add(about.id);
				break;
			case 'Shotgun_Note_Change':
				if (!created.has(about.id)) changed.add(about.id);
				break;
			case 'Shotgun_Note_Retirement':
				retired.add(about.id);
				changed.delete(about.id);
				created.delete(about.id);
				break;
			case 'Shotgun_Reply_New':
			case 'Shotgun_Reply_Change':
			case 'Shotgun_Reply_Retirement':
				replies.add(about.id);
				break;
		}
	}
	return { created: [...created], changed: [...changed], retired: [...retired], replies: [...replies] };
}

export function isEmpty(changes: Changes): boolean {
	return changes.created.length + changes.changed.length + changes.retired.length + changes.replies.length === 0;
}

/**
 * Where the last read stopped. `since` is the newest `created_at` seen, and the next read
 * asks from two seconds before it, since `greater_than` on a whole second would drop an
 * event that shares the second (finding 025); `seen` keeps those from counting twice.
 */
export interface Cursor {
	since: string;
	seen: ReadonlySet<number>;
}

/** The site's own `created_at` shape: seconds, UTC, no millis. */
export function stamp(ms: number): string {
	return new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z');
}

const OVERLAP_MS = 2000;

/** The cursor to ask with: two seconds before the last read stopped. */
export function askFrom(cursor: Cursor): string {
	return stamp(Date.parse(cursor.since) - OVERLAP_MS);
}

/** The cursor after these events, and the events not seen before, oldest first. */
export function advance(cursor: Cursor, events: readonly EventLogEntry[]): { cursor: Cursor; fresh: EventLogEntry[] } {
	const fresh = events.filter((event) => !cursor.seen.has(event.id)).sort((a, b) => a.id - b.id);
	let since = cursor.since;
	for (const event of fresh) if (event.createdAt && event.createdAt > since) since = event.createdAt;
	// Ids inside the overlap window are the only ones a later read can answer again.
	const floor = Date.parse(since) - OVERLAP_MS;
	const seen = new Set<number>();
	for (const event of events) if (event.createdAt && Date.parse(event.createdAt) >= floor) seen.add(event.id);
	for (const id of cursor.seen) seen.add(id);
	return { cursor: { since, seen }, fresh };
}

/** Every project event newer than the cursor, across pages, newest page first. Bounded so a flood cannot spin. */
export async function readSince(client: SgClient, projectId: number, cursor: Cursor, pageSize = 200, maxPages = 5): Promise<EventLogEntry[]> {
	const out: EventLogEntry[] = [];
	for (let number = 1; number <= maxPages; number++) {
		const page = await client.eventLog({ projectId, eventType: [...NOTE_EVENTS], since: askFrom(cursor), page: { size: pageSize, number } });
		out.push(...page.data);
		if (!page.hasMore) break;
	}
	return out;
}

/** The notes these replies belong to, by reply id, since a Reply event names only the reply. */
export async function notesOfReplies(client: SgClient, replyIds: readonly number[]): Promise<number[]> {
	if (replyIds.length === 0) return [];
	const res = await client.search('Reply', {
		filters: { logical_operator: 'and', conditions: [['id', 'in', [...replyIds]]] },
		fields: ['entity'],
		page: { size: replyIds.length, number: 1 }
	});
	const notes = new Set<number>();
	for (const row of res.data) {
		const ref = row.relationships['entity']?.data as EntityRef | null | undefined;
		if (ref && !Array.isArray(ref) && ref.type === 'Note') notes.add(ref.id);
	}
	return [...notes];
}

export interface WatchOptions {
	client: SgClient;
	projectId: number;
	/** Events by this HumanUser are the page's own writes and are skipped. */
	skipUser?: number | null;
	/** How long between looks while the tab is visible. */
	intervalMs?: number;
	/** How far back the first look reaches, so a change made while the page loaded is not missed. */
	backfillMs?: number;
	onChanges: (changes: Changes) => void | Promise<void>;
	onError?: (error: unknown) => void;
}

/**
 * Look at the event log on a timer while the tab is visible, and at once when it becomes
 * visible again or the window regains focus. Returns the stop function.
 */
export function watch(options: WatchOptions): () => void {
	const interval = options.intervalMs ?? 20_000;
	let cursor: Cursor = { since: stamp(Date.now() - (options.backfillMs ?? 60_000)), seen: new Set() };
	let timer: ReturnType<typeof setTimeout> | null = null;
	let running = false;
	let stopped = false;

	const visible = (): boolean => typeof document === 'undefined' || document.visibilityState === 'visible';

	async function tick(): Promise<void> {
		if (stopped || running) return;
		running = true;
		try {
			const events = await readSince(options.client, options.projectId, cursor);
			const step = advance(cursor, events);
			cursor = step.cursor;
			const changes = classify(step.fresh, options.skipUser ?? null);
			if (!isEmpty(changes)) await options.onChanges(changes);
		} catch (error) {
			options.onError?.(error);
		} finally {
			running = false;
			schedule();
		}
	}

	function schedule(): void {
		if (timer) clearTimeout(timer);
		timer = null;
		if (stopped || !visible()) return;
		timer = setTimeout(() => void tick(), interval);
	}

	function wake(): void {
		if (visible()) void tick();
		else schedule();
	}

	if (typeof document !== 'undefined') {
		document.addEventListener('visibilitychange', wake);
		window.addEventListener('focus', wake);
	}
	void tick();

	return () => {
		stopped = true;
		if (timer) clearTimeout(timer);
		if (typeof document !== 'undefined') {
			document.removeEventListener('visibilitychange', wake);
			window.removeEventListener('focus', wake);
		}
	};
}
