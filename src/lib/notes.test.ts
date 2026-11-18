import { describe, expect, it } from 'vitest';
import type { SearchOptions, SgClient } from 'sg-widgets-core';
import { filterableLinkTypes, linkNamePath, searchFilter } from './notes';

/** A client whose `_search` 400s on any filter that names one of `broken`. */
function clientRefusing(broken: readonly string[], asked: SearchOptions[] = []): SgClient {
	return {
		search: async (_type: string, options: SearchOptions) => {
			asked.push(options);
			const wire = JSON.stringify(options.filters);
			const bad = broken.find((type) => wire.includes(`.${type}.`));
			if (bad) throw new Error(`API read() Note.note_links.${bad}.cached_display_name doesn't exist.`);
			return { data: [], hasMore: false };
		}
	} as unknown as SgClient;
}

describe('searchFilter', () => {
	it('names each link type through cached_display_name', () => {
		const wire = JSON.stringify(searchFilter('sh010', ['Shot', 'CustomEntity09']));
		expect(wire).toContain(linkNamePath('Shot'));
		expect(wire).toContain(linkNamePath('CustomEntity09'));
		expect(linkNamePath('Shot')).toBe('note_links.Shot.cached_display_name');
	});

	it('leaves out a type it is not given', () => {
		expect(JSON.stringify(searchFilter('sh010', ['Shot']))).not.toContain('CustomEntity12');
	});
});

describe('filterableLinkTypes', () => {
	// CustomEntity12 and 13 on the operator's site: enabled, in valid_types, the field in their
	// schema, and still every dotted path through them 400s (probed 2026-11-17, issue #6).
	it('keeps the types whose path answers, in their order', async () => {
		const types = ['Asset', 'CustomEntity12', 'Shot', 'CustomEntity13'];
		expect(await filterableLinkTypes(clientRefusing(['CustomEntity12', 'CustomEntity13']), types)).toEqual(['Asset', 'Shot']);
	});

	it('asks one row per type, through the same path the search uses', async () => {
		const asked: SearchOptions[] = [];
		await filterableLinkTypes(clientRefusing([], asked), ['Shot']);
		expect(asked).toHaveLength(1);
		expect(asked[0]!.page?.size).toBe(1);
		expect(JSON.stringify(asked[0]!.filters)).toContain(linkNamePath('Shot'));
	});
});
