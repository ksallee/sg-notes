# The artist's day in Flow PT, and what artists wish it did

Research pass, 2026-09-15. Web and community forum only; every claim carries its URL. Official
behaviour, user practice and inference are marked. Companion passes: `02-review-notes.md`,
`03-inbox-and-feed.md`.

Naming: Shotgun → ShotGrid (2021) → Flow Production Tracking (March 2024). Shotgun Desktop → Flow PT
Desktop. Artist docs still sit under `SG-Supervisor-Artist` paths and say "ShotGrid Create".

## 1. The artist's day, step by step

**Official.** The web My Tasks page "is intended to help Artists keep track of what they're working
on": assigned Tasks on the left, the linked Shot or Asset in a right-hand detail pane
([artist doc](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-create/SG_Supervisor_Artist_sa_create_sa_create_artists_html.html)).
A site preference, "In My Tasks show task link detail", decides whether the pane shows the Task or
the entity ([t/19951, Mar 2025](https://community.shotgridsoftware.com/t/add-versions-from-other-tasks-to-my-tasks/19951),
[t/20734, May 2026](https://community.shotgridsoftware.com/t/adding-new-version-to-automatically-link-to-the-artists-assigned-task/20734)).

In the Create-style artist view, tasks are thumbnails in three tabs, Active / Upcoming / Done, sorted
by due date by default, and "a blue dot on the top left of the thumbnail indicates that there is
unread feedback on that task" (same doc). Which statuses fall in which tab is a status→category
mapping, not artist-editable ([t/902, Sep 2019](https://community.shotgridsoftware.com/t/my-tasks-status-categories/902)).

**Start of day.** Open the Inbox: "The Inbox allows you to see activity on all the things that are
important to you and your work"; you are auto-followed on Tasks you're assigned to, reply inline via
"Add a reply…", filter by update type, hide read, right-click → Mark Read
([Inbox and following doc](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-scheduling-tasks/SG_Producer_pr_scheduling_tasks_pr_inbox_following_html.html)).

**Working.** Launch the DCC with context from Flow PT Desktop or the task thumbnail; in Maya/Nuke,
`tk-multi-workfiles2`'s first tab is My Tasks, "very reminiscent of the 'My Tasks' page on the Shotgun
website" ([wiki](https://github.com/shotgunsoftware/tk-multi-workfiles2/wiki/Documentation));
`tk-multi-shotgunpanel` docks entity data in-DCC with actions like `assign_task` and `play_in_rv`
([wiki](https://github.com/shotgunsoftware/tk-multi-shotgunpanel/wiki/Documentation)).

**End of day.** Upload a Version by drag-drop onto the task or `+Version`, optionally request
feedback, edit task or version status from the info panel, optionally log time (artist doc). A
one-click "Send for Review" from Maya shipped in 2020
([t/7739](https://community.shotgridsoftware.com/t/one-click-send-for-review-from-maya-to-shotgun-create/7739)).

## 2. Status vocabularies in practice

Shot/Task codes verbatim from a 2020 thread: wtg / rdy / ip / hld / omt / cbb / fin = Waiting to
Start, Ready to Start, In Progress, On Hold, Omit, CBB, Final
([t/4623](https://community.shotgridsoftware.com/t/fetching-entity-level-status-list/4623)).
Autodesk's sg-jira-bridge maps `wtg→To Do, rdy→Open, ip→In Progress, fin→Done, hld→Backlog,
omt→Closed` ([settings.py](https://github.com/shotgunsoftware/sg-jira-bridge/blob/master/settings.py)).
CBB = "Could Be Better": almost complete, finalled with the caveat it will be improved if time
permits ([VP Glossary](https://vpglossary.com/vesglossary/cbb/)).

Other entities carry their own vocabularies: Version = N/A, Pending Review, Pending Director Review,
Viewed, Final Approved; Note = Open, In Progress, Closed, and "Only 'Open' Notes are displayed in
certain places" ([statuses tutorial](https://help.autodesk.com/cloudhelp/ENU/SG-Tutorials/files/SG_Tutorials_tu_tracking_statuses_html.html)).
`rev` and `apr` are widespread practice, not in any official list found: user practice.

**Studio practice.** Statuses get chained: "We've linked Version statuses to Task statuses to Shot
Statuses", Shot for clients, Task for coordinators and artists, Version for artists and supervisors
([t/17368, May 2023; webhook status-mapping server open-sourced Jul 2025](https://community.shotgridsoftware.com/t/using-webhooks-to-overhaul-statuses/17368)).
Autodesk's shotgunEvents examples propagate Task status → Version status
([task_status_update_version_status.py](https://github.com/shotgunsoftware/shotgunEvents/blob/master/src/examplePlugins/task_status_update_version_status.py)).

**Inference.** "Ready to start" is mostly derived: dependencies cascade dates, not statuses
([Task Dependencies](https://developers.shotgridsoftware.com/python-api/cookbook/tasks/task_dependencies.html)),
so `rdy` is set by a coordinator or a webhook.

## 3. Priority and ordering

- Due date is the default My Tasks sort (artist doc).
- Priority is awkward: an admin can set My Tasks sort to any Task field except status-list fields,
  which is what Priority usually is ([t/7505, Feb 2020](https://community.shotgridsoftware.com/t/display-priority-of-my-tasks/7505)).
- Task order within a Pipeline Step is the `Sort Order` field
  ([t/10813](https://community.shotgridsoftware.com/t/managing-task-order-in-pipeline-view/10813)).
- Sorting is configured globally by admins, never per artist. The core complaint below.

## 4. What artists complain about and ask for

- **My Tasks is too rigid.** "We found that My Tasks is too limited in terms of customization and
  formatting, so we've created a custom page for our artists"
  ([t/15583, Jun 2022](https://community.shotgridsoftware.com/t/remove-my-tasks-link-from-top-toolbar/15583)).
- **No per-artist config.** "my main peeve with the My Tasks page is that it can only be configured
  globally rather than allowing each artist to make it their own, including filtering and sorting"
  ([t/767, Aug 2019](https://community.shotgridsoftware.com/t/sc-and-mytask-page-should-follow-same-ux-concepts/767)).
- **Grouping wastes the screen.** "when I sort my tasks by status they all group by shots as well,
  wasting a ton of screen estate" ([t/11304, Jan 2021](https://community.shotgridsoftware.com/t/my-tasks-page/11304)).
- **Just show me task + status.** "simplify it a bit so they know the assigned task and status in
  one go" ([t/13582, Sep 2021](https://community.shotgridsoftware.com/t/change-layout-my-task-page/13582)).
- **The card doesn't carry the brief.** "It would be very handy to see the description in the task
  card"; staff confirmed no card customization ([t/9808, Aug 2020](https://community.shotgridsoftware.com/t/adding-tasks-description-to-the-my-tasks-card/9808)).
- **Inbox overload.** "all Inboxes are at 99+"; "A digest feature would be great too"
  ([t/3501, 2019–2022](https://community.shotgridsoftware.com/t/open-discussion-what-makes-a-great-communication-notification-experience-with-shotgun/3501)).
  Inbox cannot be split per project; the workaround is a filtered Notes page
  ([t/11043](https://community.shotgridsoftware.com/t/organise-inbox/11043)).
- **Notes get lost in hand-offs.** "ShotGrid should just add a forward note function"
  ([t/15351, May 2022](https://community.shotgridsoftware.com/t/how-can-i-forward-client-notes-to-artist/15351)).
  Reviewers aren't auto-followed on tasks they review ([t/17071, Mar 2023](https://community.shotgridsoftware.com/t/reviewer-notifications-following/17071)).
- **No "awaiting feedback" state.** A category "for tasks that are awaiting feedback, somewhere
  between 'Active' and 'Done'" ([t/902](https://community.shotgridsoftware.com/t/my-tasks-status-categories/902)).
- **General UX.** "It just looks old and puts people off"
  ([t/13826, Oct 2021](https://community.shotgridsoftware.com/t/ux-in-sg-whats-the-plan/13826));
  asks for a customizable My Tasks alternative, Kanban-style ([t/442](https://community.shotgridsoftware.com/t/adoption-challenges/442)).
- **Submit friction, still in 2026.** "I want the task field in the popup window to be automatically
  filled with the task that's assigned to me" ([t/20734, May 2026](https://community.shotgridsoftware.com/t/adding-new-version-to-automatically-link-to-the-artists-assigned-task/20734)).
- **Time logging.** The web app doesn't prompt for a time log at version upload the way Create does
  ([t/19942, Mar 2025](https://community.shotgridsoftware.com/t/ability-to-add-a-time-log-at-version-creation/19942));
  artists forget to log time ([t/15281](https://community.shotgridsoftware.com/t/artist-is-forget-the-timelog/15281)).
- **Mobile.** No substantive forum discussion found. A gap, not evidence of absence.

## 5. One-click actions, ranked by how often they came up

1. Submit a version for review with the task pre-linked (t/20734, t/7739, artist docs).
2. Set task status from the card without opening the task (t/13582, artist docs).
3. Reply to or close a note, and forward it to the right artist (t/15351, Inbox doc).
4. Log time against the task, ideally at submit (t/19942, t/15281).
5. Open in the DCC with context (Flow PT Desktop, workfiles2 My Tasks tab).
6. Mark read / clear the blue dot on unread feedback (Inbox doc, artist doc).

## 6. Existing "artist dashboard" precedents

- **Per-project "Artist Homepage" custom pages.** "We've moved away from using My Tasks and instead
  create an Artist Homepage on each project that has views for Tasks/Notes/Reviews/Time Logs
  assigned-to or involving the Current User". Kept per project because a global page "would list
  entities for all projects, so may get crowded" ([t/17536, Jun 2023](https://community.shotgridsoftware.com/t/advanced-sorting-for-my-tasks/17536)).
- **Custom pages filtered to Current User** are the standard admin answer
  ([t/18786, May 2024](https://community.shotgridsoftware.com/t/how-to-add-tasks-in-dashboard-for-artists/18786)).
- **In-DCC panels**: tk-multi-shotgunpanel, workfiles2 My Tasks tab.
- **Third-party dashboards** exist commercially ([gridflow.pro, Jul 2025](https://gridflow.pro/blog/unlocking-shotgrids-full-potential/));
  Autodesk's 2026 framing is "build role-specific dashboards"
  ([Autodesk blog, Jul 2026](https://blogs.autodesk.com/media-and-entertainment/2026/07/01/choose-the-right-autodesk-flow-starting-point-for-your-production-bottleneck/)).

## Implications for a one-screen artist page

- One card per task with description, status, due date, priority and entity thumbnail on the card
  itself. The card is the top unmet ask (t/9808, t/13582).
- Sort and filter per artist and persistent, not a global admin setting (t/767, t/11304, t/17536).
- Default sort by due date, priority as a visible second signal; don't break on status-list-typed
  Priority fields (t/7505).
- Pre-fill the task on every submit dialog. Still broken in 2026 (t/20734).
- An explicit "awaiting feedback" lane between active and done (t/902).
- A per-project, note-first "waiting on you" list with mark-read and inline reply; digest, not
  firehose (t/3501, t/11043, Inbox doc).
- A "forward this note" action. No native equivalent (t/15351).
- Prompt for a time log at version submit (t/19942).
- The blue-dot unread-feedback convention artists already know from Create (artist doc).
- "What changed since I left" = status changes, new versions, new notes on my tasks: the four views
  the one studio-built Artist Homepage chose (t/17536).

## Caveats

Reddit was not fetchable, so no voices outside the Autodesk forum. No conference transcripts
surfaced. Mobile is a gap. `rev`/`apr` are unsourced officially. The Create-era artist docs are the
best official description of the artist screen, but Create's current shipping status is unconfirmed.
