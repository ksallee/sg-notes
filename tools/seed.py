"""Seed a lead's month into the sandbox project, through the real API.

    python tools/seed.py                          # dry run: resolve ids, print the plan, write nothing
    python tools/seed.py --write --supervisor LOGIN [--artist LOGIN] [--artist2 LOGIN]
    python tools/seed.py --clean                  # delete every row in fixtures/seed-manifest.json
    python tools/seed.py --markdown --write       # rewrite the bodies of the rows it already made

Three layers make the demo (BRIEF.md, "Simulating a site"). This is the first: real rows, real
shapes, real activity-stream entries. `tools/_plan.py` builds the month from a fixed random seed, so
the same anchor date produces the same site; this file only executes it.

Notes and replies are written as people through `sudo_as_login`, never as the bare script, except for
a handful deliberately left to the script user: a script's Note reaches no stream and no Inbox
(finding 067), which is a shape the page has to render.

Bodies carry markdown on a share of the notes and replies: a Note and a Reply render GitHub Flavored
Markdown on the site, and a review note uses it. `--markdown` rewrites the content of the rows in the
manifest in place, so a sandbox that was seeded before does not double.

`created_at` is sent on every create and read back exactly, so the month has a month's spread.
Event-log timestamps cannot be authored, so a run ends with a pass of mutations: those are the only
changes "what changed since" can see (finding 025).

Only the project named by FPT_PROBE_SANDBOX_PROJECT is written. Never the demo project.
"""
import argparse
import datetime as dt
import json
import re
import sys
import time

import _plan
import _site

TODAY = dt.date.today()
FIELD_IN_ERROR = re.compile(r"\b[A-Z][A-Za-z]*\.([a-z_]+)")
# A 400 that names no field. The site refuses the flag on create and says so in English.
REFUSED_BY_MESSAGE = {"Client Notes can not be created through the API": "client_note"}
SECOND_ARTIST_NAME = "Other Artist"


class Seed:
    def __init__(self, e, supervisor, artist="", artist2=""):
        self.e = e
        self.script = _site.client(e)
        self.project = _site.project_id(self.script, e)
        self.logins = {}
        self.users = {}
        self.clients = {"script": self.script}

        artist = artist or (e.get("FPT_USER_LOGIN") or "").strip()
        if not artist:
            raise SystemExit("set FPT_USER_LOGIN in sg-groundtruth/.env.local, or pass --artist")
        self._person("artist", artist)
        self._person("artist2", artist2 or self._by_name(SECOND_ARTIST_NAME))
        if supervisor:
            self._person("sup", supervisor)
        else:
            self.clients["sup"] = self.script
            self.logins["sup"] = ""
            self.users["sup"] = None

        self.plan = _plan.build(TODAY, list(self.clients))
        self.made = []          # [slug, id, label], creation order
        self.ids = {}           # plan key -> {type, id}
        self.dropped = set()    # fields this site refuses on create
        self.steps = self._steps()
        self.started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.read_marks = None    # each set once the site's first answer says whether the field
        self.client_notes = None  # is writable, and never attempted again once it is not

    # -- resolution -----------------------------------------------------------------------------

    def _person(self, role, login):
        self.logins[role] = login
        self.users[role] = _site.user_id(self.script, login)
        self.clients[role] = _site.client(self.e, as_login=login)

    def _by_name(self, name):
        rows = _site.search(self.script, "human_users", [["name", "is", name]], ["login"])
        if not rows:
            raise SystemExit(f"no HumanUser named {name!r}: pass --artist2 with a login")
        return rows[0]["attributes"]["login"]

    def _steps(self):
        rows = _site.search(self.script, "steps", [], ["code", "entity_type"], size=200)
        out = {}
        for s in rows:
            key = (s["attributes"]["code"], s["attributes"]["entity_type"])
            out.setdefault(key, s["id"])     # lowest id wins where a site has duplicates
        return out

    def who(self, role):
        return self.clients[role]

    def ref(self, key):
        return self.ids[key]

    def user_ref(self, role):
        return {"type": "HumanUser", "id": self.users[role]}

    # -- writes ---------------------------------------------------------------------------------

    def create(self, c, slug, body, key, type_name, quiet=False):
        """A create that drops any field this site refuses, once, and never sends it again.

        An unknown or read-only field is a 400 naming the field (`endpoints-records-post`), so the
        site itself says which of the optional fields it will take.
        """
        body = {"project": {"type": "Project", "id": self.project},
                **{k: v for k, v in body.items() if k not in self.dropped}}
        for _ in range(4):
            r = c.post(f"/entity/{slug}", headers=_site.JSON, json=body)
            if r.ok:
                break
            field = self._refused(r, body)
            if field is None:
                raise SystemExit(f"create {slug} {key} -> {r.status_code} {r.text[:400]}")
            print(f"  ! this site refuses {slug}.{field} on create; dropping it for the rest of the run")
            self.dropped.add(field)
            body.pop(field)
        else:
            raise SystemExit(f"create {slug} {key} -> {r.status_code} {r.text[:400]}")
        d = r.json()["data"]
        self.made.append([slug, d["id"], key])
        self.ids[key] = {"type": type_name, "id": d["id"]}
        if not quiet:
            print(f"  {type_name:<9} {d['id']:>6}  {key}")
        return d

    def _refused(self, r, body):
        if r.status_code != 400:
            return None
        for message, field in REFUSED_BY_MESSAGE.items():
            if message in r.text and field in body:
                return field
        for name in FIELD_IN_ERROR.findall(r.text):
            if name in body and name not in ("project",):
                return name
        return None

    def put(self, c, slug, i, patch, label, quiet=False):
        r = c.put(f"/entity/{slug}/{i}", headers=_site.JSON, json=patch)
        _site.ok(r, f"update {slug}/{i} {label}")
        if not quiet:
            print(f"  {slug:<9} {i:>6}  {label}: {json.dumps(patch)}")

    def thumb(self, c, slug, i, code):
        _site.upload(c, slug, i, "image", f"{code}.png", _site.png(code))

    # -- passes ---------------------------------------------------------------------------------

    def membership(self):
        """An Artist-permission account sees only the projects it is on: 400 "project [N] can not be
        accessed by this user" otherwise. Add mode, so nobody else on the project is touched
        (recipes/009). Membership is not a row, so --clean leaves it."""
        on = {p["id"] for p in self.script.get(
            f"/entity/projects/{self.project}", params={"fields": "users"}
        ).json()["data"]["relationships"]["users"]["data"]}
        missing = [self.users[r] for r in ("artist", "artist2") if self.users[r] not in on]
        if not missing:
            return
        self.put(self.script, "projects", self.project, {
            "users": {"multi_entity_update_mode": "add",
                      "value": [{"type": "HumanUser", "id": i} for i in missing]}},
            "artists added to the project")

    def entities(self):
        print("\n# sequence, shots, assets")
        for s in self.plan["sequences"]:
            self.create(self.script, "sequences", {"code": s["code"], "description": s["description"]},
                        s["code"], "Sequence")
        for s in self.plan["shots"]:
            self.create(self.script, "shots", {
                "code": s["code"], "description": s["description"], "sg_shot_type": "VFX",
                "sg_status_list": s["status"],
                "sg_sequence": self.ref(s["sequence"])}, s["code"], "Shot")
            self.thumb(self.script, "shots", self.ids[s["code"]]["id"], s["code"])
        for a in self.plan["assets"]:
            self.create(self.script, "assets", {
                "code": a["code"], "description": a["description"], "sg_asset_type": a["kind"],
                "sg_status_list": a["status"]}, a["code"], "Asset")
            self.thumb(self.script, "assets", self.ids[a["code"]]["id"], a["code"])

    def tasks(self):
        # The script creates Tasks: a coordinator's job, and the Artist permission set refuses it
        # (400 "Entity of type Task cannot be created by this user").
        print(f"\n# {len(self.plan['tasks'])} tasks, assigned to the two artists")
        for i, t in enumerate(self.plan["tasks"]):
            ent = self.ref(t["entity"])
            step = self.steps.get((t["step"], ent["type"]))
            if step is None:
                raise SystemExit(f"no Step {t['step']} for {ent['type']} on this site")
            self.create(self.script, "tasks", {
                "content": t["step"], "entity": ent, "step": {"type": "Step", "id": step},
                "task_assignees": [self.user_ref(t["assignee"])],
                "sg_status_list": t["status"], "due_date": t["due"],
                "sg_priority_1": t["priority"], "sg_description": t["description"],
                "created_at": t["created_at"]}, t["key"], "Task", quiet=i % 10)
        print(f"  {len(self.plan['tasks'])} tasks")

    def versions(self):
        print(f"\n# {len(self.plan['versions'])} versions, submitted by their task's assignee")
        thumbed = 0
        for i, v in enumerate(self.plan["versions"]):
            c = self.who(v["user"])
            self.create(c, "versions", {
                "code": v["code"], "entity": self.ref(v["entity"]),
                "sg_task": self.ref(v["task"]), "user": self.user_ref(v["user"]),
                "sg_status_list": v["status"], "description": v["description"],
                "created_at": v["created_at"]}, v["code"], "Version", quiet=True)
            # Media on a live site is a transcode behind the row, so a share of the Versions carry no
            # image at all: the "No Playable Media" shape (research/08 §2) the page has to render.
            if i % 5 != 3:
                self.thumb(c, "versions", self.ids[v["code"]]["id"], v["code"])
                thumbed += 1
        print(f"  {len(self.plan['versions'])} versions, {thumbed} with a thumbnail")

    def notes(self):
        n = self.plan["notes"]
        print(f"\n# {len(n)} notes, {sum(len(x['replies']) for x in n)} replies, "
              f"{sum(len(x['attachments']) for x in n)} attachments")
        t0 = time.time()
        for i, note in enumerate(n):
            self._note(note)
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(n)} notes, {time.time() - t0:.0f}s")

    def _note(self, note):
        links = []
        if note["version"]:
            links = [self.ref(note["version"]), self.ref(note["record"])]
        elif note["record"]:
            links = [self.ref(note["record"])]
        elif note["kind"] == "project":
            # A Note about the project itself, not about a record. `Project` is absent from
            # `note_links.valid_types` and stored anyway (`entity_types/Note`); real projects hold them
            # (research/07).
            links = [{"type": "Project", "id": self.project}]
        body = {"subject": note["subject"], "content": note["content"], "note_links": links,
                "tasks": [self.ref(k) for k in note["tasks"]],
                "sg_status_list": note["status"], "client_note": note["client_note"],
                "created_at": note["created_at"]}
        if note["note_type"]:
            body["sg_note_type"] = note["note_type"]
        if note["to"]:
            body["addressings_to"] = [self.user_ref(r) for r in note["to"]]
        if note["cc"]:
            body["addressings_cc"] = [self.user_ref(r) for r in note["cc"]]
        key = f"note:{note['created_at']}:{note['subject']}"
        c = self.who(note["author"])
        d = self.create(c, "notes", body, key, "Note", quiet=True)
        note["_id"] = d["id"]
        if note["client_note"] and "client_note" in self.dropped:
            self.set_client_note(c, d["id"])

        for a in note["attachments"]:
            if a["annotation"]:
                # A legacy annotation is a burned-in frame attached to the Note, named for the Version
                # and the frame (research/08 §1).
                name = f"annot_version_{self.ref(a['version'])['id']}.{a['frame']}.png"
                label = f"annot {a['version']} {a['frame']}"
            else:
                name = f"{(note['record'] or 'note')}_{a['kind'].replace(' ', '_')}.png"
                label = f"{a['kind']} for {note['subject']}"
            _site.upload(c, "notes", d["id"], None, name, _site.png(label))

        for r in note["replies"]:
            body = {"entity": {"type": "Note", "id": d["id"]}, "content": r["content"],
                    "created_at": r["created_at"]}
            body = {k: v for k, v in body.items() if k not in self.dropped}
            resp = _site.ok(self.who(r["author"]).post("/entity/replies", headers=_site.JSON, json=body),
                            f"reply on {key}")
            self.made.append(["replies", resp["id"], f"reply:{note['subject']}:{r['author']}"])

        for role in note["read_by"]:
            self.mark_read(role, d["id"])

    def set_client_note(self, c, note_id):
        """`client_note` is refused on create; whether an update takes it is the site's to say."""
        if self.client_notes is False:
            return
        r = c.put(f"/entity/notes/{note_id}", headers=_site.JSON, json={"client_note": True})
        if not r.ok and self.client_notes is None:
            print(f"  ! client_note is not writable here either: {r.status_code} {r.text[:200]}")
            print("    client-facing notes carry sg_note_type Client and nothing else")
            self.client_notes = False
            return
        self.client_notes = r.ok

    def mark_read(self, role, note_id):
        """`read_by_current_user` is per-person, so a read mark is a write as that person."""
        if self.read_marks is False:
            return
        r = self.who(role).put(f"/entity/notes/{note_id}", headers=_site.JSON,
                               json={"read_by_current_user": "read"})
        if not r.ok and self.read_marks is None:
            print(f"  ! read_by_current_user is not writable here: {r.status_code} {r.text[:200]}")
            self.read_marks = False
            return
        self.read_marks = r.ok

    def mutate(self):
        """Changes written after every row exists: the only window the event log can measure."""
        m = self.plan["mutations"]
        print(f"\n# {len(m)} mutations, the window 'what changed since' can see")
        by_note = {f"note:{n['created_at']}:{n['subject']}": n for n in self.plan["notes"]}
        for change in m:
            if change["type"] == "note":
                subject, created = change["key"].rsplit("@", 1)
                note = by_note[f"note:{created}:{subject}"]
                c, i = self.who(note["author"]), note["_id"]
                slug = "notes"
            elif change["type"] == "task":
                c, i, slug = self.who("sup"), self.ref(change["key"])["id"], "tasks"
            else:
                c, i, slug = self.who("sup"), self.ref(change["key"])["id"], "versions"
            self.put(c, slug, i, {change["field"]: change["value"]}, change["key"], quiet=True)
        print(f"  {len(m)} rows changed")

    def attachments(self):
        """Uploads leave Attachment rows the delete of their parent does not remove (recipe 013).

        One search over the run's own window catches every one of them, note files and thumbnails
        alike, so --clean takes the site back to where it started.
        """
        print("\n# attachment rows, for --clean")
        rows = _site.search_all(self.script, "attachments",
                                [["project", "is", {"type": "Project", "id": self.project}],
                                 ["created_at", "greater_than", self.started]], ["filename"])
        for a in rows:
            self.made.append(["attachments", a["id"], f"attachment:{a['attributes'].get('filename')}"])
        print(f"  {len(rows)} attachments")

    def manifest(self):
        return {"project": self.project,
                "artist": self.users["artist"], "artist_login": self.logins["artist"],
                "artist2": self.users["artist2"], "artist2_login": self.logins["artist2"],
                "supervisor": self.users["sup"], "supervisor_login": self.logins["sup"],
                "seed": self.plan["seed"], "weeks": self.plan["weeks"],
                "started_at": self.started,
                "seeded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "today": TODAY.isoformat(),
                "refused_on_create": sorted(self.dropped),
                "client_note_writable": self.client_notes,
                "read_by_current_user_writable": self.read_marks,
                "created": self.made}


def markdown(e, write):
    """Rewrite the content of the notes and replies the manifest owns, in place.

    The plan is a pure function of its anchor date, so rebuilding it on the manifest's own `today`
    hands back the rows the last run wrote, in the order it wrote them: the manifest's notes and
    replies zip onto the plan's, label for label. Only `content` is sent, only on the ids the
    manifest names, and only on the rows the plan marks up. Nothing is created and nothing the seed
    does not own is read or touched.

    A Note and a Reply render GitHub Flavored Markdown on the site, so this is what a seeded month
    looks like once the bodies carry what a real review note carries.
    """
    m = _site.read_manifest()
    if not m:
        raise SystemExit("nothing to rewrite: no fixtures/seed-manifest.json")
    plan = _plan.build(dt.date.fromisoformat(m["today"]), ["script", "artist", "artist2", "sup"])
    rows = [r for r in m["created"] if r[0] in ("notes", "replies")]
    want = []
    for note in plan["notes"]:
        want.append(("notes", f"note:{note['created_at']}:{note['subject']}", note, note["author"]))
        for r in note["replies"]:
            want.append(("replies", f"reply:{note['subject']}:{r['author']}", r, r["author"]))
    if len(rows) != len(want):
        raise SystemExit(f"the manifest holds {len(rows)} notes and replies, the plan {len(want)}: "
                         "it was written by another plan and this pass will not guess the pairing")
    for (slug, i, label), (slug2, label2, _, _) in zip(rows, want):
        if (slug, label) != (slug2, label2):
            raise SystemExit(f"manifest {slug}/{i} is {label!r}, the plan says {label2!r}: "
                             "the rows do not line up and nothing has been written")

    marked = [(row[1], w) for row, w in zip(rows, want) if w[2]["markup"]]
    notes = sum(1 for i, w in marked if w[0] == "notes")
    print(f"project {m['project']}, manifest of {m['seeded_at']}")
    print(f"{notes} notes and {len(marked) - notes} replies carry markdown; "
          f"the other {len(rows) - len(marked)} rows stay plain prose")
    for kind, _ in _plan.MARKUP_MIX:
        ids = [i for i, w in marked if w[0] == "notes" and w[2]["markup"] == kind]
        print(f"  {kind:<11} {len(ids):>3} notes  {', '.join(str(i) for i in ids[:6])}"
              f"{' ...' if len(ids) > 6 else ''}")
    if not write:
        print("\ndry run. Pass --write to send these bodies.")
        return

    clients = {"script": _site.client(e)}
    for role, key in (("artist", "artist_login"), ("artist2", "artist2_login"), ("sup", "supervisor_login")):
        login = (m.get(key) or "").strip()
        clients[role] = _site.client(e, as_login=login) if login else clients["script"]

    print()
    t0, done, failed = time.time(), 0, []
    for i, (slug, label, row, role) in marked:
        r = clients[role].put(f"/entity/{slug}/{i}", headers=_site.JSON, json={"content": row["content"]})
        if r.ok:
            done += 1
        else:
            failed.append((slug, i, r.status_code, r.text[:200]))
            print(f"  ! {slug}/{i} -> {r.status_code} {r.text[:200]}")
        if slug == "notes":
            print(f"  Note      {i:>6}  {row['markup']:<11} {label.rsplit(':', 1)[-1]}")
    print(f"\n{done} of {len(marked)} rows rewritten in {time.time() - t0:.0f}s")
    if failed:
        raise SystemExit(f"{len(failed)} rows the site would not take")
    m["markdown"] = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                     "notes": notes, "replies": len(marked) - notes}
    _site.write_manifest(m)


def clean(e):
    m = _site.read_manifest()
    if not m:
        raise SystemExit("nothing to clean: no fixtures/seed-manifest.json")
    c = _site.client(e)
    rows = m["created"]
    gone = 0
    for n, (slug, i, label) in enumerate(reversed(rows)):
        r = c.delete(f"/entity/{slug}/{i}")
        gone += r.status_code == 204
        if r.status_code != 204 or n % 50 == 0:
            print(f"  {r.status_code}  {slug}/{i}  {label}")
    print(f"deleted {gone} of {len(rows)}")
    _site.MANIFEST.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write the rows; without it, print the plan")
    ap.add_argument("--clean", action="store_true", help="delete every row in the manifest and exit")
    ap.add_argument("--markdown", action="store_true",
                    help="rewrite the content of the notes and replies in the manifest, in place, "
                         "so the rows the seed already made carry the markdown the plan now writes")
    ap.add_argument("--artist", default="", metavar="LOGIN",
                    help="first artist's login; default FPT_USER_LOGIN")
    ap.add_argument("--artist2", default="", metavar="LOGIN",
                    help=f"second artist's login; default the HumanUser named {SECOND_ARTIST_NAME!r}")
    ap.add_argument("--supervisor", default="", metavar="LOGIN",
                    help="login the supervisor's notes and reviews are written as (sudo_as_login)")
    a = ap.parse_args()
    e = _site.env()
    if a.clean:
        return clean(e)
    if a.markdown:
        return markdown(e, a.write)
    if _site.read_manifest():
        raise SystemExit("fixtures/seed-manifest.json exists: run --clean first, the seed does not reuse rows")

    s = Seed(e, a.supervisor, a.artist, a.artist2)
    print(f"project {s.project}")
    for role in ("artist", "artist2", "sup"):
        print(f"  {role:<8} HumanUser {s.users[role]}  {s.logins[role] or 'the script user'}")
    if not s.users["sup"]:
        print("  no --supervisor: notes will not reach a stream (finding 067)")
    print(_plan.summary(s.plan))
    if not a.write:
        print("\ndry run. Pass --write to create these rows.")
        return
    t0 = time.time()
    try:
        s.membership()
        s.entities()
        s.tasks()
        s.versions()
        s.notes()
        s.mutate()
        s.attachments()
    finally:
        _site.write_manifest(s.manifest())
        print(f"\nmanifest: {_site.MANIFEST} ({len(s.made)} rows) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    sys.exit(main())
