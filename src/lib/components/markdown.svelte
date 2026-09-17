<script lang="ts" module>
	import { Lexer, type Token, type Tokens } from 'marked';

	/**
	 * A note's body, as the site renders it. Notes and replies take GitHub Flavored Markdown
	 * (Autodesk, "Formatting text fields with ShotGrid Markdown"), and a newline is a line
	 * break there as it is in the web app, so `breaks` is on.
	 */
	const OPTIONS = { gfm: true, breaks: true };

	/** A fresh lexer per body: a Lexer keeps every token it has made and hands the pile back to the next call. */
	export function parse(source: string): Token[] {
		return new Lexer(OPTIONS).lex(source);
	}

	/** The schemes a link may open. Anything else renders as its text. */
	const SCHEMES = new Set(['http:', 'https:', 'mailto:']);

	export function safeHref(href: string): string | null {
		try {
			const url = new URL(href);
			return SCHEMES.has(url.protocol) ? url.href : null;
		} catch {
			return null;
		}
	}

	/** The words, with the markup taken off, for a one-line preview. */
	export function plain(source: string): string {
		const out: string[] = [];
		const walk = (tokens: Token[]): void => {
			for (const token of tokens) {
				const t = token as Tokens.Generic;
				if (t.type === 'space' || t.type === 'hr' || t.type === 'def') continue;
				if (t.type === 'table') {
					const table = token as Tokens.Table;
					for (const cell of table.header) walk(cell.tokens);
					for (const row of table.rows) for (const cell of row) walk(cell.tokens);
					continue;
				}
				if (Array.isArray(t.tokens) && t.type !== 'codespan') walk(t.tokens as Token[]);
				else if (Array.isArray(t.items)) walk(t.items as Token[]);
				else if (typeof t.text === 'string') out.push(t.text);
			}
		};
		walk(parse(source));
		return out.join(' ').replace(/\s+/g, ' ').trim();
	}
</script>

<script lang="ts">
	import { cn } from '$lib/utils.js';

	let { text, class: className }: { text: string; class?: string } = $props();
	const tokens = $derived(parse(text));
</script>

<!--
	Rendered from the token tree, never from HTML: every string lands as text, so a note
	cannot carry a script or a tracking pixel into the page. A raw HTML tag in the body
	shows as the characters typed; an image shows as a link to it; a link opens only over
	http, https or mailto.
-->
{#snippet inline(tokens: Token[])}
	{#each tokens as token, index (index)}
		{#if token.type === 'text' || token.type === 'escape'}
			{(token as Tokens.Text).text}
		{:else if token.type === 'strong'}
			<strong class="font-semibold">{@render inline((token as Tokens.Strong).tokens)}</strong>
		{:else if token.type === 'em'}
			<em>{@render inline((token as Tokens.Em).tokens)}</em>
		{:else if token.type === 'del'}
			<del class="text-muted-foreground">{@render inline((token as Tokens.Del).tokens)}</del>
		{:else if token.type === 'codespan'}
			<code class="bg-muted rounded px-1 py-0.5 font-mono text-[0.85em]">{(token as Tokens.Codespan).text}</code>
		{:else if token.type === 'br'}
			<br />
		{:else if token.type === 'link'}
			{@const link = token as Tokens.Link}
			{@const href = safeHref(link.href)}
			{#if href}
				<a {href} target="_blank" rel="noopener noreferrer" title={link.title ?? undefined} class="focus-visible:ring-ring underline underline-offset-2 outline-none focus-visible:ring-2">{@render inline(link.tokens)}</a>
			{:else}
				{@render inline(link.tokens)}
			{/if}
		{:else if token.type === 'image'}
			{@const image = token as Tokens.Image}
			{@const href = safeHref(image.href)}
			{#if href}
				<a {href} target="_blank" rel="noopener noreferrer" class="underline underline-offset-2">{image.text || 'image'}</a>
			{:else}
				{image.text}
			{/if}
		{:else if token.type === 'checkbox'}
			<input type="checkbox" checked={(token as Tokens.Checkbox).checked} disabled class="mr-1 align-middle" />
		{:else}
			<!-- Inline HTML and anything unknown: the characters, as typed. -->
			{(token as Tokens.Generic).raw}
		{/if}
	{/each}
{/snippet}

{#snippet blocks(tokens: Token[])}
	{#each tokens as token, index (index)}
		{#if token.type === 'space' || token.type === 'def'}
			<!-- nothing -->
		{:else if token.type === 'paragraph'}
			<p>{@render inline((token as Tokens.Paragraph).tokens)}</p>
		{:else if token.type === 'text'}
			<!-- A tight list item's line, or a block the lexer left as text. -->
			{@const block = token as Tokens.Text}
			{#if block.tokens}{@render inline(block.tokens)}{:else}{block.text}{/if}
		{:else if token.type === 'heading'}
			{@const heading = token as Tokens.Heading}
			<p class={heading.depth <= 2 ? 'text-base font-semibold' : 'font-semibold'} role="heading" aria-level={Math.min(heading.depth + 2, 6)}>{@render inline(heading.tokens)}</p>
		{:else if token.type === 'blockquote'}
			<blockquote class="border-border text-muted-foreground flex flex-col gap-2 border-l-2 pl-3">{@render blocks((token as Tokens.Blockquote).tokens)}</blockquote>
		{:else if token.type === 'code'}
			<pre class="bg-muted overflow-x-auto rounded-md p-2 font-mono text-xs whitespace-pre"><code>{(token as Tokens.Code).text}</code></pre>
		{:else if token.type === 'hr'}
			<hr class="border-border" />
		{:else if token.type === 'list'}
			{@const list = token as Tokens.List}
			<svelte:element this={list.ordered ? 'ol' : 'ul'} start={list.ordered && list.start !== '' ? list.start : undefined} class={cn('flex flex-col gap-0.5 pl-5', list.ordered ? 'list-decimal' : 'list-disc')}>
				{#each list.items as item, i (i)}
					<li class={item.task ? 'list-none -ml-5' : undefined}>
						{#if item.task}<input type="checkbox" checked={item.checked} disabled class="mr-1.5 align-middle" />{/if}
						{@render blocks(item.tokens)}
					</li>
				{/each}
			</svelte:element>
		{:else if token.type === 'table'}
			{@const table = token as Tokens.Table}
			<div class="overflow-x-auto">
				<table class="border-border w-auto border-collapse text-xs">
					<thead>
						<tr>
							{#each table.header as cell, c (c)}
								<th class="border-border border px-2 py-1 font-semibold" style:text-align={cell.align ?? undefined}>{@render inline(cell.tokens)}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each table.rows as row, r (r)}
							<tr>
								{#each row as cell, c (c)}
									<td class="border-border border px-2 py-1" style:text-align={cell.align ?? undefined}>{@render inline(cell.tokens)}</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{:else}
			<!-- Block HTML and anything unknown: the characters, as typed. -->
			<p class="whitespace-pre-wrap">{(token as Tokens.Generic).raw}</p>
		{/if}
	{/each}
{/snippet}

<div data-slot="markdown" class={cn('flex min-w-0 flex-col gap-2 break-words', className)}>
	{@render blocks(tokens)}
</div>
