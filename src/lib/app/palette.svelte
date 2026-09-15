<!--
	The command palette: what can be done to the ticked notes, or to the one open
	when nothing is ticked. ⌘K opens it. A status is picked in the list itself; a
	reply needs words, so it opens a small dialog of its own; a bulk write shows its
	progress and what failed in a third, which stays until it is read.
-->
<script lang="ts">
	import type { EntityRow, StatusRecord } from '@sg-widgets/core';
	import CheckIcon from '@lucide/svelte/icons/check';
	import ChevronsDownUp from '@lucide/svelte/icons/chevrons-down-up';
	import ChevronsUpDown from '@lucide/svelte/icons/chevrons-up-down';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Eye from '@lucide/svelte/icons/eye';
	import EyeOff from '@lucide/svelte/icons/eye-off';
	import Layers from '@lucide/svelte/icons/layers';
	import ListChecks from '@lucide/svelte/icons/list-checks';
	import MessageSquareReply from '@lucide/svelte/icons/message-square-reply';
	import SquareX from '@lucide/svelte/icons/square-x';
	import Tag from '@lucide/svelte/icons/tag';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Command from '$lib/components/ui/command/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import StatusBadge from '$lib/components/status-badge.svelte';
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
		/** The notes an action applies to. */
		targets: EntityRow[];
		/** True when the targets are ticked rows rather than the open note. */
		ticked: boolean;
		statuses: Record<string, StatusRecord>;
		/** The codes a Note may take on this project, in the schema's order. */
		noteStatuses: string[];
		groupBy: GroupBy;
		job: Job | null;
		onStatus: (notes: EntityRow[], code: string) => void;
		onRead: (notes: EntityRow[], read: boolean) => void;
		onReply: (notes: EntityRow[], content: string) => void;
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
		targets,
		ticked,
		statuses,
		noteStatuses,
		groupBy,
		job,
		onStatus,
		onRead,
		onReply,
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

	const count = $derived(targets.length);
	const noun = $derived(count === 1 ? 'note' : 'notes');
	const what = $derived(count === 0 ? 'No note' : ticked ? `${count} ticked ${noun}` : `The open note`);

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
		onReply(targets, content);
		draft = '';
	}
</script>

<Command.Dialog bind:open bind:value={search} title="Actions" description="What to do with the notes" class="max-w-md" data-slot="palette">
	<Command.Input placeholder={page === 'status' ? 'Which status…' : page === 'group' ? 'Group by…' : 'What to do…'} />
	<Command.List>
		<Command.Empty>Nothing matches.</Command.Empty>
		{#if page === 'actions'}
			<Command.Group heading={what}>
				<Command.Item value="reply" disabled={count === 0} onSelect={() => run(() => (replyOpen = true))}>
					<MessageSquareReply aria-hidden="true" /> Reply to {count} {noun}…
				</Command.Item>
				<Command.Item value="set status" disabled={count === 0} onSelect={() => (page = 'status')}>
					<Tag aria-hidden="true" /> Set the status of {count} {noun}…
				</Command.Item>
				<Command.Item value="close" disabled={count === 0} onSelect={() => run(() => onStatus(targets, CLOSED))}>
					<CircleCheck aria-hidden="true" /> Close {count} {noun}
				</Command.Item>
				<Command.Item value="mark read" disabled={count === 0} onSelect={() => run(() => onRead(targets, true))}>
					<Eye aria-hidden="true" /> Mark {count} {noun} read
				</Command.Item>
				<Command.Item value="mark unread" disabled={count === 0} onSelect={() => run(() => onRead(targets, false))}>
					<EyeOff aria-hidden="true" /> Mark {count} {noun} unread
				</Command.Item>
				<Command.Item value="open web" disabled={count === 0} onSelect={() => run(() => onOpen(targets))}>
					<ExternalLink aria-hidden="true" /> Open {count} {noun} in the web app
				</Command.Item>
			</Command.Group>
			<Command.Group heading="Selection">
				<Command.Item value="select all" onSelect={() => run(onSelectAll)}><ListChecks aria-hidden="true" /> Tick every loaded note</Command.Item>
				<Command.Item value="clear selection" disabled={!ticked} onSelect={() => run(onClearSelection)}><SquareX aria-hidden="true" /> Untick everything</Command.Item>
			</Command.Group>
			<Command.Group heading="List">
				<Command.Item value="group by" onSelect={() => (page = 'group')}><Layers aria-hidden="true" /> Group by…</Command.Item>
				<Command.Item value="collapse all" onSelect={() => run(onCollapseAll)}><ChevronsDownUp aria-hidden="true" /> Collapse all</Command.Item>
				<Command.Item value="expand all" onSelect={() => run(onExpandAll)}><ChevronsUpDown aria-hidden="true" /> Expand all</Command.Item>
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
			<Dialog.Title>Reply to {count} {noun}</Dialog.Title>
			<Dialog.Description>One reply, written on each of them as you.</Dialog.Description>
		</Dialog.Header>
		<form class="flex flex-col gap-3" onsubmit={(event) => (event.preventDefault(), sendReply())}>
			<Textarea bind:value={draft} rows={4} placeholder="Reply…" onkeydown={(event) => event.key === 'Enter' && (event.metaKey || event.ctrlKey) && sendReply()} />
			<Dialog.Footer>
				<Button type="button" variant="ghost" size="sm" onclick={() => (replyOpen = false)}>Cancel</Button>
				<Button type="submit" size="sm" disabled={draft.trim() === ''}>Reply</Button>
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
				<div class="bg-primary h-full transition-[width] duration-150 ease-out motion-reduce:transition-none" style="width:{job.total ? (100 * job.done) / job.total : 100}%"></div>
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
