"""Snapshot the seeded day's responses into fixtures/live/, the groundtruth way: real shapes, offline.

    python tools/capture.py

Reads as the script user, for the artist named by FPT_USER_LOGIN, in the sandbox project. Every file
is the parsed body the API answered, with three substitutions a machine can make safely: the site
host, e-mail addresses, and presigned media URLs, which expire in 900 s and are replaced by a file
under fixtures/media/ holding the bytes (field_types/image). Names are left as the seed wrote them;
the authored day (layer three, BRIEF.md) is where they change.
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
NOTE_FIELDS = ["subject", "content", "sg_status_list", "sg_note_type", "created_at", "updated_at",
               "created_by", "user", "addressings_to", "addressings_cc", "note_links", "tasks",
               "read_by_current_user", "attachments", "replies"]


class Capture:
    def __init__(self):
        self.e = _site.env()
        self.c = _site.client(self.e)
        self.project = _site.project_id(self.c, self.e)
        self.login = (self.e.get("FPT_USER_LOGIN") or "").strip()
        self.me = _site.user_id(self.c, self.login)
        self.media = {}         # url path hash -> local file
        OUT.mkdir(parents=True, exist_ok=True)
        MEDIA.mkdir(parents=True, exist_ok=True)

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
            self.media[key] = f"media/{f.name}"
        return self.media[key]

    # -- files -----------------------------------------------------------------------------------

    def save(self, name, body):
        text = json.dumps(body, indent=1, sort_keys=True)
        text = _lib.scrub(text, self.e)
        (OUT / f"{name}.json").write_text(text + "\n")
        print(f"  {name}.json")

    def rows(self, slug, filters, fields, sort=None):
        r = self.c.post(f"/entity/{slug}/_search", headers=_site.ARR, json={
            "filters": filters, "fields": fields, "page": {"size": 200}, **({"sort": sort} if sort else {})})
        body = r.json() if r.ok else _site.ok(r, f"search {slug}")
        return body["data"], body      # one parse: the rows the caller edits are the rows saved

    def run(self):
        me_body = self.c.get(f"/entity/human_users/{self.me}", params={"fields": "login,name,image,email"}).json()
        self.keep_media(me_body, f"HumanUser_{self.me}")
        self.save("me", me_body)

        # The page's root query: Autodesk's own My Tasks filter (research/03 §5), scoped to the project.
        tasks, body = self.rows("tasks", [["task_assignees", "is", {"type": "HumanUser", "id": self.me}],
                                          ["project", "is", {"type": "Project", "id": self.project}]],
                                TASK_FIELDS, sort="due_date")
        for t in tasks:
            self.keep_media(t, f"Task_{t['id']}_entity")
        self.save("tasks", body)

        ents = {}
        for t in tasks:
            e = (t["relationships"].get("entity") or {}).get("data")
            if e:
                ents[(e["type"], e["id"])] = e
        shots = [e["id"] for e in ents.values() if e["type"] == "Shot"]
        assets = [e["id"] for e in ents.values() if e["type"] == "Asset"]
        if shots:
            rows, body = self.rows("shots", [["id", "in", shots]], SHOT_FIELDS)
            for x in rows:
                self.keep_media(x, f"Shot_{x['id']}")
            self.save("shots", body)
        if assets:
            rows, body = self.rows("assets", [["id", "in", assets]], ASSET_FIELDS)
            for x in rows:
                self.keep_media(x, f"Asset_{x['id']}")
            self.save("assets", body)

        # Versions attach from their own side (entity_types/Shot): filter the child on the parents.
        vfilters = [["project", "is", {"type": "Project", "id": self.project}],
                    ["entity", "in", list(ents.values())]]
        versions, body = self.rows("versions", vfilters, VERSION_FIELDS, sort="-created_at")
        for v in versions:
            self.keep_media(v, f"Version_{v['id']}")
        self.save("versions", body)

        # Notes reach the artist three ways (research/02, implication 2); one search each, merged.
        seen, merged = set(), {"data": []}
        for label, f in (
            ("addressed", [["addressings_to", "is", {"type": "HumanUser", "id": self.me}]]),
            ("on my tasks", [["tasks", "in", [{"type": "Task", "id": t["id"]} for t in tasks]]]),
            ("on my entities", [["note_links", "in", list(ents.values())
                                 + [{"type": "Version", "id": v["id"]} for v in versions]]]),
        ):
            rows, body = self.rows("notes", [["project", "is", {"type": "Project", "id": self.project}], *f],
                                   NOTE_FIELDS, sort="-created_at")
            print(f"  notes {label}: {len(rows)}")
            for n in rows:
                if n["id"] not in seen:
                    seen.add(n["id"])
                    merged["data"].append(n)
        self.save("notes", merged)

        (OUT / "threads").mkdir(exist_ok=True)
        for n in merged["data"]:
            body = self.c.get(f"/entity/notes/{n['id']}/thread_contents",
                              params={"entity_fields[Note]": "sg_status_list,subject",
                                      "entity_fields[Attachment]": "filename,image"}).json()
            self.keep_media(body, f"Note_{n['id']}_thread")
            self.save(f"threads/{n['id']}", body)

        # The feed: one stream per Shot or Asset behind my tasks, never the user's own (probe 066).
        (OUT / "streams").mkdir(exist_ok=True)
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
        print(f"\n{len(self.media)} media files under fixtures/media/")


if __name__ == "__main__":
    Capture().run()
