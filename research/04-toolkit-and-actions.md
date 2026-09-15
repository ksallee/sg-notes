# Toolkit launches, publishes, and what the site records of them

Measured on the test site, 2026-09-15, read-only, with the corpus client. Not a corpus finding:
the Toolkit side of it needs an engine running, which is out of sg-groundtruth's scope. What is
here is what the REST API returns without one.

## Launches are in the event log, not the activity stream

The site holds 190 event types. Nine are not `Shotgun_*`, and one of those is Toolkit's:

| event_type | count | what |
|---|---|---|
| `Toolkit_App_Startup` | 47 | one row per app launch through `tk-multi-launchapp` |
| `AutodeskLicense` | 519 | licence checks |
| `ShotGrid_PAT_Exchanged` | 310 | personal access token use |
| `Shotgun_Review_Tools_Version_View` | 65 | a Version opened in a review tool |
| `Shotgun_Reading_Change` | 357 | a note marked read or unread |
| `Shotgun_NoteTask_New` | 7 | a Note linked to a Task |

A launch row, verbatim shape (values are the site's):

```json
{"event_type": "Toolkit_App_Startup",
 "description": "tk-multi-launchapp v0.14.2: Maya 2026",
 "meta": {"core": "v0.24.1", "engine": "tk-shotgun v0.11.4", "app": "tk-multi-launchapp v0.14.2",
          "launched_engine": "tk-maya", "command": "open -n -a \"/Applications/Autodesk/maya2026/Maya.app\"",
          "platform": "darwin", "task": 5829},
 "user": {"type": "HumanUser", "id": 253}, "entity": {"type": "Asset", "id": 1412},
 "project": {"type": "Project", "id": 91}, "created_at": "2026-09-15T16:28:45Z"}
```

`meta.task` is present when the launch had a Task context (from the web action menu, engine
`tk-shotgun`) and absent from a Desktop launch (engine `tk-desktop`). So "what did I open today, on
what" is one `_search` on `event_log_entries` filtered on `event_type` and `user`. None of it is on
any `activity_stream`; the seeded Shot's stream after a launch on the site showed only creates.

## Publishes are in both

`Shotgun_PublishedFile_New` has 5,873 rows on the site, and a PublishedFile create is a `create`
row on the entity's and the project's stream (probe 043, and 91 of the sandbox stream's 214 rows
were PublishedFiles). The Inbox has a "Publish Creation" filter (research/03 §2). A Toolkit publish
(`tk-multi-publish2`) writes a PublishedFile with `path`, `published_file_type`, `task`, `entity`
and, with the review plugin, a Version; `recipes/004` and `013` in the corpus cover the two shapes of
`path` (a LocalStorage-relative `local` link, or uploaded bytes).

## What "Toolkit available" and "path openable" rest on

| capability | evidence on the site | what the page can offer |
|---|---|---|
| a pipeline configuration for the project | `PipelineConfiguration` rows: project 91 has `Primary` (`sgtk:descriptor:dev?path=…/tk-config-flowam`) and `basic`; the sandbox 1180 has none | open in the associated app with Task context, run any engine command, publish. Through `sgtk.bootstrap.ToolkitManager` headless (BRIEF.md, settled by probe 065) |
| a LocalStorage root mounted | `LocalStorage` `primary`, `mac_path` `/Volumes/FPT`; `PublishedFile.path.local_path_mac` resolves against it (`field_types/url`, `findings/058`) | reveal in Finder, open with the OS default app, copy the path |
| neither | always | preview the Version's media (`sg_uploaded_movie`, `image`, presigned for 900 s), the annotation frames, open the row in the web app, reply, change a status, log time, mark read, follow |

The page probes these at start: a `PipelineConfiguration` search for the project, a stat on each
root's local path, and whether `tank` or a Desktop install is on disk. Actions are offered by tier,
never greyed out in bulk: a row with an uploaded `path` gets "download" where a `local` one gets
"reveal".

## Still open

Status changes made over the API (`PUT sg_status_list`) had not appeared on any stream 13 minutes
after the write, while creates and replies took 33 s (probe 067). The seeded rows measure it: read
`fixtures/live/streams/Shot_*.json` again after the next capture.
