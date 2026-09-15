# A design review of sg-notes

Read on the seeded sandbox, 2026-09-15, headless at 1440x900, dark only. Screenshots are named in
the text and sit in `.playwright-mcp/`. Each area is rated out of five in its heading.

Assumptions, since the operator was not reachable. The reader is a lead opening the page with a
project's notes to clear. The dev key stands in for a signed-in person, so every note reads unread
and none is addressed to the reader. The seeded month is a small show, not a five-thousand-note one.

## What works

The page answers the question it set out to answer, on one screen. Notes sit under the record they
are about, which neither the Inbox nor the Review notes panel will do. Grouping is live on nine keys,
search runs on the site rather than over the loaded page, and the facets carry counts over the whole
project. Ticking, a stacked pane and a selection-scoped palette give a lead a way through 325 notes
that no shipping Flow PT surface offers. The waiting-on rule is derived correctly and stated in
plain words. That is a lot for a first version.

## The list — 2/5

`review-settled.png`. A row is three lines and 69 pixels, or two and 49 when the note links nothing,
so twenty rows fill the viewport. The author is drawn twice: as an avatar, then as a name opening
the body line. Grouped by Author it is drawn three times (`review-group-author.png`). Grouped by
Status, every row still carries its own badge under a header that names the status
(`review-group-status.png`).

Nothing in the row is ranked: subject, body, links, time and the waiting line are all muted grey at
12 to 14 pixels. The one element with weight is the subject, bold because the note is unread, and
every note is unread. Up to four status glyphs appear in one row and all four render as near-black
circles. A closed note is drawn like an open one. Rows are divided at half of a border token that is
white at five per cent, which is 1.06:1 against the page, so there is no visible line between them
and the list reads as a wall.

## Grouping, search, filters, ticking — 3/5

Grouping is the best thing here. Its nine options are right, though "Nothing" is an odd word for
flat, and picking it disables the two collapse buttons beside it without saying why
(`review-group-none.png`).

Search is a 28-pixel box wearing the browser's own clear cross rather than the design system's
(`review-empty.png`). It does not embolden what it matched, although the rules ask for that and the
library's search control does it. Ticking has three gestures — a checkbox, shift-click for a run,
option-click for one — and the page documents none of them.

The facet pills are raw schema labels: "Created by", "Client Note", "Read by Current User". The last
is site jargon; the middle filters a field that is false on all 325 notes, so it is a dead end by
construction. There is no facet for the thing the page computes and the reader came for.

## The right pane — 3/5

`review-thread.png`. The single thread is the strongest surface in the app, and it has three faults.
The record card shows two contradictory statuses: the header badge reads Waiting to Start and the
Status row sixty pixels under it reads In Progress, for the same Shot. The note's status picker
carries a clear cross, so a lead can blank a mandatory field. Largest, reply and status are two
controls in two corners, when the loop this page exists to close is reply, then Closed.

The stacked pane (`review-ticked-palette.png`) is a good idea drawn thin: its lines carry relative
times while the threads under them carry absolute ones. The pane itself is 512 pixels wide, fixed,
and empty until a row is picked, including when the list has none to pick (`review-empty.png`).

## The palette — 3/5

`review-palette.png`. Eleven items in three groups, wording that counts its targets, a heading that
says what they are. With nothing ticked and nothing open it offers six disabled items counting zero:
"Reply to 0 notes…", "Close 0 notes". A palette opening on a dead list should say what to do instead.

There is no Forward. It is the loudest ask on the forum, it is named in the brief as first-class, and
its absence is what a lead notices first. Nor is there Reply and close. Bulk reply writes one sentence
onto every ticked note through a dialog that names no note and warns of nothing
(`review-reply.png`). A Reply cannot be deleted, so there is no way back.

## Waiting on whom — 2/5

The rule is right and the drawing throws it away. The line is the second row of the date cell, muted,
capped at ten rems, so the common case truncates to "Waiting on Kevin Artist, Oth…". It is the same
colour, size and weight as the timestamp above it. The brief calls it a column; it is a footnote.

Blank means two things. A closed note prints nothing; a note whose replies have not landed prints a
skeleton. One second into a load, a hundred rows carry a hundred shimmering bars where the answer
will go, because the replies are read after the rows arrive (`review-loading.png`). They resolve over
several seconds and the rows grow as they do. "Addressed to nobody" shares the slot and the styling
with "Waiting on X", so a warning and a status speak in one voice.

## Empty, loading, error — 2/5

The first read is honest: skeletons shaped like rows, no spinner. A re-read dims rather than flashes.
The empty state is neither: one line pinned to the top of an 800-pixel void, saying "No note matches
this filter" when what the reader typed was a search, with no control to clear it, beside a pane
still offering to open a thread. I could not reach the error state without writing to the site, so it
is unrated; the code puts a state line and a retry in the right place.

## Keyboard — 2/5

Arrows walk the rows, Home and End jump, Enter opens a thread, the palette is on the usual key, and
a reply sends on command-return. Everything else is Tab. Reaching the first row from a fresh page
takes 22 tabs, and every row then costs two stops, so the hundredth row is 220 tabs away. There is no
skip link, no key that focuses the search, none that ticks the focused row, and no Escape that clears
a search or a selection. A lead cannot triage this list from the keyboard.

## Motion — 4/5

Durations are 150 and 200, easing is correct, reduced-motion variants are present, and nothing
animates on first render. One violation: the bulk-job progress bar animates width, which the rules
forbid outright.

## Colour and contrast — 2/5

The palette is legible where it is text: body 16.7:1, muted text 5.13:1, the success green 7.41:1.
Everything that is not text fails. A selected row is 1.10:1 against the page, a ticked row 1.04:1,
hover 1.02:1, the sticky group header's fill 1.03:1, row separators 1.06:1, and the focus ring
1.41:1 against the 3:1 a focus indicator is held to.

The result is in `review-ticked-palette.png`: three rows are ticked and the only evidence is three
checkboxes. Selection, hover and focus — the three things a triage list has to show — are all below
what a good monitor resolves in a bright room. These values came over from the sg-widgets site, so
the repair belongs in both places.

## Widget choices — 3/5

What is composed is composed well, and every widget takes its documented props. What is hand-drawn
and should not be is the list row. One row component is meant to serve every widget that lists entity
rows; this list draws its own because the grouped list cannot group on a derived key. The grouping is
the blocked part, not the row, and the cost shows: the leading slot is top-aligned with a padding
nudge rather than a fixed centred slot, and neighbouring rows differ by 20 pixels.

Also hand-drawn: the job progress bar, where shadcn ships Progress; the stacked pane, where Accordion
would have brought its keyboard model; and the reply composer, a bare textarea where the pane wants
an addressee row and a close toggle. The toolbar stacks 32-pixel pills over a 28-pixel search, a
28-pixel select and 24-pixel chevrons in 60 vertical pixels.

## Wording — 3/5

Good: "Waiting on Kevin Artist.", "Addressed to nobody, so nobody will see it in an inbox.", "One
reply, written on each of them as you." That is the app's voice and it is a good one. Weak: "Read by
Current User" on a pill; "No note matches this filter" after a search; "Reply to 0 notes…"; "Group by
Nothing"; "Actions", which names a menu rather than a job. The site's host is printed bare beside the
wordmark, where it reads as the signed-in person, and the far right pairs "Reading with the dev key"
with a "Sign in" button, which together read as a failure rather than a working state.

## What a first-time user fails at

Ticking: they find the checkbox and never learn that shift-click takes a run. Seeing what they
ticked: at 1.04:1 they lose the thread after three rows. Understanding the palette: the key is
printed on the Actions button, which is right, but with nothing ticked it lists six disabled items
rather than saying it acts on a selection. Closing a note after replying: the note stays Open and
they do not connect the picker in the far corner with what they did. Forwarding: they look, do not
find it, and go back to the web app. Trusting the count: "100+ notes" is the loaded page.

## Against the field

Linear's Triage is the nearest analogue and scopes its palette to the selection exactly as this app
does. It adds single-digit verbs for the actions done ninety per cent of the time, a mark-read pair,
a "show unread first" toggle, and a persistent bulk bar at the foot of the list. Its snooze returns
an item at a chosen time or when there is new activity, whichever comes first — the best idea in the
field for a notes queue.

Hey's Focus and Reply is this app's stacked pane with a reply box beside each thread; the stack here
is readable and not composable, which is one prop away. Frame.io's comment panel filters on person,
hashtag, annotation and unread, and sorts on six keys including Completed. This app has no sort at
all: the order is fixed newest-first, so a lead cannot bring the oldest unanswered note to the top.

ftrack marks a note done and tells its author; Frame.io has Mark As Complete beside an unread filter;
Linear has accept and decline beside mark-read. All three keep read and resolved on separate axes.
This app does too, and draws them identically.

What this app has that none of them do is notes grouped by the record they are about; Linear's own
docs say its inbox can be reordered but not grouped. Defend that by making the group header carry an
open count, a waiting count, and a thumbnail that is never a broken-image glyph. Nobody in the field
answers who owes the next word. This app does, and draws it as the smallest text on the page.

## Recommendations, by impact

1. **Make selection visible.** Give the list its own fills rather than the accent token: a primary
   wash at 12 to 15 per cent on a selected row with a two-pixel leading bar, half that on a ticked
   one, and a bulk bar at the foot carrying the count and the three common verbs.
2. **Make waiting-on a column.** Fixed width, avatars plus a name, foreground weight when the reader
   is owed, and "Closed" printed there so blank never means two things. Decide the case from the
   note's own replies relationship, which the page already requests, so the hundred skeletons go and
   nothing reflows. Add a Waiting-on facet to the bar.
3. **Fix the focus ring and the separators.** Take the ring token to primary or lighter and the
   border token to ten or twelve per cent white, in the dark block.
4. **Join reply to status.** A "Reply and close" split button in the pane, a matching palette item,
   and a reply box per thread in the stacked pane.
5. **Give the list a keyboard.** Slash focuses the search, `x` ticks the focused row and `Shift+X`
   extends, Escape clears the search then the selection, `e` closes, `r` replies, `u` toggles read.
   Take the checkbox out of the tab order and print the table in the palette.
6. **Thin the row.** Drop the author's name from the body line, drop the status glyphs from the link
   chips, hide the facet the group already states, and fade closed notes.
7. **Add Forward**, and say in the palette that it duplicates the note to new addressees.
8. **Guard the bulk write.** List the subjects in the reply dialog, say it cannot be undone, and
   print the send shortcut on the button.
9. **Add a sort:** newest, oldest, longest waiting, most replies.
10. **Fix the zero states.** Centre the block, name what was searched, offer to clear it, and blank
    the right pane when there is nothing to open.
11. **Fix the count:** "100+ notes" is the loaded page, not the project.
12. **Highlight matched runs** in the weight the rules name.
13. **Rename the pills** to To, From, Type and Read; drop Client Note for a note-type facet.
14. **Stop passing the status field to the record card**, which draws one already.

## Not this app: sg-widgets issues

These belong in `docs/seams.md`, and then in the library.

1. **The status glyph is unreadable on a dark page.** Logged as seam 5; the library owes it a dark
   treatment.
2. **The thumbnail's missing-image state is a broken-image glyph.** Two of three group headers in
   `review-loading.png` show a crossed-out picture box where an entity glyph belongs. No thumbnail is
   the normal case, not an error.
3. **The entity card draws two statuses.** Its own chain picks one field and a caller-supplied status
   column picks another; the card showed Waiting to Start and In Progress for one Shot.
4. **The status picker offers a clear on a mandatory field**, against clause 8 of the picker contract.
5. **The filter bar renders status values as plain text.** Its facet popover lists Closed, Open and
   In Progress with no badge (`review-filter.png`) while the list badges them.
6. **The filter bar has no label override**, so "Read by Current User" reaches the pill from the
   schema.
7. **The small control size renders at 28 pixels**, where the rules put it at the shadcn 32-pixel
   step. Either the rule or the registry is wrong; a host mixing the two gets two heights.
8. **The dark palette's non-text tokens fail contrast.** Ring, border and accent were copied from the
   site's stylesheet and measure 1.41:1, 1.13:1 and 1.10:1.
9. **The grouped list cannot group on a derived key.** Logged as seam 4, and it is what forces this
   app to hand-draw the row anatomy the library owns.
10. **The search highlight is not reusable.** A host drawing its own list cannot ask for the
    treatment the search control gives matched runs.
