<!--
	One note, read in full: the record it is about, the note, its annotation frames
	and attachments, the replies in order, who it is waiting on, and the two writes
	v1 makes: a reply and a status.
-->
<script lang="ts">
	import type { EntityRef, EntityRow, SgContext, StatusRecord } from '@sg-widgets/core';
	import { cellValue, condition, entityDetailUrl, formatDateTime, group, preferencesOf, toApi3Hash } from '@sg-widgets/core';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import StateLine from '$lib/components/state-line.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import EntityCard from '$lib/components/entity-card.svelte';
	import EntityChip from '$lib/components/entity-chip.svelte';
	import StatusPicker from '$lib/components/status-picker.svelte';
	import UserAvatar from '$lib/components/user-avatar.svelte';
	import { addressees, recordOf, refKey, refOf, refsOf, text, versionOf, waitingOn, type Waiting } from '$lib/notes';
	import { canCreate } from '$lib/writes';

	type Props = {
		context: SgContext;
		/** The client writes go through. */
		writer: import('@sg-widgets/core').SgClient;
		note: EntityRow;
		replies: EntityRow[];
		people: Map<number, EntityRow>;
		/** The linked records, keyed `Type:id`, so a Version's or a Task's entity is known. */
		records: Map<string, EntityRow>;
		statuses: Record<string, StatusRecord>;
		projectId: number;
		onStatus: (code: string) => Promise<void>;
		onReply: (content: string) => Promise<void>;
	};

	let { context, writer, note, replies, people, records, statuses, projectId, onStatus, onReply }: Props = $props();

	const author = $derived(refOf(note, 'created_by'));
	const record = $derived(recordOf(note, records));
	/** The Version the note was written on, when it is not the record itself. */
	const version = $derived.by(() => {
		const on = versionOf(note);
		return on && record && refKey(on) === refKey(record) ? null : on;
	});
	const waiting = $derived(waitingOn(note, replies));
	const prefs = $derived(preferencesOf(context));
	const noteUrl = $derived(entityDetailUrl(context.siteUrl, { type: 'Note', id: note.id }));

	/** Attachments carry their own `image` thumbnail; the frame is `this_file` (entity_types/Attachment). */
	const attachments = $derived.by(async () => {
		const refs = refsOf(note, 'attachments');
		if (refs.length === 0) return [] as EntityRow[];
		const result = await context.client.search('Attachment', {
			filters: toApi3Hash(group('and', [condition('id', 'in', refs.map((ref) => ref.id))])),
			fields: ['filename', 'image', 'this_file', 'created_at'],
			page: { size: 50, number: 1 }
		});
		return result.data;
	});

	let statusFailure = $state<string | null>(null);
	async function pickStatus(code: string | undefined): Promise<void> {
		if (!code || code === text(note, 'sg_status_list')) return;
		statusFailure = null;
		try {
			await onStatus(code);
		} catch (error) {
			statusFailure = error instanceof Error ? error.message : String(error);
		}
	}

	let draft = $state('');
	let sending = $state(false);
	let failure = $state<string | null>(null);
	const replyable = $derived(canCreate(writer));

	function personImage(ref: EntityRef | null): string | null {
		const value = ref ? cellValue(people.get(ref.id) ?? { type: 'HumanUser', id: 0, attributes: {}, relationships: {} }, 'image') : null;
		return typeof value === 'string' ? value : null;
	}

	function fileUrl(row: EntityRow): string | null {
		const value = row.attributes.this_file as { url?: string } | null | undefined;
		return value && typeof value.url === 'string' ? value.url : null;
	}

	function waitingLine(state: Waiting): string {
		switch (state.kind) {
			case 'closed':
				return 'Closed.';
			case 'nobody':
				return 'Addressed to nobody, so nobody will see it in an inbox.';
			case 'author':
				return `Waiting on ${state.who.name ?? 'the author'} to answer.`;
			default:
				return `Waiting on ${state.who.map((ref) => ref.name ?? '').filter(Boolean).join(', ')}.`;
		}
	}

	async function send(): Promise<void> {
		const content = draft.trim();
		if (!content || sending) return;
		sending = true;
		failure = null;
		try {
			await onReply(content);
			draft = '';
		} catch (error) {
			failure = error instanceof Error ? error.message : String(error);
		} finally {
			sending = false;
		}
	}
</script>

{#snippet person(ref: EntityRef | null, at: string)}
	<div class="flex items-center gap-2">
		<UserAvatar name={ref?.name ?? '?'} image={personImage(ref)} size="sm" />
		<span class="min-w-0 truncate text-sm font-medium">{ref?.name ?? 'Unknown'}</span>
		<span class="text-muted-foreground ml-auto shrink-0 text-xs tabular-nums" title={at}>{formatDateTime(at, prefs)}</span>
	</div>
{/snippet}

<article class="motion-safe:animate-in motion-safe:fade-in motion-safe:duration-150 flex flex-col gap-4 p-4" data-slot="thread-pane" data-note-id={note.id}>
	{#if record}
		<EntityCard {context} entity={record} variant="card" size="sm" fields={['sg_status_list', 'description']} />
	{/if}

	<header class="flex flex-col gap-2">
		<div class="flex items-center gap-2">
			<h2 class="min-w-0 flex-1 truncate text-base font-medium" title={text(note, 'subject')}>{text(note, 'subject') || 'No subject'}</h2>
			<div class="w-40 shrink-0">
				<StatusPicker {context} entityType="Note" {projectId} value={text(note, 'sg_status_list')} size="sm" onValueChange={(code) => void pickStatus(code)} />
			</div>
		</div>
		{#if statusFailure}
			<p class="text-destructive text-xs" data-slot="status-failure">{statusFailure}</p>
		{/if}
		<div class="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
			{#if version}
				<span class="flex items-center gap-1.5">on <EntityChip entity={version} variant="link" size="xs" {context} /></span>
			{/if}
			{#each refsOf(note, 'tasks') as task (task.id)}
				<EntityChip entity={task} variant="chip" size="xs" {context} />
			{/each}
			{#if text(note, 'sg_note_type')}<span>{text(note, 'sg_note_type')}</span>{/if}
			{#if cellValue(note, 'client_note') === true}<span>client-facing</span>{/if}
			{#if noteUrl}
				<a href={noteUrl} target="_blank" rel="noopener" class="hover:text-foreground ml-auto flex items-center gap-1 transition-colors duration-150">
					Open in the web app <ExternalLink aria-hidden="true" class="size-3.5" />
				</a>
			{/if}
		</div>
		{#if addressees(note).length > 0}
			<div class="text-muted-foreground flex flex-wrap items-center gap-1.5 text-xs">
				<span>To</span>
				{#each addressees(note) as ref (ref.id)}
					<span class="text-foreground">{ref.name}</span>
				{/each}
			</div>
		{/if}
	</header>

	<section class="flex flex-col gap-2" data-slot="thread-note">
		{@render person(author, text(note, 'created_at'))}
		<p class="whitespace-pre-wrap text-sm">{text(note, 'content')}</p>
		{#await attachments}
			{#if refsOf(note, 'attachments').length > 0}
				<ul class="flex flex-wrap gap-2" aria-busy="true" aria-label="Reading the attachments">
					{#each refsOf(note, 'attachments') as ref (ref.id)}
						<li><Skeleton class="h-24 w-40" /></li>
					{/each}
				</ul>
			{/if}
		{:then rows}
			{#if rows.length > 0}
				<ul class="flex flex-wrap gap-2">
					{#each rows as row (row.id)}
						{@const image = cellValue(row, 'image')}
						{@const href = fileUrl(row)}
						<li>
							<a {href} target="_blank" rel="noopener" class="border-border block overflow-hidden rounded-md border" title={text(row, 'filename')}>
								{#if typeof image === 'string'}
									<img src={image} alt={text(row, 'filename')} class="h-24 w-auto" />
								{:else}
									<span class="text-muted-foreground block px-2 py-1 text-xs">{text(row, 'filename')}</span>
								{/if}
							</a>
						</li>
					{/each}
				</ul>
			{/if}
		{:catch error}
			<StateLine state="error" pad="none" icon={CircleAlert} label={error instanceof Error ? error.message : 'The attachments could not be read.'} />
		{/await}
	</section>

	{#if replies.length > 0}
		<ol class="border-border flex flex-col gap-3 border-t pt-3" data-slot="thread-replies">
			{#each replies as reply (reply.id)}
				<li class="flex flex-col gap-1">
					{@render person(refOf(reply, 'user'), text(reply, 'created_at'))}
					<p class="whitespace-pre-wrap pl-8 text-sm">{text(reply, 'content')}</p>
				</li>
			{/each}
		</ol>
	{/if}

	<p class={waiting.kind === 'nobody' ? 'text-warning text-xs' : 'text-muted-foreground text-xs'} data-slot="thread-waiting">{waitingLine(waiting)}</p>

	<form class="flex flex-col gap-2" onsubmit={(event) => (event.preventDefault(), void send())}>
		<Textarea bind:value={draft} placeholder={replyable ? 'Reply…' : 'Replying needs the client to gain create; see docs/sg-widgets-issues.md'} disabled={!replyable || sending} rows={3} />
		<div class="flex items-center gap-2">
			<Button type="submit" size="sm" disabled={!replyable || sending || draft.trim() === ''}>{sending ? 'Sending…' : 'Reply'}</Button>
			{#if failure}<span class="text-destructive text-xs">{failure}</span>{/if}
		</div>
	</form>
</article>
