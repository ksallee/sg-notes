# sg-notes

The notes workbench for Flow Production Tracking: every note in a project, grouped by what it is
about, searched, threaded, ticked and acted on in bulk. `BRIEF.md` is the plan; `research/` is what
the community and the docs say the day looks like; `tools/` seeds and captures the sandbox and drives
the page headless; `fixtures/` is the reference for what the site's rows look like; `docs/seams.md`
is what fought when the sg-widgets registry met its first host.

## Run the app

    pnpm install
    pnpm dev

Open the URL Vite prints, name the site, sign in through the App Session Launcher when the tab
opens, and pick a project. The pick is remembered. With `.env.local` holding `FPT_API_SITE_URL`,
`FPT_API_SCRIPT_NAME` and `FPT_API_API_KEY` (see `.env.example`), `pnpm dev` reads through the
script key and no sign-in is needed; a production build ignores those and always signs in.

`@sg-widgets/core` is linked from `../sg-widgets/packages/core`, so that checkout has to exist and
be built (`pnpm --filter @sg-widgets/core build` there). The widgets under `src/lib/components` are
registry copies; `docs/seams.md` says how they were installed and what to repair after an `add`.

    pnpm check                                             # svelte-check
    node tools/qa.mjs --project 1180 --drive tools/drives/lead-view.js   # drive the page headless
    node tools/qa.mjs --project 1180 --shot .playwright-mcp/lead.png     # and screenshot it
    node tools/qa.mjs --project 1180 --theme claude --mode light --shot .playwright-mcp/claude.png

The page wears one of three themes, all the sg-widgets docs site's own (Default, Supabase, Claude), in
light, dark or the system's scheme, from the palette menu in the bar; `--theme` and `--mode` set them
for a drive. The app is where the widgets are seen wearing a palette they were not drawn on, beside
primitives that are not sg-widgets' own.

A drive is the body of an async function; it returns `{verdict, ...}` and the exit code follows.
`tools/drives/` holds one per behaviour: the lead view, search and grouping, a reply, bulk actions.
The reply and bulk drives write to the project they run on.

## Seed and capture

Both scripts read `../sg-groundtruth/.env.local` and use its client, so run them with that repo's
interpreter:

    PY=../sg-groundtruth/.venv/bin/python
    $PY tools/seed.py                                    # dry run: the plan, no writes
    $PY tools/seed.py --write --artist <login> --artist2 <login> --supervisor <login>
    $PY tools/capture.py                                 # snapshot to fixtures/live/ and fixtures/media/
    $PY tools/seed.py --clean                            # delete every seeded row

Three people, all written through `sudo_as_login`. `--artist` and `--artist2` are the logins the
tasks are split between and the versions and most replies are written as; `--supervisor` is the
login the review notes are written as. The current month uses the site's two Artist-permission
accounts and the operator's own login, so notes written in the web app as yourself land on the page.
`--artist2` defaults to the HumanUser named "Other Artist". The seed adds both artists to the
project's users if needed; the Artist permission set cannot create Tasks, so Tasks are always
created by the script user. About one note in twenty-five is left to the script user on purpose:
those reach no stream and no Inbox (sg-groundtruth finding 067), which is a shape the page has to
render. Without `--supervisor` every note is the script's.

`tools/_plan.py` builds the month from a fixed random seed, so the same anchor date produces the
same site and a reseed is a reseed. The dry run prints that plan. One run writes:

| | |
|---|---|
| records | 3 sequences, 22 shots, 12 assets |
| work | 107 tasks over two artists, 156 versions, four in five with a thumbnail |
| notes | 321 over five weeks, on a long tail: a handful of records carry 15 to 27, most carry one or two |
| shape | a third unaddressed, a third client-facing, half with a task, 8 on the project itself, 5 linked to nothing |
| threads | 374 replies, 0 to 5 per note |
| files | 140 attachments, 57 of them `annot_version_<version>.<frame>.png` |

`fixtures/seed-manifest.json` is the list of rows the last seed made, in order, with the three people
and what the site refused. `--clean` deletes them in reverse and removes the file. The seed refuses
to run while the file exists.

## What the site would not take

Measured on the test site, once, on rows the seed owns.

- `created_at` **is** accepted on a Note and a Reply create and reads back exactly, under
  `sudo_as_login` and as the script, although `/schema` reports `Note.created_at` as
  `editable: false`. The month is real: notes and replies are spread over five weeks with a working
  week's rhythm, and so are the Tasks and Versions under them.
- The seed sends no `updated_at`, so every row's is the moment it ran. A note whose `updated_at` is a
  month newer than its `created_at` is the normal case here, not a signal. The site would take one:
  `updated_at` is accepted on create for Note, Task and Version (a Reply has no such field), per
  sg-groundtruth finding 070, so a later seed can date both.
- `client_note` is refused twice over: a create answers `Client Notes can not be created through the
  API` and an update answers `Note.client_note is editable on create only`. It is false on every note
  in these fixtures. A client-facing note carries `sg_note_type` `Client` and nothing else.
- `read_by_current_user` takes an update, as the person whose read state it is.
- An upload carries no date, so an Attachment's `created_at` is the moment the seed ran while the
  Note it hangs off is weeks old.
- Event-log entry timestamps cannot be authored at all. "What changed since" is measurable forward
  from a seed and never backward over it (finding 025), so a run ends with a pass of status changes
  on notes, tasks and versions. Those are the newest thing the log holds when the capture runs, and
  `live/events.json` is that window.

## What the fixtures hold

Two views of one project: 325 notes, 375 replies, 140 attachments, 400 event-log entries and 269
media files. Each view is read as the person whose view it is, because `read_by_current_user` is
per-person and means nothing read as a script.

| file | the call |
|---|---|
| `live/me.json` | the artist's HumanUser row |
| `live/tasks.json` | Tasks where `task_assignees` is the artist, in the sandbox, by due date, with the entity's thumbnail as a dotted path |
| `live/shots.json`, `live/assets.json` | the entities behind those tasks |
| `live/versions.json` | Versions on those entities, newest first |
| `live/notes.json` | Notes addressed to the artist, on their tasks, or on their entities and versions, merged, read as the artist |
| `live/streams/<Type>_<id>.json` | the activity stream of each Shot and Asset behind the artist's tasks, the feed's fan-out (probe 066) |
| `live/following.json` | what the artist follows in the project |
| `live/project-notes.json` | every note in the project, newest first, read as the supervisor |
| `live/project-shots.json`, `live/project-assets.json`, `live/project-versions.json`, `live/project-tasks.json` | the records those notes point at |
| `live/people.json` | the project's HumanUsers and everyone a note names, with `image` |
| `live/events.json` | `event_log_entries` for the project since the seed started, newest first, capped at 400 |
| `live/threads/<note>.json` | `thread_contents` per note, for every note in the project |
| `media/` | every thumbnail and avatar the responses pointed at, since the URLs expire in 900 s |

The site host, e-mail addresses and media URLs are replaced; names are as the seed wrote them. A
capture removes what an earlier one left behind, so `fixtures/` holds one site and not a history.

## What the page has to survive

Shapes that are in these fixtures because a real site has them.

- `client_note` is false on all 325 notes and `sg_note_type` is null on 39, so neither alone says
  whether a note faces the client.
- 23 notes were written by an ApiUser and have no HumanUser author to draw.
- 6 notes link to nothing, 8 link the Project rather than a record, and 207 link two things at once.
- Two of the three people have no avatar.
- 24 of the 130 Versions the notes point at have no `image`, and one Shot's thumbnail was still
  transcoding when the capture ran and reads null.
- The sandbox is not empty and the seed does not own all of it: four notes from earlier probes have
  no links and no thread, and the project holds Versions and Tasks no note mentions.
