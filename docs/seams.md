# Seams: what fought when sg-notes became the first host of sg-widgets

Logged as they were found, 2026-09-15, building the lead view. Each is an sg-widgets issue in
waiting, or a note that it is not. The install was the documented one-liner, from a local build
of the registry served over HTTP, into a SvelteKit app with sg-widgets' own `components.json`.

## 1. The Svelte registry ships none of its own primitives

`packages/svelte/src/lib/components/ui` differs from upstream shadcn-svelte in 57 files across
command, select, popover, dialog, dropdown-menu, input-group, kbd, checkbox, button, badge, input,
switch, table, textarea, toggle, calendar, hover-card, separator and skeleton, and adds
`command-status.svelte` and `label`. The registry names every one of them by plain upstream name,
so a host installs the upstream files: `search-control.svelte` then fails to compile on
`Command.Status`, and every picker draws with upstream's classes rather than the package's
(`data-highlighted`, the overflow fade, the row insets). React ships its `command` as a
`registry:ui` item for exactly this reason (`docs/registry-conventions.md` §1); Svelte has to do
the same for every primitive it changed. Workaround here: the `ui` folder copied from the package.

## 2. `@sg-widgets/core` is not on npm, and the CLI rewrites its spec

Every item names `@sg-widgets/core` as a dependency. `shadcn-svelte add` wrote it into
`package.json` as `"latest"`, over the `link:` spec already there, and `pnpm install` then 404s.
Until core is published, a host has to repair the spec after every `add`. The CLI also wrote
`bits-ui`, `@lucide/svelte`, `@internationalized/date` and `tailwind-variants` into both
dependency lists.

## 3. `init` was skipped, so `clsx`, `tailwind-merge` and `tw-animate-css` were not added

The items import `$lib/utils` and the stylesheet imports `tw-animate-css`; neither is in any
item's `dependencies`. A host that copies `components.json` and `app.css` by hand has to add
them by hand. Worth a line on the install page, or a `utils` item.

## 4. The grouped list cannot group on the record a note is about

`GroupedList` groups on a sorted path and leads the source's sort with it. A note's record is
`note_links`, a multi-entity field the site will not sort on, and the group key is derived
(the Shot or Asset over the Version, `$lib/notes.recordOf`). The app draws its own groups,
copying the widget's header and row anatomy. A `groupKey(row)` option, with the source left
sorted as the caller says, would let the widget do it.

## 5. The status sprite disappears on a dark page

`StatusGlyph` draws a stock status from the site's sprite, dark strokes made for the web app's light
page. On a dark host the bare `glyph` variant of `StatusBadge` is near invisible for Pending Review,
On Hold and the other stock icons, while the coloured shipped cells read fine. The `icon` variant
puts a surface behind it and is what this app uses in lists. The glyph wants a dark-mode treatment
of its own: an inverted or recoloured sprite, or a mask drawn in `currentColor`.

## 6. Not a seam: the live pattern carried over as is

The docs site's `live.ts`, the two launcher endpoints and the dev-token endpoint moved into
SvelteKit without a change of shape. `RestClient` from the browser, `createSgContext` once,
`ProjectPicker`, `FilterBar`, `StatusPicker`, `EntityCard`, `EntityChip`, `StatusBadge`,
`UserAvatar`, `Thumbnail`, `StateLine` and the `Skeleton` primitive took their documented props.
