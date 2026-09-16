# Seams: what fought when sg-notes became the first host of sg-widgets

Logged as they were found, 2026-09-15, building the lead view. The install was the documented
one-liner, from a local build of the registry served over HTTP, into a SvelteKit app with
sg-widgets' own `components.json`. Filed and fixed the same day on `dev`: ksallee/sg-widgets#196
(PR #200), #197 (#201, #205), #198 (#203), #199 (#202); #206 filed for the designer. A clean
reinstall of every item from that `dev` registry into this app then checked green with nothing
copied by hand, which is the test that counts.

## 1. The Svelte registry ships none of its own primitives

`packages/svelte/src/lib/components/ui` differs from upstream shadcn-svelte in 57 files across
command, select, popover, dialog, dropdown-menu, input-group, kbd, checkbox, button, badge, input,
switch, table, textarea, toggle, calendar, hover-card, separator and skeleton, and adds
`command-status.svelte` and `label`. The registry names every one of them by plain upstream name,
so a host installs the upstream files: `search-control.svelte` then fails to compile on
`Command.Status`, and every picker draws with upstream's classes rather than the package's
(`data-highlighted`, the overflow fade, the row insets). React ships its `command` as a
`registry:ui` item for exactly this reason (`docs/registry-conventions.md` §1); Svelte has to do
the same for every primitive it changed. Fixed in #200: `command`, `select` and `checkbox`, the
three that carry this repo's own changes, ship as `registry:ui` items and the registry's `ui`
alias now points where the files are; the other sixteen differ from upstream only by class
order or by upstream's own drift, so a host rightly gets upstream's. `docs/registry-conventions.md`
says when a primitive earns an item.

## 2. `@sg-widgets/core` is not on npm, and the CLI rewrites its spec

Every item names `@sg-widgets/core` as a dependency. `shadcn-svelte add` wrote it into
`package.json` as `"latest"`, over the `link:` spec already there, and `pnpm install` then 404s.
Until core is published, a host has to repair the spec after every `add`. The CLI also wrote
`bits-ui`, `@lucide/svelte`, `@internationalized/date` and `tailwind-variants` into both
dependency lists. Still true after #205: the CLI installs its dependencies as one batch, so the
404 on core stops every other package from landing; the install page now says so and gives the
repair line. Publishing core is the fix, and it is the operator's.

## 3. `init` was skipped, so `clsx`, `tailwind-merge` and `tw-animate-css` were not added

The items import `$lib/utils` and the stylesheet imports `tw-animate-css`; neither is in any
item's `dependencies`. A host that copies `components.json` and `app.css` by hand has to add
them by hand. Fixed in #201 and #205: the items declare `clsx`, `tailwind-merge` and
`tw-animate-css`, and `/start/install/` says what `init` writes.

## 4. The grouped list cannot group on the record a note is about

`GroupedList` groups on a sorted path and leads the source's sort with it. A note's record is
`note_links`, a multi-entity field the site will not sort on, and the group key is derived
(the Shot or Asset over the Version, `$lib/notes.recordOf`). The app draws its own groups,
copying the widget's header and row anatomy. Fixed in #203: `GroupedList` takes `groupKey(row)`
and `groupLabel(value)` in both frameworks and leaves the source's sort alone. This app keeps its
own list all the same: it has since grown ticking, links per row, a parent per header and a
grouping switch, which is a notes list rather than a grouped list, and the widget has what a
plainer host needs.

## 5. The status sprite disappears on a dark page

`StatusGlyph` draws a stock status from the site's sprite, dark strokes made for the web app's light
page. On a dark host the bare `glyph` variant of `StatusBadge` is near invisible for Pending Review,
On Hold and the other stock icons, while the coloured shipped cells read fine. The `icon` variant
puts a surface behind it and is what this app uses in lists. The glyph wants a dark-mode treatment
of its own: an inverted or recoloured sprite, or a mask drawn in `currentColor`. Filed as #206,
a design decision left to the designer.

## 6. The Note schema does not declare `read_by_current_user`

Measured on the operator's site: `GET /schema/Note/fields` answers 33 fields and none of them is
the read state, so a schema override that only retypes a declared field never fires and the filter
bar offered the pill disabled under its programmatic name. Fixed in #202: the override adds the
field when the schema lacks it, and the pill reads "Read by Current User".

## 7. What the design review found in the library

`docs/ux-review.md` set ten findings apart as the library's. Filed and fixed on `dev` the same day:
the thumbnail's empty state (#207, PR #216), the entity card's two statuses (#208, #216), a clear on
a mandatory field (#209, #217), status values as plain text in the filter bar and no label override
(#210 and #215, #219), the control ladder at 28/32/36 with the rule corrected rather than the
registry (#212, #220), the dark palette's non-text tokens (#213, #221: ring 6.99:1, border 1.32:1,
accent 1.50:1), the search highlight as a `match-text` item (#214, #222), the pill capped at
`max-w-64` with `+n` (#211, #219), and collapse state as a mode plus exceptions in core so
"collapse all" holds across pages (#223, #224). This app took every one on a clean reinstall: the
list imports the collapse state, the bar names its pills To, From, Type and Read through `labels`,
the rows draw `MatchText`, and the dark block carries the site's corrected values. Left with the
designer: the primitives' half-strength focus ring at 2.67:1 and muted text on a highlighted row.

## 8. The filter bar's `counts` hook cannot count an entity facet

With no `counts`, the bar tallies facet values from one page of `sampleSize` rows, 200 by default,
so on a 325-note project the read-state facet said 104 read and 96 unread. With `counts`, the values
come from `facetValues([], field)`, the schema's `validValues` alone, so a list facet counts through
`_summarize` but an entity facet (To, From) lists nobody, and `_summarize` refuses to group on
`read_by_current_user` at all (400 "Grouping is not allowed"). This app raises `sampleSize` to 1000
instead, exact for its projects and a sample on a bigger one. The hook wants to take its values from
the summarize groups, which carry the entity's name and id, and to fall back per field.

## 9. Not a seam: the live pattern carried over as is

The docs site's `live.ts`, the two launcher endpoints and the dev-token endpoint moved into
SvelteKit without a change of shape. `RestClient` from the browser, `createSgContext` once,
`ProjectPicker`, `FilterBar`, `StatusPicker`, `EntityCard`, `EntityChip`, `StatusBadge`,
`UserAvatar`, `Thumbnail`, `StateLine` and the `Skeleton` primitive took their documented props.
