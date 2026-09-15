# How review notes reach an artist (2023–2026)

Research pass, 2026-09-15. Every claim cited. **[official]** = Autodesk docs or blog, **[practice]** =
forum or user report, **[inference]** = reasoning from those.

## 1. Creative Review in 2025–2026, and what it stores

**Timeline.** Creative Review entered public beta 27 May 2025
([t/20100](https://community.shotgridsoftware.com/t/autodesk-s-creative-review-public-beta-has-arrived/20100)),
consolidating Screening Room, the Media app, the Overlay Player and the Review Notes app
([t/20267](https://community.shotgridsoftware.com/t/new-review-experience-creative-review-on-flow-production-tracking/20267)).
It went GA on 29 June 2026, renamed **Review**
([t/20851](https://community.shotgridsoftware.com/t/introducing-review-in-flow-production-tracking/20851);
[Autodesk blog, 29 Jun 2026](https://blogs.autodesk.com/media-and-entertainment/2026/06/29/new-review-and-collaboration-tools-in-flow-production-tracking/)). [official]

**What it is.** Browser player with Hold/Ghost/Compare, frame-accurate annotation, notes, attachment
upload, related versions/playlists/cuts, and Live Review synced sessions RV users can join. [official]

**Note behaviour is still thin.** At beta launch: no note editing, no replying, no shape tools
(t/20100). Shape/text annotation tools landed 15 July 2026 (t/20851). Replies became *visible* in
the notes panel on 27 Aug 2026 (v0.227.9); *creating* replies and editing/deleting notes are "coming
in a future release" ([t/20913](https://community.shotgridsoftware.com/t/creative-review-public-beta-v0-227-9-released/20913)).
As of Sept 2026 an artist cannot answer a note from inside Review. [official]

**What it stores.** Standard Note entities linked to the Version, annotation images as note
attachments. "View annotations in the player" replays only annotations created inside Review, one
note at a time ([t/20611](https://community.shotgridsoftware.com/t/client-review-2026/20611)). RV
annotations cannot be viewed in Review ([t/20899](https://community.shotgridsoftware.com/t/how-to-show-annotations-in-rv/20899)).
The Notes Stream panel shows only versions of the same Task as the one viewed
([t/20499](https://community.shotgridsoftware.com/t/creative-review-notes-stream-request/20499)), and
notes opened via a playlist do not get linked to that Playlist
([t/20425](https://community.shotgridsoftware.com/t/creative-review-linking-for-notes/20425)). [practice]

## 2. The Note model as studios use it

Fields: `subject`, `content`, `note_links` (Version, Shot, Asset, Playlist), `tasks`,
`addressings_to`, `addressings_cc`, `sg_status_list`, `replies`, `attachments`, `client_note`
([python-api reference](https://developers.shotgridsoftware.com/python-api/reference.html);
[tk-framework-qtwidgets activity_stream](https://developers.shotgridsoftware.com/tk-framework-qtwidgets/activity_stream.html)). [official]

- **Status.** "A Note is typically created during a review session, with 'Open' status indicating the
  note has not yet been addressed, and after the Note is addressed, it is set to 'Closed'"
  ([Notes help](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_notes_html.html)).
  The Open Notes rollup on Shots/Assets keys off Open and is read-only
  ([t/14749](https://community.shotgridsoftware.com/t/shotgrid-open-notes/14749)). [official + practice]
- **Read/unread** is per user, field `read_by_current_user`; unread notes render bold; "Mark Selected
  as Read" in bulk (Notes help). [official]
- **Addressing is the permission boundary.** In the Vendor group, "if they are not in the `to` or `cc`
  field they should not be able to see notes on a version"
  ([t/16242](https://community.shotgridsoftware.com/t/notes-between-supervisors-hidden-from-the-artist/16242)). [practice]
- **Note→Task.** The Review Notes app links notes to Tasks via `tasks`
  ([Autodesk KB](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/When-using-the-Review-Notes-App-how-are-notes-linked-to-tasks-in-Flow-Production-Tracking.html)),
  but a Note's Tasks cannot be edited from a Notes page, and "It is not possible to change a Task
  Status from a Note's linked Tasks field" ([t/9165](https://community.shotgridsoftware.com/t/from-a-notes-page-can-i-edit-the-tasks-linked-to-my-notes/9165)). [practice]
- **Client notes.** `client_note` is set only at creation; replies to client notes are visible only to
  users with "Can See Client Notes"
  ([Client Notes and Replies](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-reviews/SG_Producer_pr_reviews_pr_client_notes_html.html)). [official]
- [inference] There is no native "resolved/answered" concept. The durable signals are
  `sg_status_list`, `read_by_current_user`, and whether the last Reply was authored by someone
  other than the artist.

## 3. Where an artist sees notes today

| Surface | What it shows | How it defines "needs me" |
|---|---|---|
| Inbox ([help](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-scheduling-tasks/SG_Producer_pr_scheduling_tasks_pr_inbox_following_html.html)) | Activity on followed entities; auto-follow on Task assignment; filter by type, hide read | Follow + unread. "There isn't a direct inbox filtering system like you'd find on pages" ([t/18869, Jun 2024](https://community.shotgridsoftware.com/t/inbox-filters-and-conditions/18869)) |
| Email / digests | Per-entity toggles in Account Settings; digests permission-gated ([Quick Start](https://www.autodesk.com/learn/ondemand/curated/flow-production-tracking-quick-start-guide/3xH9223TQHenCid0zOVXx)) | Following + @mention |
| Review Notes app summary email | One email per session to chosen recipients ([help](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-reviews/SG_Producer_pr_reviews_pr_review_notes_html.html)) | Recipient list at publish time |
| Notes tab / Open Notes on Shot, Asset, Version | Count and list of Open notes | Status = Open only |
| Review notes panel | Notes on the version; replies read-only | No "mine" filter; closed notes still listed ([t/20427](https://community.shotgridsoftware.com/t/note-stream-feedback-requests/20427)) |
| FPT Create (artist) | "A blue dot … indicates that there is unread feedback on that task" ([Create for Artists](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-create/SG_Supervisor_Artist_sa_create_sa_create_artists_html.html)) | Unread, per Task. The closest existing "needs my reply" |
| tk-multi-shotgunpanel | Activity stream + note reply widget, @-autocomplete, screen grab ([panel](https://github.com/shotgunsoftware/tk-multi-shotgunpanel)) | Entity context only |
| iOS Flow PT Review | Comments, annotated frames, camera images ([help](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-mobile-review/SG_Supervisor_Artist_sa_review_iphone_using_html.html)) | Version-centric |

## 4. Dailies conventions and the note→work loop

Playlists are "ordered lists of Versions" for review sessions, artist dropboxes, and sharing
([Media App and Playlists](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_media_app_playlists_html.html)).
Supervisors work from Review > Playlists with tabs like "Need to Review"; Versions default to
"Pending Review" ([review process tutorial](https://help.autodesk.com/cloudhelp/ENU/SG-Tutorials/files/SG_Tutorials_tu_review_process_html.html)).
Documented Version labels: Pending Review / Pending Director Review / Viewed / Final Approved; Shot:
In Progress / CBB / Omit / On Hold / Final Approved
([tracking statuses](https://help.autodesk.com/cloudhelp/ENU/SG-Tutorials/files/SG_Tutorials_tu_tracking_statuses_html.html)).
[inference] `rev/vwd/apr/cbb` are the codes behind those labels.

In Screening Room/RV: annotate → create a Note to commit the annotations; "Only annotations linked
to notes are committed" ([Autodesk KB](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Annotation-attached-to-wrong-Notes-in-ShotGrid-Screening-Room.html)).
The artist then submits a new Version from My Tasks, RV's Submit tool or Toolkit publish
([Submitting your work](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_submitting_work_html.html))
and flips Task/Version status by hand. [official] Closing the note is a convention, not an
automation; studios bolt on Event Daemon / webhook code, e.g. a checkbox that will "duplicate the
comment and make it an internal note. Then also put the task on retake"
([t/15351](https://community.shotgridsoftware.com/t/how-can-i-forward-client-notes-to-artist/15351)). [practice]

## 5. Annotations and attachments over the API

Annotations are Attachments linked to the Note. The frame number is in the filename:
`annot_version_<version_id>.<frame_number>.png`; "it's the `annot_version` prefix and the frame number
that seems to do the trick" ([t/7212, Feb 2020](https://community.shotgridsoftware.com/t/note-attachment-with-frame-number-python-api/7212));
no cleaner method as of Nov 2022 ([t/9363](https://community.shotgridsoftware.com/t/create-annotation-with-frame-overlay-via-the-api/9363)).
Attachments carry `link_type` upload / web (`rvlink://`, `cinesync://`) / local, and
`attachment_links` ([attachments cookbook](https://developers.shotgridsoftware.com/python-api/cookbook/attachments.html)).
REST exposes a note's image at `/api/v1.1/entity/note/{note_id}/image?alt=original|thumbnail`
([t/20592](https://community.shotgridsoftware.com/t/flow-production-tracking-rest-api-download-a-note-thumbnail/20592)).
[inference] A page can render annotation thumbnails and parse the frame from the filename, but
cannot get vector geometry.

## 6. Complaints and wishes

- "You should be able to reply to notes in Creative Review", plus @tagging and reactions "without
  creating formal note entities that require status tracking and closure"
  ([t/20375, Sep 2025](https://community.shotgridsoftware.com/t/creative-review-modernize-note-behavior/20375)).
- "Is it possible to have conditions / filter / sorting for the notes stream?" ([t/20427](https://community.shotgridsoftware.com/t/note-stream-feedback-requests/20427)).
- "the notes won't link to the playlist" ([t/20425](https://community.shotgridsoftware.com/t/creative-review-linking-for-notes/20425)).
- "Previous notes don't appear to be linked" ([t/20559, Nov 2025](https://community.shotgridsoftware.com/t/creative-review-beta-notes-could-not-be-sent/20559)).
- "The notes in activity list have only the playlist as visible link, which draws the note useless"
  ([t/16366, Nov 2022](https://community.shotgridsoftware.com/t/review-notes-in-activity/16366)).
- "shotgrid should just add a forward note function" (t/15351).
- "artists can see notes given to the other sequences that they are not assigned to"
  ([t/15878](https://community.shotgridsoftware.com/t/notes-and-seeing-only-assign-shots-sequences/15878)).
- Notes Stream scoped to one Task, not the whole Shot (t/20499).

## Implications for a one-screen artist page

1. **Build the "needs my reply" query yourself.** No surface offers it: the Inbox is follow-based with
   no conditions (t/18869); Open Notes is a read-only count keyed on status (t/14749).
2. **Definition, "a note waiting on my reply":** a Note where (a) it reaches me: I am in
   `addressings_to`, or I am assigned to a Task in `note.tasks`, or `note_links` holds a Version or
   Shot on a Task assigned to me; and (b) status is not `clsd`; and (c) the last event is not mine:
   `replies` is empty or the newest Reply's `user` is not me; and (d) `read_by_current_user` is the
   "new since I left" badge, not the gate. [inference], every component a queryable field.
3. **Rank "addressed to me" above "found via my Task".** Addressing is the permission boundary
   (t/16242); Task-derived hits are the long tail that goes missing.
4. **Reply is the highest-value action on the page.** Review cannot create replies as of Aug 2026
   (t/20913) and users are asking (t/20375).
5. **Pair every reply with a status control.** Note Open→Closed is the only "addressed" signal, and
   Task status cannot be changed from a Note in the stock UI (t/9165).
6. **Show annotation thumbnails inline, link out to Review for playback.** Fetch via the note image
   route (t/20592), parse the frame from the filename (t/7212).
7. **Group notes by Shot/Asset, not Task.** The Review stream is Task-scoped and users want the whole
   shot (t/20499); playlist links are unreliable (t/20425, t/16366).
8. **"What changed since I left" = Version status transitions plus new notes.** Dailies outcomes land
   as Version status, not as a message (review process tutorial).
9. **Flag orphan notes:** notes on my Versions with empty `tasks` and empty `addressings_to`. These are
   the ones studios lose (t/15351).

## Sources

help.autodesk.com/cloudhelp/ENU (SG-Supervisor-Artist, SG-Producer, SG-Tutorials, SG-Whats-New);
blogs.autodesk.com/media-and-entertainment (29 Jun 2026); community.shotgridsoftware.com topics
20100, 20267, 20375, 20425, 20427, 20499, 20559, 20592, 20611, 20851, 20899, 20913, 18869, 16242,
16366, 15351, 15878, 14749, 9165, 9363, 7212; developers.shotgridsoftware.com; github.com/shotgunsoftware.
The `help.autodesk.com/view/SGSUB/ENU/?guid=…` deep links are SPA routes that 404 to a fetcher;
content was reached through the cloudhelp `/files/…html` mirrors.
