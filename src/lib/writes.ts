/**
 * What the page writes, and through what.
 *
 * `SgClient` has `update` and no `create` today; the create lands with the
 * sg-widgets client issues (docs/sg-widgets-issues.md, item 1). Until it does,
 * a reply is offered disabled rather than through a private extension.
 */
import type { EntityRef, EntityRow, SgClient } from '@sg-widgets/core';

type Creating = SgClient & { create(entityType: string, body: Record<string, unknown>): Promise<EntityRow> };

export function canCreate(client: SgClient): client is Creating {
	return typeof (client as Partial<Creating>).create === 'function';
}

/** A Reply created without `entity` cannot be deleted (entity_types/Reply), so it goes in the one call. */
export function createReply(client: SgClient, note: EntityRef, content: string): Promise<EntityRow> {
	if (!canCreate(client)) return Promise.reject(new Error('This client cannot create a Reply yet.'));
	return client.create('Reply', { entity: { type: 'Note', id: note.id }, content });
}
