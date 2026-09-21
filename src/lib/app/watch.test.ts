import { describe, expect, it } from 'vitest';
import type { EventLogEntry } from 'sg-widgets-core';
import { advance, askFrom, classify, stamp, type Cursor } from './watch';

function event(id: number, eventType: string, entity: { type: string; id: number } | null, extra: Partial<EventLogEntry> = {}): EventLogEntry {
	return {
		id,
		eventType,
		attributeName: null,
		description: null,
		createdAt: `2026-09-17T10:00:${String(id % 60).padStart(2, '0')}Z`,
		entity: entity ? { ...entity, name: '' } : null,
		project: { type: 'Project', id: 1180, name: '' },
		user: { type: 'HumanUser', id: 451, name: '' },
		meta: null,
		oldValue: undefined,
		newValue: undefined,
		...extra
	};
}

describe('classify', () => {
	it('sorts note and reply events into buckets, once each, oldest first', () => {
		const changes = classify([
			event(3, 'Shotgun_Note_Change', { type: 'Note', id: 7 }),
			event(1, 'Shotgun_Note_Change', { type: 'Note', id: 7 }),
			event(2, 'Shotgun_Note_New', { type: 'Note', id: 9 }),
			event(4, 'Shotgun_Reply_New', { type: 'Reply', id: 30 }),
			event(5, 'Shotgun_Note_Change', { type: 'Note', id: 8 })
		]);
		expect(changes).toEqual({ created: [9], changed: [7, 8], retired: [], replies: [30] });
	});

	it('reads a retired note off meta, since the event has no entity, and drops it from the other buckets', () => {
		const changes = classify([
			event(1, 'Shotgun_Note_Change', { type: 'Note', id: 7 }),
			event(2, 'Shotgun_Note_Retirement', null, { meta: { type: 'entity_retirement', entity_type: 'Note', entity_id: 7 } })
		]);
		expect(changes).toEqual({ created: [], changed: [], retired: [7], replies: [] });
	});

	it('does not count a field set on create as a change', () => {
		const changes = classify([
			event(1, 'Shotgun_Note_New', { type: 'Note', id: 9 }),
			event(2, 'Shotgun_Note_Change', { type: 'Note', id: 9 })
		]);
		expect(changes).toEqual({ created: [9], changed: [], retired: [], replies: [] });
	});

	it("skips the page's own user", () => {
		const changes = classify(
			[event(1, 'Shotgun_Note_Change', { type: 'Note', id: 7 }), event(2, 'Shotgun_Note_Change', { type: 'Note', id: 8 }, { user: { type: 'HumanUser', id: 253, name: '' } })],
			451
		);
		expect(changes.changed).toEqual([8]);
	});
});

describe('cursor', () => {
	it('asks from two seconds before where it stopped', () => {
		expect(askFrom({ since: '2026-09-17T10:00:10Z', seen: new Set() })).toBe('2026-09-17T10:00:08Z');
	});

	it('moves to the newest event and answers only what was not seen', () => {
		const start: Cursor = { since: '2026-09-17T10:00:00Z', seen: new Set() };
		const first = advance(start, [event(2, 'Shotgun_Note_Change', { type: 'Note', id: 7 }), event(1, 'Shotgun_Note_Change', { type: 'Note', id: 7 })]);
		expect(first.fresh.map((e) => e.id)).toEqual([1, 2]);
		expect(first.cursor.since).toBe('2026-09-17T10:00:02Z');
		// The overlap window answers event 2 again; it is not fresh twice.
		const second = advance(first.cursor, [event(2, 'Shotgun_Note_Change', { type: 'Note', id: 7 }), event(3, 'Shotgun_Reply_New', { type: 'Reply', id: 1 })]);
		expect(second.fresh.map((e) => e.id)).toEqual([3]);
		expect(second.cursor.since).toBe('2026-09-17T10:00:03Z');
	});

	it('writes a stamp the site accepts: seconds, UTC, no millis', () => {
		expect(stamp(Date.UTC(2026, 8, 17, 10, 0, 5, 250))).toBe('2026-09-17T10:00:05Z');
	});
});
