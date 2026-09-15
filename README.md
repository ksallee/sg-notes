# sg-notes

The notes workbench for Flow Production Tracking. `BRIEF.md` is the plan;
`research/` is what the community and the docs say the day looks like; `tools/` seeds and captures
the sandbox; `fixtures/` is what the page is built on.

Nothing of the page exists yet. Build order is in the brief.

## Run

Both scripts read `../sg-groundtruth/.env.local` and use its client, so run them with that repo's
interpreter:

    PY=../sg-groundtruth/.venv/bin/python
    $PY tools/seed.py                                    # dry run: the plan, no writes
    $PY tools/seed.py --write --artist <login> --supervisor <login>   # seed the sandbox, as people
    $PY tools/capture.py                                 # snapshot to fixtures/live/ and fixtures/media/
    $PY tools/seed.py --clean                            # delete every seeded row

`--artist` is the login the tasks are assigned to and the versions and replies are written as;
`--supervisor` the login whose notes and reviews are written. Both go through `sudo_as_login`. The
current day uses the site's Artist-permission account as the artist and the operator's own login as
the supervisor, so notes written in the web app as yourself land on the artist's page. The seed adds
the artist to the project's users if needed; the Artist permission set cannot create Tasks, so Tasks
are always created by the script user. Without `--supervisor` the notes are the script's and
never reach an activity stream (sg-groundtruth probe 067).

`fixtures/seed-manifest.json` is the list of rows the last seed made, in order. `--clean` deletes
them in reverse and removes the file. The seed refuses to run while the file exists.

## What the fixtures hold

| file | the call |
|---|---|
| `live/me.json` | the artist's HumanUser row |
| `live/tasks.json` | Tasks where `task_assignees` is the artist, in the sandbox, by due date, with the entity's thumbnail as a dotted path |
| `live/shots.json`, `live/assets.json` | the entities behind those tasks |
| `live/versions.json` | Versions on those entities, newest first |
| `live/notes.json` | Notes addressed to the artist, on their tasks, or on their entities and versions, merged |
| `live/threads/<note>.json` | `thread_contents` per note |
| `live/streams/<Type>_<id>.json` | the activity stream of each Shot and Asset, the feed's fan-out (probe 066) |
| `live/following.json` | what the artist follows in the project |
| `media/` | every thumbnail and avatar the responses pointed at, since the URLs expire in 900 s |

The site host, e-mail addresses and media URLs are replaced; names are as the seed wrote them.
