<!--
	One note, read in full: the record it is about, then the thread as the site
	orders it (Note, Attachments and Replies in time order, through
	`threadContents`), who it is waiting on, and the two writes v1 makes: a reply
	and a status.

	States. The thread stands behind skeletons while it is read; a failed read is a
	line with a retry; a failed write says so beside the control that made it.
-->
<script lang="ts">
	import type { EntityRef, EntityRow, SgClient, SgContext, StatusRecord, ThreadRow } from '@sg-widgets/core';
	import { cellValue, entityDetailUrl, formatDateTime, preferencesOf } from '@sg-widgets/core';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import EntityCard from '$lib/components/entity-card.svelte';
	import EntityChip from '$lib/components/entity-chip.svelte';
	import StateLine from '$lib/components/state-line.svelte';
	import StatusPicker from '$lib/components/status-picker.svelte';
	import UserAvatar from '$lib/components/user-avatar.svelte';
	import { addressees, isClientFacing, recordOf, refKey, refsOf, text, versionOf, waitingOn, type Waiting } from '$lib/notes';
	import { canCreate } from '$lib/writes';

	type Props = {
		context: SgContext;
		/** The client writes go through. */
		writer: SgClient;
		note: EntityRow;
		/** The replies the list knows, for the waiting-on rule. */
		replies: EntityRow[];
		/** The linked records, keyed `Type:id`, so a Version's or a Task's entity is known. */
		records: Map<string, EntityRow>;
		statuses: Record<string, StatusRecord>;
		projectId: number;
		onStatus: (code: string) => Promise<void>;
		onReply: (content: string) => Promise<void>;
	};

	let { context, writer, note, replies, records, statuses, projectId, onStatus, onReply }: Props = $props();

	const record = $derived(recordOf(note, records));
	/** The Version the note was written on, when it is not the record itself. */
	const version = $derived.by(() => {
		const on = versionOf(note);
		return on && record && refKey(on) === refKey(record) ? null : on;
	});
	const waiting = $derived(waitingOn(note, replies));
	const prefs = $derived(preferencesOf(context));
	const noteUrl = $derived(entityDetailUrl(context.siteUrl, { type: 'Note', id: note.id }));

	/** Bumped after a write, so the thread is read again. */
	let revision = $state(0);
	/** An Attachment's thumbnail is `image`; the frame itself is `this_file` (entity_types/Attachment). */
	const thread = $derived.by(() => {
		void revision;
		return context.client.threadContents(note.id, { Attachment: ['filename', 'image', 'this_file'] });
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

	async function send(): Promise<void> {
		const content = draft.trim();
		if (!content || sending) return;
		sending = true;
		failure = null;
		try {
			await onReply(content);
			draft = '';
			revision += 1;
		} catch (error) {
			failure = error instanceof Error ? error.message : String(error);
		} finally {
			sending = false;
		}
	}

	function field(row: ThreadRow, name: string): string {
		const value = row.fields[name];
		return typeof value === 'string' ? value : '';
	}

	function fileUrl(row: ThreadRow): string | null {
		const value = row.fields.this_file as { url?: string } | null | undefined;
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
</script>

{#snippet person(author: ThreadRow['author'], at: string | null)}
	<div class="flex items-center gap-2">
		<UserAvatar name={author?.name ?? '?'} image={author?.image ?? null} size="sm" />
		<span class="min-w-0 truncate text-sm font-medium">{author?.name ?? 'Unknown'}</span>
		{#if at}
			<span class="text-muted-foreground ml-auto shrink-0 font-mono text-xs tabular-nums" title={at}>{formatDateTime(at, prefs)}</span>
		{/if}
	</div>
{/snippet}

<article class="motion-safe:animate-in motion-safe:fade-in motion-safe:duration-150 flex flex-col gap-4 p-4" data-slot="thread-pane" data-note-id={note.id}>
	{#if record}
		<EntityCard {context} entity={record} variant="card" size="sm" fields={['sg_status_list', 'description']} />
	{/if}

	<header class="flex flex-col gap-2">
		<div class="flex items-center gap-2">
			<h2 class="min-w-0 flex-1 truncate text-lg font-semibold tracking-tight" title={text(note, 'subject')}>{text(note, 'subject') || 'No subject'}</h2>
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
			{#if isClientFacing(note)}<span>client-facing</span>{/if}
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

	{#await thread}
		<div class="flex flex-col gap-3" aria-busy="true" aria-label="Reading the thread">
			<div class="flex items-center gap-2"><Skeleton class="size-6 rounded-full" /><Skeleton class="h-4 w-32" /></div>
			<Skeleton class="h-4 w-full" />
			<Skeleton class="h-4 w-4/5" />
		</div>
	{:then rows}
		<ol class="flex flex-col gap-3" data-slot="thread-rows">
			{#each rows as row (`${row.type}:${row.id}`)}
				<li class="flex flex-col gap-1" data-thread-type={row.type}>
					{#if row.type === 'Attachment'}
						{@const image = field(row, 'image')}
						{@const href = fileUrl(row)}
						<a {href} target="_blank" rel="noopener" class="border-border block w-fit overflow-hidden rounded-md border" title={field(row, 'filename')}>
							{#if image}
								<img src={image} alt={field(row, 'filename')} class="h-24 w-auto" />
							{:else}
								<span class="text-muted-foreground block px-2 py-1 text-xs">{field(row, 'filename')}</span>
							{/if}
						</a>
					{:else}
						{@render person(row.author, row.createdAt)}
						<p class={row.type === 'Reply' ? 'whitespace-pre-wrap pl-8 text-sm' : 'whitespace-pre-wrap text-sm'}>{row.content ?? ''}</p>
					{/if}
				</li>
			{/each}
		</ol>
	{:catch error}
		<StateLine state="error" pad="none" icon={CircleAlert} label={error instanceof Error ? error.message : 'The thread could not be read.'}>
			<Button size="sm" variant="outline" onclick={() => (revision += 1)}>Try again</Button>
		</StateLine>
	{/await}

	<p class="text-muted-foreground text-xs" data-slot="thread-waiting">{waitingLine(waiting)}</p>

	<form class="flex flex-col gap-2" onsubmit={(event) => (event.preventDefault(), void send())}>
		<Textarea bind:value={draft} placeholder={replyable ? 'Reply…' : 'This client cannot create a Reply.'} disabled={!replyable || sending} rows={3} />
		<div class="flex items-center gap-2">
			<Button type="submit" size="sm" disabled={!replyable || sending || draft.trim() === ''}>{sending ? 'Sending…' : 'Reply'}</Button>
			{#if failure}<span class="text-destructive text-xs">{failure}</span>{/if}
		</div>
	</form>
</article>
