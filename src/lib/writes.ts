/**
 * What the page writes, and through what.
 *
 * `create` came to `SgClient` with sg-widgets #193. The check stays so a build
 * against an older core offers the reply disabled rather than failing on send.
 */
import type { EntityRef, EntityRow, SgClient } from 'sg-widgets-core';

export function canCreate(client: SgClient): boolean {
	return typeof client.create === 'function';
}

/** A Reply created without `entity` cannot be deleted (entity_types/Reply), so it goes in the one call. */
export function createReply(client: SgClient, note: EntityRef, content: string): Promise<EntityRow> {
	if (!canCreate(client)) return Promise.reject(new Error('This client cannot create a Reply.'));
	return client.create('Reply', { entity: { type: 'Note', id: note.id }, content });
}
