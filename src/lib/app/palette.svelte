<!--
	The command palette: what can be done to the ticked notes, or to the one open
	when nothing is ticked. ⌘K opens it. A status is picked in the list itself; a
	reply needs words, so it opens a small dialog of its own; a bulk write shows its
	progress and what failed in a third, which stays until it is read.
-->
<script lang="ts">
	import type { EntityRef, EntityRow, SgContext, StatusRecord } from '@sg-widgets/core';
	import CheckIcon from '@lucide/svelte/icons/check';
	import ChevronsDownUp from '@lucide/svelte/icons/chevrons-down-up';
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Eye from '@lucide/svelte/icons/eye';
	import EyeOff from '@lucide/svelte/icons/eye-off';
	import Layers from '@lucide/svelte/icons/layers';
	import ListChecks from '@lucide/svelte/icons/list-checks';
	import Forward from '@lucide/svelte/icons/forward';
	import Keyboard from '@lucide/svelte/icons/keyboard';
	import MessageSquareReply from '@lucide/svelte/icons/message-square-reply';
	import Search from '@lucide/svelte/icons/search';
	import SquareX from '@lucide/svelte/icons/square-x';
	import Tag from '@lucide/svelte/icons/tag';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Kbd } from '$lib/components/ui/kbd/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import StatusBadge from '$lib/components/status-badge.svelte';
	import UserMultiPicker from '$lib/components/user-multi-picker.svelte';
	import { CLOSED, GROUP_OPTIONS, text, type GroupBy } from '$lib/notes';

	/** A bulk write as it runs and as it ended. */
	export interface Job {
		label: string;
		done: number;
		total: number;
		failures: string[];
	}

	type Props = {
		open?: boolean;
		context: SgContext;
		projectId: number;
		/** The Forward dialog, two-way, so a key can open it. */
		forwardOpen?: boolean;
		/** The notes an action applies to. */
		targets: EntityRow[];
		/** True when more than one note is selected. */
		several: boolean;
		statuses: Record<string, StatusRecord>;
		/** The codes a Note may take on this project, in the schema's order. */
		noteStatuses: string[];
		groupBy: GroupBy;
		job: Job | null;
		onStatus: (notes: EntityRow[], code: string) => void;
		onRead: (notes: EntityRow[], read: boolean) => void;
		onReply: (notes: EntityRow[], content: string, close: boolean) => void;
		onForward: (notes: EntityRow[], to: EntityRef[], message: string) => void;
		onFocusReply: () => void;
		onFocusSearch: () => void;
		onGroupBy: (value: GroupBy) => void;
		onSelectAll: () => void;
		onClearSelection: () => void;
		onCollapseAll: () => void;
		onExpandAll: () => void;
		onOpen: (notes: EntityRow[]) => void;
		onJobRead: () => void;
	};

	let {
		open = $bindable(false),
		context,
		projectId,
		forwardOpen = $bindable(false),
		targets,
		several,
		statuses,
		noteStatuses,
		groupBy,
		job,
		onStatus,
		onRead,
		onReply,
		onForward,
		onFocusReply,
		onFocusSearch,
		onGroupBy,
		onSelectAll,
		onClearSelection,
		onCollapseAll,
		onExpandAll,
		onOpen,
		onJobRead
	}: Props = $props();

	type Page = 'actions' | 'status' | 'group';
	let page = $state<Page>('actions');
	let search = $state('');
	let replyOpen = $state(false);
	let draft = $state('');
	let closeToo = $state(false);
	let forwardTo = $state<EntityRef[]>([]);
	let forwardMessage = $state('');

	const count = $derived(targets.length);
	const noun = $derived(count === 1 ? 'note' : 'notes');
	const what = $derived(count === 0 ? 'No note selected' : several ? `${count} selected ${noun}` : 'The selected note');

	$effect(() => {
		if (open) {
			page = 'actions';
			search = '';
		}
	});

	function run(action: () => void): void {
		open = false;
		action();
	}

	function sendReply(): void {
		const content = draft.trim();
		if (!content) return;
		replyOpen = false;
		onReply(targets, content, closeToo);
		draft = '';
		closeToo = false;
	}

	function sendForward(): void {
		if (forwardTo.length === 0) return;
		forwardOpen = false;
		onForward(targets, forwardTo, forwardMessage);
		forwardTo = [];
		forwardMessage = '';
	}

	/** What one note is called in a list of targets. */
	function title(note: EntityRow): string {
		return text(note, 'subject') || text(note, 'content').split('\n')[0] || `Note ${note.id}`;
	}
</script>

<Command.Dialog bind:open bind:value={search} title="Actions" description="What to do with the notes" class="max-w-md" data-slot="palette">
	<Command.Input placeholder={page === 'status' ? 'Which status…' : page === 'group' ? 'Group by…' : 'What to do…'} />
	<Command.List>
		<Command.Empty>Nothing matches.</Command.Empty>
		{#if page === 'actions'}
			{#if count === 0}
				<Command.Group heading="No note selected">
					<Command.Item value="how" disabled>Select a note in the list, or several, and these act on them.</Command.Item>
				</Command.Group>
			{:else}
				<Command.Group heading={what}>
					<Command.Item value="reply" onSelect={() => run(() => ((closeToo = false), (replyOpen = true)))}>
						<MessageSquareReply aria-hidden="true" /> Reply to {count} {noun}… <Command.Shortcut>R</Command.Shortcut>
					</Command.Item>
					<Command.Item value="reply and close" onSelect={() => run(() => ((closeToo = true), (replyOpen = true)))}>
						<CircleCheck aria-hidden="true" /> Reply to {count} {noun} and close…
					</Command.Item>
					<Command.Item value="close" onSelect={() => run(() => onStatus(targets, CLOSED))}>
						<CircleCheck aria-hidden="true" /> Close {count} {noun} <Command.Shortcut>E</Command.Shortcut>
					</Command.Item>
					<Command.Item value="set status" onSelect={() => (page = 'status')}>
						<Tag aria-hidden="true" /> Set the status of {count} {noun}…
					</Command.Item>
					<Command.Item value="forward" onSelect={() => run(() => (forwardOpen = true))}>
						<Forward aria-hidden="true" /> Forward {count} {noun} to…<span class="text-muted-foreground ml-1 text-xs">a copy, with new addressees</span> <Command.Shortcut>F</Command.Shortcut>
					</Command.Item>
					<Command.Item value="mark read" onSelect={() => run(() => onRead(targets, true))}>
						<Eye aria-hidden="true" /> Mark {count} {noun} read <Command.Shortcut>U</Command.Shortcut>
					</Command.Item>
					<Command.Item value="mark unread" onSelect={() => run(() => onRead(targets, false))}>
						<EyeOff aria-hidden="true" /> Mark {count} {noun} unread
					</Command.Item>
					<Command.Item value="open web" onSelect={() => run(() => onOpen(targets))}>
						<ExternalLink aria-hidden="true" /> Open {count} {noun} in the web app
					</Command.Item>
				</Command.Group>
			{/if}
			<Command.Group heading="Selection">
				<Command.Item value="select all" onSelect={() => run(onSelectAll)}><ListChecks aria-hidden="true" /> Select every loaded note <Command.Shortcut>⌘A</Command.Shortcut></Command.Item>
				<Command.Item value="clear selection" disabled={count === 0} onSelect={() => run(onClearSelection)}><SquareX aria-hidden="true" /> Clear the selection <Command.Shortcut>Esc</Command.Shortcut></Command.Item>
			</Command.Group>
			<Command.Group heading="List">
				<Command.Item value="search" onSelect={() => run(onFocusSearch)}><Search aria-hidden="true" /> Search <Command.Shortcut>/</Command.Shortcut></Command.Item>
				<Command.Item value="group by" onSelect={() => (page = 'group')}><Layers aria-hidden="true" /> Group by…</Command.Item>
				<Command.Item value="collapse all" onSelect={() => run(onCollapseAll)}><ChevronsDownUp aria-hidden="true" /> Collapse all</Command.Item>
				<Command.Item value="expand all" onSelect={() => run(onExpandAll)}><ChevronsUpDown aria-hidden="true" /> Expand all</Command.Item>
			</Command.Group>
			<Command.Group heading="Keys">
				<Command.Item value="keys" disabled>
					<Keyboard aria-hidden="true" />
					<span class="flex flex-wrap gap-x-3 gap-y-1 text-xs">
						<span><Kbd>↑</Kbd><Kbd>↓</Kbd> move</span><span><Kbd>⇧↑</Kbd><Kbd>⇧↓</Kbd> extend</span><span><Kbd>X</Kbd> select</span>
						<span><Kbd>R</Kbd> reply</span><span><Kbd>E</Kbd> close</span><span><Kbd>U</Kbd> read</span><span><Kbd>F</Kbd> forward</span><span><Kbd>/</Kbd> search</span><span><Kbd>Esc</Kbd> back out</span>
					</span>
				</Command.Item>
			</Command.Group>
		{:else if page === 'status'}
			<Command.Group heading="Set {count} {noun} to">
				{#each noteStatuses as code (code)}
					<Command.Item value={statuses[code]?.name ?? code} onSelect={() => run(() => onStatus(targets, code))}>
						<StatusBadge {code} status={statuses[code] ?? null} variant="icon" size="xs" />
						{statuses[code]?.name ?? code}
					</Command.Item>
				{/each}
			</Command.Group>
		{:else}
			<Command.Group heading="Group by">
				{#each GROUP_OPTIONS as option (option.value)}
					<Command.Item value={option.label} onSelect={() => run(() => onGroupBy(option.value))}>
						{option.label}
						{#if option.value === groupBy}<CheckIcon aria-hidden="true" class="ml-auto" />{/if}
					</Command.Item>
				{/each}
			</Command.Group>
		{/if}
	</Command.List>
</Command.Dialog>

<Dialog.Root bind:open={replyOpen}>
	<Dialog.Content class="max-w-md" data-slot="reply-dialog">
		<Dialog.Header>
			<Dialog.Title>Reply to {count} {noun}{closeToo ? ' and close' : ''}</Dialog.Title>
			<Dialog.Description>
				{count === 1 ? 'One reply, written as you.' : 'The same reply, written on each of them as you.'} A reply cannot be taken back.
			</Dialog.Description>
		</Dialog.Header>
		{#if count > 1}
			<ul class="text-muted-foreground flex max-h-32 flex-col gap-0.5 overflow-auto text-xs" data-slot="reply-targets">
				{#each targets.slice(0, 8) as note (note.id)}
					<li class="truncate" title={title(note)}>{title(note)}</li>
				{/each}
				{#if count > 8}<li>and {count - 8} more</li>{/if}
			</ul>
		{/if}
		<form class="flex flex-col gap-3" onsubmit={(event) => (event.preventDefault(), sendReply())}>
			<Textarea bind:value={draft} rows={4} placeholder="Reply…" onkeydown={(event) => event.key === 'Enter' && (event.metaKey || event.ctrlKey) && sendReply()} />
			<label class="flex items-center gap-2 text-sm">
				<Checkbox bind:checked={closeToo} /> Close {count === 1 ? 'it' : 'them'} after replying
			</label>
			<Dialog.Footer>
				<Button type="button" variant="ghost" size="sm" onclick={() => (replyOpen = false)}>Cancel</Button>
				<Button type="submit" size="sm" disabled={draft.trim() === ''}>{closeToo ? 'Reply and close' : 'Reply'} <Kbd>⌘↵</Kbd></Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>

<Dialog.Root bind:open={forwardOpen}>
	<Dialog.Content class="max-w-md" data-slot="forward-dialog">
		<Dialog.Header>
			<Dialog.Title>Forward {count} {noun}</Dialog.Title>
			<Dialog.Description>
				A copy of each, with the same links and the original text quoted, addressed to the people you pick. The original stays as it is.
			</Dialog.Description>
		</Dialog.Header>
		{#if count > 1}
			<ul class="text-muted-foreground flex max-h-32 flex-col gap-0.5 overflow-auto text-xs">
				{#each targets.slice(0, 8) as note (note.id)}
					<li class="truncate" title={title(note)}>{title(note)}</li>
				{/each}
				{#if count > 8}<li>and {count - 8} more</li>{/if}
			</ul>
		{/if}
		<form class="flex flex-col gap-3" onsubmit={(event) => (event.preventDefault(), sendForward())}>
			<UserMultiPicker {context} {projectId} bind:value={forwardTo} placeholder="To…" includeApiUsers={false} />
			<Textarea bind:value={forwardMessage} rows={3} placeholder="A word for them, above the original…" />
			<Dialog.Footer>
				<Button type="button" variant="ghost" size="sm" onclick={() => (forwardOpen = false)}>Cancel</Button>
				<Button type="submit" size="sm" disabled={forwardTo.length === 0}>Forward</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>

<Dialog.Root open={job !== null} onOpenChange={(next) => !next && job && job.done === job.total && onJobRead()}>
	<Dialog.Content class="max-w-md" data-slot="job-dialog" showCloseButton={job !== null && job.done === job.total}>
		{#if job}
			<Dialog.Header>
				<Dialog.Title>{job.label}</Dialog.Title>
				<Dialog.Description>
					{#if job.done < job.total}
						{job.done} of {job.total} done…
					{:else if job.failures.length === 0}
						All {job.total} done.
					{:else}
						{job.total - job.failures.length} of {job.total} done, {job.failures.length} failed.
					{/if}
				</Dialog.Description>
			</Dialog.Header>
			<div class="bg-muted h-1 w-full overflow-hidden rounded-full" role="progressbar" aria-valuemin="0" aria-valuemax={job.total} aria-valuenow={job.done}>
				<div class="bg-primary h-full origin-left transition-transform duration-150 ease-out motion-reduce:transition-none" style="transform:scaleX({job.total ? job.done / job.total : 1})"></div>
			</div>
			{#if job.failures.length > 0}
				<ul class="text-destructive flex flex-col gap-1 text-xs">
					{#each job.failures as failure (failure)}<li>{failure}</li>{/each}
				</ul>
			{/if}
			{#if job.done === job.total}
				<Dialog.Footer><Button size="sm" onclick={onJobRead}>Done</Button></Dialog.Footer>
			{/if}
		{/if}
	</Dialog.Content>
</Dialog.Root>
