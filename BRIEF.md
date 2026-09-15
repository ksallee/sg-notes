# sg-artistpage

An artist's landing page for their day on Flow Production Tracking. One screen: the tasks assigned to
you, what changed since you left, the notes waiting on your reply, and one click to act. Built on
`../sg-widgets`, and meant to be the first real host those widgets live in.

Status: a brief. Nothing is built. Read `Open questions` before any code.

## Why this, and why first

- It is the view every studio rebuilds and Flow PT never quite gives: not a grid of My Tasks, but
  "what do I do now." Review already lives in Flow PT; this does not compete with it.
- It is the first app over sg-widgets. Sixty widgets in two frameworks have never lived outside the
  docs site. This is the test that they compose.
- It stresses composition on purpose. The page mixes sg-widgets items with foreign shadcn-svelte
  widgets — a sidebar, resizable panes, a command palette, toasts, a small chart — to find where the
  token contract holds and where it breaks. Every seam that fights is the next sg-widgets issue.
- It carries no infrastructure. Local-first, one process the artist runs, the same install story as
  sg-comfyui.

## Name

`sg-artistpage` for now. `sg-day` if a crisper name is wanted. Not `sg-apps`: this is the first app
and the source the blueprint is extracted from; the extracted patterns may become sg-apps later.

## Sources

- `../sg-widgets`. The client, the widgets, the proxy handler and session auth. Read its CLAUDE.md.
  `docs/proposals/connect-panel.md` is the Mock/Live pattern to reuse.
- `../sg-groundtruth`. The corpus and the FPT client. Read `corpus/INDEX.md` first. The seed and
  capture scripts call the API through its `FPT` client.
- `../sg-comfyui`. The precedent for a local host: routes, settings, login, profile, a publish that
  is a sequential pipeline. `src/comfyui_sg/routes.py` is the shape.
- `../llm-ui-annotation`. The precedent for the agent channel: a Vite plugin as the only writer, a
  file queue under a dot-directory, an `annot watch` CLI the agent runs, a websocket back to the
  page. The protocol transfers; the package does not.

Clean room applies (the rule is in `../sg-chrome/BRIEF.md`). Derive from public docs, the corpus, and
public shotgunsoftware repos. Never read the private sources it names.

## What it reads

The signed-in person is HumanUser 253 on the test site. Everything below goes through the widgets'
client.

| block | from |
|---|---|
| My tasks | Task where `task_assignees` includes me, with due date, status, linked entity |
| The entity and its thumbnail | the Task's linked Shot or Asset, its image field. See `recipes/013` |
| What changed | the activity stream on my entities. `corpus/endpoints/get_entity_type_id_activity_stream.md` |
| Notes waiting | Note linked to my tasks and its thread. `corpus/endpoints/get_entity_notes_id_thread_contents.md` |
| Following | who and what I follow. `human_users/<id>/following`, `.../followers` |

Open probe: whether a HumanUser has its own activity stream (one feed of my day), or whether "my
feed" must be fanned out over my tasks' entities. This decides the page's data shape. One
sg-groundtruth probe answers it.

## Simulating activity

The site is sandbox projects with little real activity, and the activity stream is populated only by
real mutations, all stamped "now." So there are three layers, and the demo runs on the last.

1. **Seed** (`tools/seed.py`, through the corpus `FPT` client, `--write`, one sandbox project only,
   never Big Buck Bunny). Creates a project, tasks assigned to the user, linked Shots and Assets with
   generated thumbnails, statuses, Versions, Notes and Replies. Then it *mutates* — flips statuses,
   adds notes — because that, and only that, writes activity-stream entries. Proves the real API
   shapes end to end.
2. **Capture** (`tools/capture.py`). Snapshots the seeded project's responses into `fixtures/`, the
   groundtruth way: real shapes, committed, offline, deterministic.
3. **Authored day.** The fixtures are then tuned into a believable day — timestamps spread over
   yesterday and this morning, a mix of statuses, a couple of unread notes — which the sandbox's
   all-"now" timestamps cannot give. The mock source serves these. Dev and every demo run on the mock.

Live runs against the seeded sandbox occasionally, the sg-widgets `--live` discipline. Generated
media only, so the public demo carries no one else's licensing.

## The local service

One process the artist starts. It holds the session token from the App Session Launcher (sg-widgets
`session-auth`), serves the page on localhost, exposes the widgets' proxy protocol (sg-widgets
`proxy-handler`), and exposes the same commands to an agent as a CLI. Register a command once; it is
a route and a CLI verb both. This is the blueprint the whole set is circling: params typed per
command, `check()` then `do()`, hooks and runners added only when a second command needs them.

The agent channel follows llm-ui-annotation: a watched directory is the queue, a `watch` verb blocks
until work lands, the page gets a websocket push. Read-only page first, then the channel, then write
commands. Each ships alone.

## Launching a Toolkit command (settled by probe, 2026-09-15)

"Open in Associated Application," and any registered engine command, is reachable, but not the way it
first looks.

- Desktop's `wss://shotgunlocalhost.com:9000` is origin-locked by design. Its `server_protocol.py`
  requires the connection Origin to be one of the site's own domains and the browser user to match
  Desktop's own login, and every frame after the handshake is Fernet-encrypted with a secret only the
  site issues. A localhost page cannot drive it. Do not try; the secret path is off-limits.
- The sanctioned launcher is `sgtk.bootstrap.ToolkitManager`, or the `tank` command the config
  installs on disk. The local service bootstraps the engine as the signed-in user and runs the
  command headless — the same code path Desktop uses, no socket, no origin gate.
- For a trigger that starts in the Flow PT web UI, register an Action Menu Item pointing at the local
  service.

The handshake transcript and the six-method public surface are in
`../sg-groundtruth/probes/065_desktop_websocket.py`. Write the finding there.

## Stack

- Svelte 5 first, matching sg-widgets' build order and llm-ui-annotation. React later if wanted.
- Native CSS and shadcn tokens, per sg-widgets design rules. Foreign widgets layer on the same tokens.
- The house writing rules apply: `../sg-widgets/docs/writing-rules.md`.

## Open questions

Prototype, don't search.

- The user-feed probe above: one entity's stream, or a fan-out over my tasks' entities.
- Local service tooling: plain Vite plus a small server, or the sg-comfyui route style in Node.
- Which sg-widgets items the page uses, and which foreign widgets it deliberately pulls in to stress.
- How "one click" maps to commands: open in app (Toolkit bootstrap), reply to a note (write), change
  a status (write). Which are read, which write, which launch.

Decisions.

- The name.
- Whether the seed writes a fresh project each run or reuses one sandbox.
- Whether generated thumbnails come from sg-comfyui or a trivial local generator.
- Git: not initialised yet, on purpose. `git init` when the first file lands.

## Build order

1. The user-feed probe, and the seed and capture scripts. Fixtures first: the page is built on them.
2. The read-only page on the mock source: tasks, activity, notes, thumbnails.
3. The local service: proxy, session login, one read command.
4. The agent channel, then the first write command.
5. The first launch command through Toolkit bootstrap.
6. The compose pass: pull in the foreign widgets, log every seam.
