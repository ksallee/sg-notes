"""Snapshot the seeded month's responses into fixtures/live/, the groundtruth way: real shapes, offline.

    python tools/capture.py

Two views of one project. The artist's view is every Task assigned to them and the notes that reach
them; the lead's view is every note in the project with the records, people and events behind it.
Each is read as the person whose view it is, because `read_by_current_user` is per-person and means
nothing read as a script.

Every file is the parsed body the API answered, with three substitutions a machine can make safely:
the site host, e-mail addresses, and presigned media URLs, which expire in 900 s and are replaced by
a file under fixtures/media/ holding the bytes (field_types/image). Names are left as the seed wrote
them; the authored month (layer three, BRIEF.md) is where they change.
"""
import json
import re
import sys
from pathlib import Path

import requests

import _site

sys.path.insert(0, str(_site.GROUNDTRUTH / "probes"))
import _lib  # noqa: E402  the corpus scrubber: site host, emails, tokens

OUT = _site.ROOT / "fixtures" / "live"
MEDIA = _site.ROOT / "fixtures" / "media"
PENDING = "/images/status/transient/"

TASK_FIELDS = ["content", "sg_status_list", "due_date", "start_date", "sg_priority_1", "sg_description",
               "entity", "step", "project", "task_assignees", "updated_at", "created_at",
               "entity.Shot.image", "entity.Asset.image", "time_logs_sum", "est_in_mins"]
SHOT_FIELDS = ["code", "description", "image", "sg_status_list", "sg_sequence", "sg_shot_type", "updated_at"]
ASSET_FIELDS = ["code", "description", "image", "sg_status_list", "sg_asset_type", "updated_at"]
VERSION_FIELDS = ["code", "description", "sg_status_list", "image", "entity", "sg_task", "user",
                  "created_by", "created_at", "updated_at"]
NOTE_FIELDS = ["subject", "content", "sg_status_list", "sg_note_type", "client_note", "created_at",
               "updated_at", "created_by", "user", "addressings_to", "addressings_cc", "note_links",
               "tasks", "read_by_current_user", "attachments", "replies"]
PERSON_FIELDS = ["login", "name", "email", "image", "sg_status_list", "department", "groups",
                 "permission_rule_set", "firstname", "lastname"]
# EventLogEntry has 16 fields and every one is server-written; `audit_trail` is never returned and
# `meta` is the only one that says what changed (finding 025).
EVENT_FIELDS = ["event_type", "attribute_name", "description", "meta", "created_at", "entity",
                "user", "project", "session_uuid"]

EVENT_LIMIT = 400

THREAD_PARAMS = {"entity_fields[Note]": "sg_status_list,subject,client_note",
                 "entity_fields[Attachment]": "filename,image"}


class Capture:
    def __init__(self):
        self.e = _site.env()
        self.c = _site.client(self.e)
        self.project = _site.project_id(self.c, self.e)
        m = _site.read_manifest() or {}
        self.manifest = m
        # The people the last seed wrote as, else the env's person.
        self.login = m.get("artist_login") or (self.e.get("FPT_USER_LOGIN") or "").strip()
        self.me = _site.user_id(self.c, self.login)
        self.lead_login = m.get("supervisor_login") or ""
        self.artist_c = _site.client(self.e, as_login=self.login)
        self.lead_c = _site.client(self.e, as_login=self.lead_login) if self.lead_login else self.c
        self.media = {}         # url path -> local file
        self.threads = set()    # note ids already written
        self.written = set()    # every file this run produced, so the stale ones can go
        OUT.mkdir(parents=True, exist_ok=True)
        MEDIA.mkdir(parents=True, exist_ok=True)
        (OUT / "threads").mkdir(exist_ok=True)
        (OUT / "streams").mkdir(exist_ok=True)

    # -- media -----------------------------------------------------------------------------------

    def keep_media(self, obj, hint):
        """Replace every presigned media string under `obj` with a local path, downloading once.

        A file is named for the row that owns it: `<type>_<id>_<field>`, or the walker's hint where
        the dict has no type and id of its own (a dotted-path value on a Task, an update's author).
        """
        if isinstance(obj, dict):
            if isinstance(obj.get("id"), int) and isinstance(obj.get("type"), str):
                hint = f"{obj['type']}_{obj['id']}"
            for k, v in list(obj.items()):
                # Every absolute URL the API returns is media: `links.*` are root-relative (probe 006).
                # Thumbnails come back on S3 or on the site's own `/thumbnail/` route, so match neither.
                if isinstance(v, str) and v.startswith("http"):
                    obj[k] = self.fetch(v, f"{hint}_{k.split('.')[-1]}")
                else:
                    self.keep_media(v, hint)
        elif isinstance(obj, list):
            for x in obj:
                self.keep_media(x, hint)

    def fetch(self, url, name):
        if PENDING in url:
            return "pending"          # still transcoding: the value the page has to handle anyway
        key = url.split("?")[0]
        if key not in self.media:
            r = requests.get(url, timeout=60)
            ext = {"image/png": "png", "image/jpeg": "jpg"}.get(r.headers.get("Content-Type", ""), "bin")
            f = MEDIA / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', name)}.{ext}"
            f.write_bytes(r.content)
            self.written.add(f)
            self.media[key] = f"media/{f.name}"
        return self.media[key]

    # -- files -----------------------------------------------------------------------------------

    def save(self, name, body):
        text = json.dumps(body, indent=1, sort_keys=True)
        text = _lib.scrub(text, self.e)
        (OUT / f"{name}.json").write_text(text + "\n")
        self.written.add(OUT / f"{name}.json")
        print(f"  {name}.json")

    def rows(self, slug, filters, fields, sort=None, c=None):
        """One page, saved whole: the caller edits the rows the file holds."""
        r = (c or self.c).post(f"/entity/{slug}/_search", headers=_site.ARR, json={
            "filters": filters, "fields": fields, "page": {"size": 200}, **({"sort": sort} if sort else {})})
        body = r.json() if r.ok else _site.ok(r, f"search {slug}")
        return body["data"], body

    def all_rows(self, slug, filters, fields, sort=None, c=None, limit=None):
        """Every page, in a body of the same shape."""
        data = _site.search_all(c or self.c, slug, filters, fields, sort=sort, limit=limit)
        return data, {"data": data}

    def in_project(self, *extra):
        return [["project", "is", {"type": "Project", "id": self.project}], *extra]

    def thread(self, note_id):
        if note_id in self.threads:
            return
        self.threads.add(note_id)
        body = self.c.get(f"/entity/notes/{note_id}/thread_contents", params=THREAD_PARAMS).json()
        self.keep_media(body, f"Note_{note_id}_thread")
        text = _lib.scrub(json.dumps(body, indent=1, sort_keys=True), self.e)
        (OUT / "threads" / f"{note_id}.json").write_text(text + "\n")
        self.written.add(OUT / "threads" / f"{note_id}.json")

    # -- the two views ---------------------------------------------------------------------------

    def artist_view(self):
        print(f"\n# the artist's view, read as {self.login}")
        me_body = self.c.get(f"/entity/human_users/{self.me}",
                             params={"fields": "login,name,image,email"}).json()
        self.keep_media(me_body, f"HumanUser_{self.me}")
        self.save("me", me_body)

        # The page's root query: Autodesk's own My Tasks filter (research/03 §5), scoped to the project.
        tasks, body = self.rows("tasks", self.in_project(
            ["task_assignees", "is", {"type": "HumanUser", "id": self.me}]), TASK_FIELDS, sort="due_date")
        for t in tasks:
            self.keep_media(t, f"Task_{t['id']}_entity")
        self.save("tasks", body)

        ents = {}
        for t in tasks:
            e = (t["relationships"].get("entity") or {}).get("data")
            if e:
                ents[(e["type"], e["id"])] = e
        for typ, slug, fields in (("Shot", "shots", SHOT_FIELDS), ("Asset", "assets", ASSET_FIELDS)):
            ids = [e["id"] for e in ents.values() if e["type"] == typ]
            if ids:
                rows, body = self.rows(slug, [["id", "in", ids]], fields)
                for x in rows:
                    self.keep_media(x, f"{typ}_{x['id']}")
                self.save(slug, body)

        # Versions attach from their own side (entity_types/Shot): filter the child on the parents.
        versions, body = self.all_rows("versions", self.in_project(["entity", "in", list(ents.values())]),
                                       VERSION_FIELDS, sort="-created_at")
        for v in versions:
            self.keep_media(v, f"Version_{v['id']}")
        self.save("versions", body)

        # Notes reach the artist three ways (research/02, implication 2); one search each, merged, and
        # read as the artist so `read_by_current_user` is theirs.
        seen, merged = set(), {"data": []}
        for label, f in (
            ("addressed", [["addressings_to", "is", {"type": "HumanUser", "id": self.me}]]),
            ("on my tasks", [["tasks", "in", [{"type": "Task", "id": t["id"]} for t in tasks]]]),
            ("on my entities", [["note_links", "in", list(ents.values())
                                 + [{"type": "Version", "id": v["id"]} for v in versions]]]),
        ):
            rows, _ = self.all_rows("notes", self.in_project(*f), NOTE_FIELDS, sort="-created_at",
                                    c=self.artist_c)
            print(f"  notes {label}: {len(rows)}")
            for n in rows:
                if n["id"] not in seen:
                    seen.add(n["id"])
                    merged["data"].append(n)
        self.save("notes", merged)

        # The feed: one stream per Shot or Asset behind my tasks, never the user's own (probe 066).
        for (typ, i), e in ents.items():
            slug = {"Shot": "shots", "Asset": "assets"}[typ]
            body = self.c.get(f"/entity/{slug}/{i}/activity_stream", params={
                "limit": 100, "entity_fields[Task]": "sg_status_list,due_date,task_assignees",
                "entity_fields[Version]": "sg_status_list,image,sg_task",
                "entity_fields[Note]": "sg_status_list,addressings_to,tasks"}).json()
            self.keep_media(body, f"stream_{typ}_{i}")
            self.save(f"streams/{typ}_{i}", body)

        self.save("following", self.c.get(f"/entity/human_users/{self.me}/following",
                                          params={"project_id": self.project}).json())

    def lead_view(self):
        print(f"\n# the lead's view, read as {self.lead_login or 'the script user'}")
        notes, body = self.all_rows("notes", self.in_project(), NOTE_FIELDS, sort="-created_at",
                                    c=self.lead_c)
        self.save("project-notes", body)
        print(f"  {len(notes)} notes in the project")

        # Everything the notes point at, so the list can draw a row without a second call.
        linked = {}
        for n in notes:
            for field in ("note_links", "tasks"):
                for e in (n["relationships"].get(field) or {}).get("data") or []:
                    linked.setdefault(e["type"], set()).add(e["id"])
        for typ, slug, fields in (("Shot", "project-shots", SHOT_FIELDS),
                                  ("Asset", "project-assets", ASSET_FIELDS),
                                  ("Version", "project-versions", VERSION_FIELDS),
                                  ("Task", "project-tasks", TASK_FIELDS)):
            ids = sorted(linked.get(typ, ()))
            rows, body = self.all_rows(slug.split("-")[1], [["id", "in", ids]], fields) if ids \
                else ([], {"data": []})
            for x in rows:
                self.keep_media(x, f"{typ}_{x['id']}")
            self.save(slug, body)
            print(f"  {len(rows)} {typ}s the notes point at")

        # Everyone a note names, plus the project's own members, for pickers and avatars.
        # HumanUser has no `project`: membership is the plural `projects` (entity_types/HumanUser).
        people = {u["id"] for u in _site.search_all(
            self.c, "human_users", [["projects", "is", {"type": "Project", "id": self.project}]], ["id"])}
        for n in notes:
            for field in ("created_by", "user"):
                e = (n["relationships"].get(field) or {}).get("data")
                if e and e["type"] == "HumanUser":
                    people.add(e["id"])
            for field in ("addressings_to", "addressings_cc"):
                for e in (n["relationships"].get(field) or {}).get("data") or []:
                    if e["type"] == "HumanUser":
                        people.add(e["id"])
        rows, body = self.all_rows("human_users", [["id", "in", sorted(people)]], PERSON_FIELDS)
        for x in rows:
            self.keep_media(x, f"HumanUser_{x['id']}")
        self.save("people", body)
        print(f"  {len(rows)} people")

        for n in notes:
            self.thread(n["id"])
        print(f"  {len(self.threads)} thread_contents under live/threads/")

        self.events()

    def events(self):
        """The project's event log since the seed started.

        Entry timestamps cannot be authored, so this window only ever holds the seed's own writes and
        anything done on the site since: "what changed" is measurable forward from a seed, never
        backward over it (finding 025).
        """
        since = self.manifest.get("started_at") or f"{self.manifest.get('today', '1970-01-01')}T00:00:00Z"
        # One create writes one row per field (finding 049), so a seed of this size fills the log.
        # Newest first, capped: the head is the part a "what changed since" view reads.
        rows, body = self.all_rows("event_log_entries",
                                   self.in_project(["created_at", "greater_than", since]),
                                   EVENT_FIELDS, sort="-id", limit=EVENT_LIMIT)
        self.save("events", body)
        kinds = {}
        for r in rows:
            kinds[r["attributes"]["event_type"]] = kinds.get(r["attributes"]["event_type"], 0) + 1
        print(f"  {len(rows)} event log entries since {since}")
        for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])[:8]:
            print(f"    {v:>6}  {k}")

    def sweep(self):
        """Drop what an earlier capture left behind: fixtures/ holds one site, not a history."""
        stale = [f for d in (MEDIA, OUT / "threads", OUT / "streams")
                 for f in d.iterdir() if f.is_file() and f not in self.written]
        for f in stale:
            f.unlink()
        print(f"{len(stale)} stale files removed")

    def run(self):
        self.artist_view()
        self.lead_view()
        self.sweep()
        print(f"{len(self.media)} media files under fixtures/media/")


if __name__ == "__main__":
    Capture().run()
