# What sg-notes needs from the sg-widgets client

Six gaps, found on 2026-09-15 while capturing the seeded day, each naming the corpus entry the
behaviour is measured in. Filed and shipped the same day: the reads (2, 3, 5, 6) as ksallee/sg-widgets#192,
merged to `dev` by #194; the writes (1, 4) as #193, merged by #195. `dev` awaits promotion to `main`.

What landed on `SgClient`:

    create(entityType, body): Promise<EntityRow>
    upload(entityType, id, {filename, data, field?}): Promise<UploadResult>
    threadContents(noteId, entityFields?): Promise<ThreadRow[]>
    eventLog(options?): Promise<EventLogResult>
    following(userId, {entity?, projectId?}): Promise<EntityRef[]>

Decided where the corpus was silent: `read_by_current_user` is forced to a `list` of `unread`/`read`
by a schema override, since what `/schema/Note/fields` declares for it was never read; the event log
sorts `-id` only; an upload through the proxy crosses base64 and runs server-side, since CORS on the
presigned `PUT` is unmeasured; `eventLog` is never cached.

Follow-ups the work surfaced, not filed: a widget that draws a thread; `Delivery.read_by_current_user`
needs its own probe; `SgClient` has no `delete`, and a Reply whose `entity` is null cannot be deleted
(report 005); multipart upload (044) has no path; nothing checks the upload's ETag; a create that also
uploads, as one call, if the app keeps repeating the pair.

## 1. `SgClient.create(entityType, body)`

`SgClient` has `update` and no `create`. A notes app's first write is a Reply, which is a `POST
/entity/replies` with `entity` set in the same call: a Reply created without `entity` is permanent
litter, it cannot be deleted (`entity_types/Reply`). Forwarding a note is a second create.
`project` is the whole create contract on Note and most types, and the schema's `mandatory` flags
are not the contract (`012_create_version`, `entity_types/Note`).

## 2. `SgClient.threadContents(noteId, entityFields?)`

`GET /entity/notes/<id>/thread_contents` returns Note, Attachment and Reply rows interleaved in
time order, the author under `created_by` on Note and Attachment and under `user` on Reply, and
`entity_fields[Reply]` is accepted and ignored (`get_entity_notes_id_thread_contents`). The mock
needs a thread shape too.

## 3. `SgClient.eventLog(options)`

`POST /entity/event_log_entries/_search` narrowed on `project`, `entity`, `event_type`,
`attribute_name` and `created_at`, sorted `-id`, with `old_value` and `new_value` read out of
`meta`, which is unfilterable (`025_event_log`). This is "what changed since", not the activity
stream: status changes over the API were absent from every stream 20 minutes on (`067`).

## 4. Upload

The three-call upload of `recipes/001`: a ticket from `GET …/_upload?filename=`, a `PUT` to the
presigned link with no auth header, then `POST complete_upload` with `upload_data: {}` and a body
that is one space. A field in the path picks the kind; no field is a generic Attachment. Needed
for a reply with a screenshot and for annotation frames.

## 5. `following(userId, {entity, projectId})`

`GET /entity/human_users/<id>/following`: unpaged, no `fields`, `links.self` spelled
`/entity/Note/346` (`get_entity_human_users_id_following`). The "mine" view uses it.

## 6. A `read_by_current_user` that is a string

The field reads `"unread"` and `"read"`, never a boolean (`067`). Wherever the widgets type a
checkbox from the schema, this one is a `list`.
