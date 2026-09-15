# sg-notes

The notes workbench for Flow Production Tracking: every note in a project, filtered, grouped by the
record it is about, threaded, with reply, close and forward as first-class actions, and "waiting on
whom" as a column. Built on `../sg-widgets` and meant to be the first real host those widgets live
in. It started life as an artist landing page; `research/` holds why it changed.

Status, 2026-09-15: research, probes, a seed and a capture exist. No page yet.

## Why this, and why first

- It is the loudest, oldest, still-open complaint on the Flow PT community forum: the Inbox at
  "99+" with no filters, no way to forward a note, notes on the wrong record, and Review shipping GA
  in June 2026 without the ability to reply. `research/02` and `03`.
- It is the first app over sg-widgets, and it hits the library where it is thickest: the filter bar
  and dialog, the user, status, entity and project pickers, the grouped list, the entity table,
  thumbnails, cards, avatars, the value editor. An artist page used the display widgets and little
  else.
- It stresses composition on purpose. Foreign shadcn-svelte widgets layer on the same tokens: a
  sidebar for projects and saved filters, a resizable split between list and thread, a command
  palette, toasts for write results, one chart. Every seam that fights is the next sg-widgets issue.
- It is what shapes sg-apps. The blueprint is extracted from this app, not designed ahead of it.
- It carries no infrastructure. One local process, sign-in through the browser with the App Session
  Launcher, no script key. Clone, run, see your own project's notes.

## Decisions

- **Lead view first.** The person triaging a project's notes, not the artist reading theirs. The
  artist's "mine" view is the same data filtered to me, and comes second.
- **No LLM in v1.** The evidence for an LLM here is on writing (draft a reply, summarise a thread,
  route a note), not on reading. It comes after the page has been used for real. `research/05`, `06`.
- **The client grows in sg-widgets, the proper way.** Issue, PR, merge to dev and main. This app does
  not carry a private client extension. What it needs that `SgClient` lacks today: `create` (Reply,
  Note), `threadContents`, an event-log read, upload, following. `docs/sg-widgets-issues.md`.
- **"What changed" comes from the event log**, one `_search` on `event_log_entries` by project,
  entity and `created_at`, with `old_value` and `new_value` in `meta` (corpus finding 025). Not the
  activity stream: status changes made over the API were absent from every stream 20 minutes after
  the write, while creates and replies took 33 s (findings 066, 067).
- Writes as people. A Note or Reply written by the bare script never reaches a stream or an Inbox;
  every seed write goes through `sudo_as_login` (finding 067).
- The seed reuses the one sandbox project and keeps a manifest of what it made. Thumbnails are a
  standard-library PNG generator. The artist persona is the site's Artist-permission account; the
  supervisor is the operator, so notes written in the web app land on the page.
- Name: `sg-notes`.

## Sources

- `../sg-widgets`. The client, the widgets, the proxy handler and session auth. Read its CLAUDE.md.
  `docs/proposals/connect-panel.md` is the Mock/Live pattern to reuse.
- `../sg-groundtruth`. The corpus and the FPT client. Read `corpus/INDEX.md` first. Findings 043,
  066, 067 (attention, the user feed, notes in the stream), 025 (event log), entity cards for Note,
  Reply, Attachment.
- `../sg-comfyui`. The precedent for a local host: routes, settings, login, profile.
- `../llm-ui-annotation`. The precedent for an agent channel, when one is wanted.
- `research/`. Seven passes: the artist's day, review notes, the Inbox and feed, Toolkit and
  actions, what people ask, generative UI, what a site's notes look like.

Clean room applies (the rule is in `../sg-chrome/BRIEF.md`). Derive from public docs, the corpus, and
public shotgunsoftware repos. Never read the private sources it names.

## What it reads

| block | from |
|---|---|
| Notes in the project | `POST /entity/notes/_search`, with `note_links`, `tasks`, `addressings_to`, `addressings_cc`, `sg_status_list`, `sg_note_type`, `client_note`, `read_by_current_user`, `replies`, `attachments` |
| The thread | `GET /entity/notes/<id>/thread_contents`: Note, Attachments, Replies in time order; author under `created_by` on two of them and `user` on the third |
| Who owes a reply | derived: last thread row's author versus the addressee, status not `clsd` |
| The record and its thumbnail | the linked Shot, Asset or Version, its `image` |
| Annotations | Attachments named `annot_version_<version>.<frame>.png`, one image each |
| What changed since | `event_log_entries` by project and `created_at`, filtered to the attributes the view shows |
| People | `human_users` with `image`, for pickers and avatars; `following` for the "mine" view |

## Actions, by what the machine has

| always | with a mounted storage root | with Toolkit configured for the project |
|---|---|---|
| reply, set note status, forward (duplicate with new addressees, the forum's own workaround), mark read, open the row in the web app, preview media and annotation frames | reveal in Finder, open with the OS | open in the associated app with Task context, through `sgtk.bootstrap.ToolkitManager` headless (`research/04`) |

Writes in v1: reply and note status. Forward once the client has `create`.

## Simulating a site

No production site is reachable, and the test site's demo project has 5,944 notes with no threads,
no tasks and no attachments (`research/07`). Three layers, and the demo runs on the last:

1. **Seed** (`tools/seed.py`, `--write`, one sandbox project, never the demo project). Grows from
   one artist's day to a lead's month: a few hundred notes over dozens of records on a long tail, a
   third unaddressed, a third client-facing, threads of 0 to 5, attachments on a third, tasks on half.
2. **Capture** (`tools/capture.py`) into `fixtures/live/`: real shapes, committed, offline.
3. **Authored month**: timestamps spread over weeks, which the sandbox's all-"now" cannot give.

## Open questions

- Which sg-widgets items the lead view uses, and which foreign widgets it deliberately pulls in.
- Local service tooling: plain Vite plus a small server, or the sg-comfyui route style.
- The lead's "waiting on whom" rule when a note has several addressees and a mixed thread.
- How the page survives a project where every optional column is empty.

## Build order

1. Done: the probes, the seed and capture for one day, the research.
2. The sg-widgets client issues, filed and merged, so the page has `create` and `threadContents`.
3. The seed grown to a lead's month, captured, then the authored month.
4. The read-only lead view on the mock source: list, filters, groups, thread, annotation previews.
5. The local service: proxy, browser sign-in, the first write (reply), then note status.
6. The "mine" view. Then the compose pass with the foreign widgets, logging every seam.
