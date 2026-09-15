# What sg-notes needs from the sg-widgets client

Drafts for issues on `../sg-widgets`, one per gap, found on 2026-09-15 while capturing the seeded
day. Each names the corpus entry the behaviour is measured in. Not filed yet.

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
