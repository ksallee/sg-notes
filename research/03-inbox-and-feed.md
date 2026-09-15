# What an artist gets told about: following, the Inbox, the activity stream, webhooks

Research pass, 2026-09-15. Official help text is largely unchanged across the renames, so archived
Shotgun pages are cited where only the archive is reachable. Official / user report / inference are
marked.

## 1. Auto-follow and addressing rules

**Following gates everything.** "In order to see updates in your Inbox, you need to first follow the
thing you're interested in."
([Inbox and following](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-scheduling-tasks/SG_Producer_pr_scheduling_tasks_pr_inbox_following_html.html)). [official]

**The only documented auto-follow is the Task.** "If you are assigned to a Task, you are
automatically following that Task." (same page; identical in the
[2020 archive](https://web.archive.org/web/2020/https://support.shotgunsoftware.com/hc/en-us/articles/219031268-Inbox-and-following)).
Nothing official says you also follow the Task's Shot/Asset, its Versions, or Notes on it.

- User report, wider claim: "if you are assigned to or in a group assigned to a task or in the
  reviewer fields, you automatically are following that shot/asset"
  ([t/18869, Jun 2024](https://community.shotgridsoftware.com/t/inbox-filters-and-conditions/18869)).
  Contradicted by [t/17071](https://community.shotgridsoftware.com/t/reviewer-notifications-following/17071),
  where reviewers do not auto-follow. Unverified; measure on the site. (Probe 066 measured the
  artist's follow list: 77 Tasks and 4 Notes, no Shots. Consistent with the docs.)
- "You must follow an entity for it to show up in My Following Settings"; a user saw Shot options
  only after manually following one Shot ([t/7899](https://community.shotgridsoftware.com/t/how-to-follow-an-entity/7899)).
  A fresh artist has only Task options.

**Three-layer preference stack.** Site Preferences → Entities (which creation events are
followable); Admin → Global Follow Settings; Account Settings → My Following Settings (creation events
on the left: new Note/Version/Publish; field updates on the right, e.g. status). (Inbox and following.)

**Addressing** does not make you follow anything in the docs. It feeds the email path ("Email me
whenever I receive a note", [Account settings](https://help.autodesk.com/cloudhelp/ENU/SG-Administrator/files/ar-manage-accounts-after-migrating/SG_Administrator_ar_manage_accounts_ar_account_settings_after_migrating_html.html))
and the Inbox item for the note. **Hard constraint:** notes created over the API produce Inbox items
for addressees only when attributed to a real user: "add the information 'scope' with the value
`sudo_as_login:...`, so every note created will appear in the inbox"
([t/15632, Jul 2022](https://community.shotgridsoftware.com/t/shotgrid-rest-api-create-a-note-using-rest-api-and-show-in-inbox/15632));
script users additionally need "Generate Events" enabled
([t/12047, Apr 2021, Autodesk staff](https://community.shotgridsoftware.com/t/event-log-new-version-events-missing/12047)).

## 2. What the Inbox shows, and its read model

"You receive updates in your Inbox based on two things: what you're following and your follow
settings." Item kinds: new Notes, Versions, Publishes, and field updates on followed entities.
Replies are answered inline via "Add a reply…". (Inbox and following.)

**Read model.** Selecting a message marks it read; right-click → Mark Read; Hide read, Mark all read,
Refresh. Underneath, `read_by_current_user` is a real per-user field, values "Read"/"Unread", usable
for sorting and conditional formatting ([Notes](https://help.autodesk.com/cloudhelp/ENU/SG-Supervisor-Artist/files/sa-review-approval/SG_Supervisor_Artist_sa_review_approval_sa_notes_html.html)).
Toggling it emits `Shotgun_Reading_Change` ([python-api Event Types](https://developers.shotgridsoftware.com/python-api/reference.html)).
Activity-stream updates carry a per-update `read` flag.

**Filtering.** Only by type: All Types / Notes / Version Creation / Publish Creation. No project
filter, no sender filter: "There isn't a direct inbox filtering system like you'd find on pages"
(t/18869).

**No "needs my action" vs FYI.** The nearest signals are Note status Open/Closed ("The 'Open' status
indicates that the Note has not yet been addressed", Notes page) and `read_by_current_user`.
[inference] "Awaiting my reply" must be derived.

## 3. The activity stream

`activity_stream_read()` "corresponds to the data that is displayed in the Activity tab for an entity"
([python-api reference](https://developers.shotgridsoftware.com/python-api/reference.html)). Params
`entity_type`, `entity_id`, `entity_fields`, `min_id`, `max_id`, `limit`. Returns
`earliest_update_id`, `latest_update_id`, `updates` "always returned in descending date order".

**update_type values.** Autodesk's own Toolkit renderer branches on `create`, `create_reply` and
`update`, and logs "Activity type not supported" for anything else
([activity_stream.py](https://raw.githubusercontent.com/shotgunsoftware/tk-framework-qtwidgets/master/python/activity_stream/activity_stream.py)).
(Probes 043 and 067 also measured `delete` with `meta.type` `entity_retirement`.)

**meta.type values.** `new_entity`, and `attribute_change` with `attribute_name`,
`field_data_type`, `old_value`, `new_value` ([REST API v1.1](https://developers.shotgridsoftware.com/rest-api/)).

**HumanUser stream = the Person record's own Activity tab, not a personal feed.** The endpoint is
the generic per-entity one; someone rebuilding People > History reported "I am able to get human_user
information via activity_stream, but there are far less entries" and was pointed at EventLogEntry
([t/17656, Jul 2023](https://community.shotgridsoftware.com/t/person-history-equivalent-via-rest-api/17656)).
**There is no public API for the Inbox feed itself.** [inference, high confidence; probe 066 agrees]

REST paging: `limit` defaults to 25, cap 500; `min_id` tops up, but "it is not guaranteed that this
endpoint will return all the records down from max_id to min_id".

## 4. Email and notification defaults

Two live options in Account Settings: "Email me whenever I receive a note" and "Email me whenever
there's an update to something I'm following". Everything else is "legacy, as of Flow Production
Tracking 5.0". No digest option is documented. Site defaults: "Subscribe to all emails" / "Subscribe
to my emails" ([Site Preferences](https://help.autodesk.com/cloudhelp/ENU/SG-Administrator/files/ar-site-configuration/SG_Administrator_ar_site_configuration_ar_site_preferences_html.html)).
"People will never receive notifications related to projects they're not allowed to view." Mail goes
via SES with a suppression list that silently kills delivery after a bounce (Account settings).

## 5. My Tasks as the product defines it

"My Tasks displays all the Tasks assigned to you in an easy to scan list. Clicking on a Task in your
queue loads up the Task's linked entity in the detail pane on the right." Toolbar: Sort, Filter, New
Task, search. The right pane's Activity tab is "the Task's Activity Stream… including Notes, Versions,
Publishes, and other important changes"
([My Tasks](https://help.autodesk.com/cloudhelp/ENU/SG-Producer/files/pr-scheduling-tasks/SG_Producer_pr_scheduling_tasks_pr_my_tasks_html.html)).
No documented default "status is not final" filter.

**`task_assignees` is the real field.** Autodesk's shipped Toolkit config queries
`[["task_assignees", "is", "{context.user}"]]` plus `[["task_assignees.Group.users", "is",
"{context.user}"]]` for group assignment
([tk-config-default2](https://raw.githubusercontent.com/shotgunsoftware/tk-config-default2/master/env/includes/settings/tk-multi-workfiles2.yml)).
`sg_assigned_to` is studio-custom; do not query it. Artist-controlled ordering: not found.

## 6. Webhooks and EventLogEntry as "what changed" sources

Event naming `Shotgun_[EntityType]_[New|Change|Retirement|Revival]`: `Shotgun_Task_Change`,
`Shotgun_Note_New`, `Shotgun_Version_New`, `Shotgun_Reply_New`
([event-daemon technical details](https://raw.githubusercontent.com/shotgunsoftware/developer.shotgunsoftware.com/master/docs/en/event-daemon/event-daemon-technical-details.md)).
Webhooks ([guide](https://github.com/shotgunsoftware/developer.shotgunsoftware.com/blob/master/docs/en/guides/webhooks.md))
subscribe to lifecycle events filtered by project, entity and field. Pitfalls, from the docs:

- "A Webhook delivery will not occur when subscribed to a field update for the initial creation
  operation of that entity." Derive "status set on create" from the New event.
- 6-second response deadline; slow consumers throttled to ~10 deliveries/min. Answer 200, process async.
- 1 MB payload cap strips `old_value`/`new_value`.
- 100 failed deliveries in 24h permanently stops the webhook; logs kept 7 days.
- EventLogEntry polling: id gaps are normal, abandoned after 5 minutes; studios report 40+ minute
  daemon lag ([t/3419](https://community.shotgridsoftware.com/t/event-daemon-slowness/3419)).
  "If your use case works with Webhooks, it should be the preferred solution."
- API-created entities emit no events unless the script has "Generate Events" (t/12047).
- The activity stream is unfilterable; one Version's PublishedFiles "instantly spam[s]" it
  ([t/15872](https://community.shotgridsoftware.com/t/exclude-entity-type-from-activity/15872)).

No published "feed of my day" was found. The closest is the Person-History thread, which landed on
EventLogEntry search.

## Implications for a one-screen artist page

1. **Fan out over the artist's Tasks' entities; there is no user feed.** Query Task where
   `task_assignees is me` or `task_assignees.Group.users is me` (Autodesk's own filter), collect the
   Tasks' Shots and Assets, and read each entity's stream with `min_id` from a local cache.
2. **Cache by id but overlap the window.** The docs disclaim completeness between `max_id` and
   `min_id`.
3. **Webhooks for freshness, the per-entity stream for rendering.** Treat `Shotgun_Task_Change`,
   `Shotgun_Note_New`, `Shotgun_Reply_New`, `Shotgun_Version_New` as invalidation signals.
4. **Render exactly the shapes Autodesk's own widget renders:** `create`, `create_reply`, `update`
   with `attribute_change`. Collapse `delete` and PublishedFile bursts.
5. **Build "waiting on my reply" yourself:** `addressings_to` has me, status Open, last Reply not
   mine; `read_by_current_user` for the bold affordance.
6. **"Since you left" is time-based, not follow-based.** A follow-derived feed is silently empty for
   most artists (t/7899, t/3240). Anchor on the stream ids over the task-derived entity set.
7. **Never write notes as a bare script user.** Attribute writes with `sudo_as_login` or the
   artist's own session, and have "Generate Events" on. Otherwise addressees get no Inbox item.
8. **Email is not the safety net.** Two options, no digest, silent suppression. The page has to be
   sufficient on its own.

## Sources

Official help: Inbox and following, My Tasks, Tasks and Pipeline Steps, Notes, Account settings, Site
Preferences (all cloudhelp `/files/…html`; the `help.autodesk.com/view/SGSUB/ENU/?guid=` form is a JS
shell). Developer: python-api reference, REST API v1.1, Webhooks guide, event-daemon technical
details, tk-framework-qtwidgets activity_stream, tk-config-default2. Forum: 18869, 17071, 17039,
15632, 15523, 15170, 12047, 7899, 3419, 3240, 17656, 15872. Archived Shotgun docs: Inbox and
following (2020-08-26), My Tasks (2019-10-01), Notes (2020-08-07).
