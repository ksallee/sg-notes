<!--
	The app's mark and lockup, a sibling of the sg-widgets one (its
	`docs/design-rules.md` rule 10): two tiles, the accent once on the back one, the
	quiet ink in front, lifted off by a gap in the colour of the surface under the mark.
	What makes it this app's is the front tile: it is a note about the widget, a bubble
	whose tail points at the accent tile, with two lines of text cut into it. The corners
	follow `--radius` on the back tile; the bubble is a path, so its corners are drawn.
	`src/lib/assets/favicon.svg` is this drawing with the palette's values pinned.

	The type beside it is the title split at its first space: the head word at semibold
	in `currentColor`, the tail in the muted ink at regular, tracked a touch tight.
-->
<script lang="ts">
	let { title = 'SG Notes', size = '1.25em' }: { title?: string; size?: string } = $props();
	const head = $derived(title.split(' ')[0] ?? '');
	const tail = $derived(title.split(' ').slice(1).join(' '));
</script>

<span class="wordmark" translate="no">
	<svg class="mark" style="width:{size};height:{size}" viewBox="0 0 40 40" aria-hidden="true" focusable="false">
		<rect class="tile accent" x="2" y="2" width="22" height="22" />
		<path class="bubble" d="M20 13 h14 a4 4 0 0 1 4 4 v14 a4 4 0 0 1 -4 4 h-14 a4 4 0 0 1 -4 -4 v-5 l-6 -4 6 -1 v-4 a4 4 0 0 1 4 -4 z" />
		<rect class="line" x="21" y="20" width="12" height="2.4" rx="1.2" />
		<rect class="line" x="21" y="26" width="7" height="2.4" rx="1.2" />
	</svg>
	<span class="type"><span class="head">{head}</span> <span class="tail">{tail}</span></span>
</span>

<style>
	.wordmark {
		display: inline-flex;
		align-items: center;
		gap: 0.45em;
		font-size: 1rem;
		line-height: 1.1;
		letter-spacing: -0.01em;
		white-space: nowrap;
		min-width: 0;
	}

	.mark {
		display: block;
		flex: none;
		--tile-radius: calc(var(--radius) * 0.5);
		--ground: var(--mark-ground, var(--background));
	}

	.tile {
		rx: var(--tile-radius);
		ry: var(--tile-radius);
	}

	.accent {
		fill: var(--primary);
	}

	/* The gap that lifts the bubble off the accent tile: the stroke is drawn under the
	   fill, so the whole gap falls outside the bubble and the bubble keeps its size. */
	.bubble {
		fill: color-mix(in oklab, currentColor 30%, var(--ground));
		stroke: var(--ground);
		stroke-width: 2.2;
		stroke-linejoin: round;
		paint-order: stroke;
	}

	/* The note: two lines cut into the bubble in the colour of the ground. */
	.line {
		fill: var(--ground);
	}

	.type {
		overflow: hidden;
	}

	.head {
		font-weight: 600;
	}

	.tail {
		font-weight: 400;
		color: var(--muted-foreground);
	}
</style>
