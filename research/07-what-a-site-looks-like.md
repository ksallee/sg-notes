# What a site's notes look like

Measured 2026-09-15, read-only, on the two projects the test site has beyond the sandbox. Neither is
a production site, and no production site is reachable from here; this is the best available
proxy, and the gap it leaves is stated at the end.

## The demo project (Big Buck Bunny, 5,944 notes)

Autodesk's demo generator wrote every one of them inside 54 minutes on 2015-12-01. Volume is
realistic; shape is not.

| measure | value |
|---|---|
| status | `opn` 1,942, `ip` 2,009, `clsd` 1,993: an even third each |
| `sg_note_type` | Internal 3,896, Client 2,048; `client_note` false on all |
| `note_links` | exactly one per note, always a Shot; 300 distinct Shots; the busiest carries 20 |
| `tasks` | empty on every note |
| `addressings_to` | 63% filled: 0 on 2,224, 1 on 2,351, 2 on 1,123, 3 on 243, 4 on 3 |
| `addressings_cc`, `attachments`, `replies` | empty on every note |
| `created_by` | `null` on every note (the generating user is retired) |
| `subject` | always filled; `content` median 424 characters |
| `read_by_current_user` | `unread` on all, read as the script |

What transfers: thousands of notes, a few hundred shots, a long tail with up to 20 notes on one shot,
a third of notes with nobody addressed, a third marked client-facing, and a null author the page
must render.

## A real, small project (Kids Room, 8 notes)

Written by two people over nine months, 2025-05 to 2026-02.

| measure | value |
|---|---|
| `note_links` | 7 of 8: Asset 4, Project 3 (a note on the project itself, not on a record) |
| `tasks` | 4 of 8 |
| `addressings_to` | 5 of 8 |
| `attachments` | 5 of 8 |
| `replies` | 1 of 8 |
| `sg_note_type` | null on 7 |
| `created_by` | HumanUser 5, ApiUser 3 |

What transfers: notes hang off Assets and off the Project, not only Shots; half link a Task; most
carry an attachment; type is often unset; some authors are scripts.

## What the seed has to supply

The sandbox day (6 notes, 3 replies) proves shapes, not behaviour under load. To design the lead
view against something honest, the seed grows to:

- a few hundred notes over 30 to 60 records, distributed by a long tail (most records 0 to 2, a
  handful with 15 to 20);
- a third with nobody addressed, a third client-facing, statuses spread, `sg_note_type` unset on some;
- threads of 0 to 5 replies, with the last reply alternating between the artist and a reviewer;
- attachments on a third, including `annot_version_<id>.<frame>.png` frames;
- `tasks` linked on about half; links on Shots, Assets, Versions and the Project;
- created over several weeks, several authors, at least one script author and one retired one.

`created_at` cannot be authored over REST, so date spread is the authored layer's job on top of the
capture, as the brief already says for the artist's day.

## The gap that remains

No production site was measured. The corpus's fill-rate finding (`007_fill_rates`) and the forum
threads are the only evidence of what studios actually fill in, and the forum says the Review Notes
app links `tasks` while manual notes often don't. The page has to be built to survive every column
being empty, and the first thing to do with any real site it meets is to run this measurement.
