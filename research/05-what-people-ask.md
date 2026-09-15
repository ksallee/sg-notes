# What people ask, and what has been built with LLMs on Flow PT

Research pass, 2026-09-15. Public web only; Reddit was blocked, so artist voices come from the Flow
PT community forum, Autodesk docs, MCP server READMEs and coordinator job specs. Quotes are the
source's words; other phrasings are the agent's normalisation. [official] / [user] / [inference].

## 1. The catalogue of asks

**Artist, read a fact**
1. "What am I supposed to work on next?" Verbatim: "Is it possible for artists to see a Priority
   field ... Either as a visual on the tile or as a way to sorting method?"
   ([t/7505, 2019](https://community.shotgridsoftware.com/t/display-priority-of-my-tasks/7505)). [user]
2. "What exactly am I meant to do on this task?" Verbatim: "We're trying to use the task description
   to send info to artists about what they need to do on a task. It would be very handy to see the
   description in the task card", then "So we still need a solution to this."
   ([t/9808, 2020](https://community.shotgridsoftware.com/t/adding-tasks-description-to-the-my-tasks-card/9808)). [user]
   The clearest unmet artist ask found.
3. "What's due / bid vs burned." My Tasks exists for this and is "too limited to customise"
   ([t/13582](https://community.shotgridsoftware.com/t/change-layout-my-task-page/13582)). [user]

**Artist, summarize / find**
4. "Summarize the dailies notes for me." Now an Autodesk feature (§3). [official]
5. "Did anyone reply to my note on sh010?" Only via Inbox + following; no "awaiting my reply" view. [inference]
6. "What changed on my shots since Friday?" Closest analogue: digests "every hour, day, or week"
   rather than "bombarding artists with alerts" ([GridFlow](https://gridflow.pro/blog/unlocking-shotgrids-full-potential/)). [vendor]
7. "Just show me the latest playable version." Verbatim: "anyone wanting to review media associated
   with a shot has to do a lot of clicking to see actual playable video"
   ([t/14304, Dec 2021](https://community.shotgridsoftware.com/t/how-to-streamline-the-review-process/14304)). [user]

**Artist, act / write / launch**
8. "Set my comp task to in progress": `set_status`, `assign_task` are first-class in every MCP
   server on these APIs ([ftrack-mcp](https://glama.ai/mcp/servers/huikku/ftrack-mcp)).
9. "Log 3 hours on this." Kitsu MCP example: "Add 4 hours of work on this task for today"
   ([kitsu-mcp-server](https://github.com/ingipsa/kitsu-mcp-server)); time logging is a long-running
   friction area ([t/997](https://community.shotgridsoftware.com/t/shotgun-time-logs-filter-artists-with-missing-logs/997)). [user]
10. "Open sh010 in Nuke." Verbatim: artists want to "open the application that will know that you are
    in the whole context" ([t/17351, May 2023](https://community.shotgridsoftware.com/t/action-menu-item-launch-task-in-given-context/17351));
    one MCP server launches DCCs scoped to an entity ([fpt-mcp](https://glama.ai/mcp/servers/abrahamADSK/fpt-mcp)).

**Lead / coordinator**
11. "Forward this client note to the artist who now owns the shot." Verbatim: "shotgrid should just
    add a forward note function"; the workaround is to "duplicate the note manually"
    ([t/15351](https://community.shotgridsoftware.com/t/how-can-i-forward-client-notes-to-artist/15351)). Coordinator
    job specs confirm the loop: daily task lists out, review notes captured and distributed, Flow PT
    kept current ([Framestore spec](https://framestore.recruitee.com/o/vfx-production-coordinator-speculative-applications-only)).
12. "What happened in the last 24 hours?" (Kitsu MCP `daily_progress_report`).
13. "Who's late / who hasn't logged / who needs work." A supervisor wants "a real-time look if they
    are hitting their quotas", "Revision Requests" and how many tasks "were marked final"
    ([t/3084, Sep 2019](https://community.shotgridsoftware.com/t/using-event-summary-page-to-track-my-artists-daily-work/3084)). [user]

**Supervisor / producer**
14. Cross-entity analytics. Verbatim: "Which Shot had the Task, that took the longest time to finish";
    "the json answer schema is not standarised, since the question determines, which connections
    should be there" ([t/19175, Aug 2024](https://community.shotgridsoftware.com/t/chatgpt-like-chatbot-with-shotgrid-data/19175)). [user]
15. Schedule what-ifs: shipped as Flow Generative Scheduling (§3). [official]

Most painful today [inference]: what to do on this task in priority order (1, 2); playable media in
one click (7); notes routed and replied (5, 11); time logging (9); multi-entity questions (14).

## 2. What has been built

- **rfletchr's ShotGrid MCP server** (Go, Jun 2026), deliberately read-only, with the API docs and
  operator reference embedded "so the LLM isn't guessing"
  ([t/20826](https://community.shotgridsoftware.com/t/shotgrid-mcp-server/20826)). Reaction: "Woooooow".
- **loonghao/shotgrid-mcp-server**: 40+ tools, CRUD, notes, playlists, thumbnails
  ([repo](https://github.com/loonghao/shotgrid-mcp-server)).
- **huikku/shotgrid-mcp**: ~15 curated tools, `summarize` server-side, every write takes `dry_run`,
  delete is retire + `revive` ([Glama](https://glama.ai/mcp/servers/huikku/shotgrid-mcp)).
- **abrahamADSK/fpt-mcp**: full Python API, Toolkit path resolution, DCC launching scoped to an
  entity, RAG over verified docs against "Invalid filter operators, wrong entity reference formats",
  a regex safety scan on every call; "not affiliated with Autodesk" ([Glama](https://glama.ai/mcp/servers/abrahamADSK/fpt-mcp)).
- **dcc-mcp-fpt**: 20+ typed tools ([repo](https://github.com/dcc-mcp/dcc-mcp-fpt)).
- Pre-MCP (2024): LangChain/RAG over dumps, and "dump everything into a Pandas Dataframe" (t/19175).
- **ftrack, Kitsu**: community MCP servers with the same tool shapes; **Ayon, Prism, Deadline,
  Anchorpoint**: no LLM assistant found.
- What users said about any of them: almost nothing. No field report of an LLM tool in use with
  artists exists in public. [inference]

## 3. Autodesk's AI direction

- **Flow Generative Scheduling**, shipped Jul 2024, producer-facing
  ([CG Channel](https://www.cgchannel.com/2024/07/autodesk-launches-flow-generative-scheduling/)).
- **AI Playlist Notes Summary (Beta)**, announced 7 May 2026, opt-in, off by default, admin-controlled;
  summary published back as a note on the playlist, grouped by step, artist or type; "each summary
  includes links back to the source notes for easy verification"
  ([t/20737](https://community.shotgridsoftware.com/t/new-feature-ai-playlist-notes-summary-beta/20737)).
- **Autodesk AI Assistant** is in preview for Maya/Fusion/Vault, not Flow PT. Flow PT's 2025–2026
  list is Animating in Context, Shared Playlists, unified Review, Gantt work: no conversational
  assistant, no "my day" ([2025 recap](https://adsknews.autodesk.com/en/news/what-autodesk-flow-delivered-for-media-entertainment-in-2025-and-why-it-matters/),
  [8.89 notes](https://community.shotgridsoftware.com/t/8-89-release-notes/20914)).

Don't rebuild: playlist summarisation, scheduling, review playback. Open ground: the person's own
day and the lead's loop. [inference]

## 4. Display and write confirmation

- Thumbnails are the unit of navigation; Flow PT distinguishes static, hover and click-to-play media
  ([t/3750](https://community.shotgridsoftware.com/t/supported-thumbnail-media-types/3750)). Text-only
  answers lose the thing artists navigate by.
- Cards need the body text: "half to a dozen lines of text checklist style" (t/9808).
- Every summary links back to its sources, with a rating control: Autodesk's own bar (t/20737).
- Aggregate server-side (`summarize`) rather than pulling rows (huikku/shotgrid-mcp).
- Writes: preview-then-commit with before→after diffs, `dry_run` "plan" and "preflight"; delete is
  retire + revive (huikku servers). Read-only is a legitimate v1 (t/20826).
- Ground the query layer: two projects added RAG purely to stop invented operators and fields.
- Digest, don't ping (GridFlow).

## Implications for an ask-driven page

Ten asks first, each with its shape: ranked card list with the description body; one expanded card;
grouped digest by entity; note-thread cards with an inline reply box; summary text with per-note
links; a thumbnail that plays; diff-preview-then-confirm for status; preview + confirm for time;
launch button on the card; compact date table. Lead with the two the product still refuses:
description on the card and priority at a glance. Never answer with a path or an id. Ship pre-joined
query shapes, not a text-to-query box. The lead view ("who's blocked, late, unlogged") is a near-free
second page off the same layer.
