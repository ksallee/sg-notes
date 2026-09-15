"""Seed one believable artist's day into the sandbox project, through the real API.

    python tools/seed.py                          # dry run: resolve ids, print the plan, write nothing
    python tools/seed.py --write --supervisor LOGIN
    python tools/seed.py --clean                  # delete every row in fixtures/seed-manifest.json

Three layers make the demo (BRIEF.md, "Simulating activity"). This is the first: real rows, real
shapes, real activity-stream entries. Everything is created, then *mutated*, because only a mutation
writes an `update` row to a stream (probe 067). Notes and replies are written as people through
`sudo_as_login`, never as the bare script: a script's Note wrote no stream row at all (probe 067).

Only the project named by FPT_PROBE_SANDBOX_PROJECT is written. Never Big Buck Bunny.
"""
import argparse
import datetime as dt
import json
import sys
import time

import _site

TODAY = dt.date.today()


def day(offset):
    return (TODAY + dt.timedelta(days=offset)).isoformat()


# ---------------------------------------------------------------------------------------------------
# The day. Names are generated stand-ins; nothing here is a real show.
# `status` is the value the row ends on; rows are created on the default and moved there afterwards.
# ---------------------------------------------------------------------------------------------------

SEQUENCE = "sq010"
SHOTS = {
    "sq010_sh010": "Hero walks into the kitchen, practical lamp flickers",
    "sq010_sh020": "Reverse on the window, rain added in comp",
    "sq010_sh030": "Wide of the kitchen, full CG lamp",
    "sq010_sh040": "Insert on the lamp switch",
}
ASSETS = {
    "charA": ("Character", "Hero character, look-dev approved"),
    "env_kitchen": ("Environment", "The kitchen set extension"),
    "prop_lamp": ("Prop", "Practical lamp, hero prop"),
}

# author: "sup" writes as --supervisor, "me" as the artist. `to` addresses the artist.
TASKS = [
    dict(entity="sq010_sh010", step="Comp", status="ip", due=0, priority="1_Tier",
         description="Integrate the flicker; match the plate's warm spill on the wall.",
         versions=[dict(code="sq010_sh010_comp_v001", status="vwd"),
                   dict(code="sq010_sh010_comp_v002", status="rev",
                        notes=[dict(author="sup", subject="v002 flicker timing",
                                    content="Flicker reads mechanical. Try 3 uneven pulses over 24 frames, and lift the wall spill 10%.",
                                    to=True, status="opn", annotation=1012)])]),
    dict(entity="sq010_sh020", step="Comp", status="rev", due=1, priority="1_Tier",
         description="Rain on the glass, subtle. Plate has no rain.",
         versions=[dict(code="sq010_sh020_comp_v001", status="rev",
                        notes=[dict(author="sup", subject="rain density",
                                    content="Rain is too even. Cluster it toward the top of frame.",
                                    to=True, status="opn",
                                    replies=[("me", "Clustered, and slowed the streaks 15%. New version this afternoon."),
                                             ("sup", "Good. Keep the streak speed, the slowdown reads better.")])])]),
    dict(entity="sq010_sh020", step="Roto", status="fin", due=-7, priority="2_Tier",
         description="Roto the window frame for the rain pass.",
         versions=[dict(code="sq010_sh020_roto_v001", status="apr",
                        notes=[dict(author="sup", subject="roto approved", content="Clean. Approved.",
                                    to=True, status="clsd")])]),
    dict(entity="sq010_sh030", step="Light", status="ready", due=3, priority="2_Tier",
         description="Key from the lamp, fill from the window. Match sh010."),
    dict(entity="sq010_sh030", step="Comp", status="wtg", due=7, priority="3_Tier",
         description="Waits on Light."),
    dict(entity="sq010_sh040", step="Comp", status="hld", due=10, priority="3_Tier",
         description="On hold until the insert is re-shot.",
         orphan_note=dict(author="sup", subject="sh040 re-shoot",
                          content="Insert is being re-shot Thursday. Hold comp until the new plate lands.")),
    dict(entity="charA", step="Model", status="ip", due=-1, priority="1_Tier",
         description="Hands need another pass; thumbs read short in the turntable.",
         versions=[dict(code="charA_model_v003", status="rev",
                        notes=[dict(author="sup", subject="v003 hands", content="Thumbs are still short. Compare against the reference sheet, page 2.",
                                    to=True, status="opn",
                                    replies=[("me", "Lengthened 8%. Turntable v004 coming.")])])]),
    dict(entity="env_kitchen", step="Texture", status="rev", due=2, priority="2_Tier",
         description="Tile grout too clean, dirty it up.",
         versions=[dict(code="env_kitchen_texture_v002", status="rev",
                        notes=[dict(author="sup", subject="grout",
                                    content="Grout reads brand new. Add wear along the traffic line to the sink.",
                                    to=True, status="opn", annotation=1)])]),
    dict(entity="prop_lamp", step="Model", status="wtg", due=14, priority="3_Tier",
         description="Block out from the art department sketch."),
]


def plan_summary():
    lines = [f"sequence {SEQUENCE}", f"{len(SHOTS)} shots, {len(ASSETS)} assets, {len(TASKS)} tasks"]
    nv = sum(len(t.get("versions", [])) for t in TASKS)
    nn = sum(len(v.get("notes", [])) for t in TASKS for v in t.get("versions", [])) + sum(1 for t in TASKS if t.get("orphan_note"))
    nr = sum(len(n.get("replies", [])) for t in TASKS for v in t.get("versions", []) for n in v.get("notes", []))
    lines.append(f"{nv} versions, {nn} notes, {nr} replies")
    for t in TASKS:
        lines.append(f"  {t['entity']:<12} {t['step']:<8} -> {t['status']:<6} due {day(t['due'])}  {t['priority']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------------------------------

class Seed:
    def __init__(self, e, supervisor):
        self.e = e
        self.script = _site.client(e)
        self.artist_login = (e.get("FPT_USER_LOGIN") or "").strip()
        if not self.artist_login:
            raise SystemExit("set FPT_USER_LOGIN in sg-groundtruth/.env.local: the artist")
        self.me = _site.client(e, as_login=self.artist_login)
        self.sup = _site.client(e, as_login=supervisor) if supervisor else self.script
        self.project = _site.project_id(self.script, e)
        self.artist = _site.user_id(self.script, self.artist_login)
        self.supervisor = _site.user_id(self.script, supervisor) if supervisor else None
        self.made = []          # [slug, id, label], creation order
        self.ids = {}           # code -> {type, id}
        self.steps = self._steps()

    def _steps(self):
        rows = _site.search(self.script, "steps", [], ["code", "entity_type"], size=200)
        out = {}
        for s in rows:
            key = (s["attributes"]["code"], s["attributes"]["entity_type"])
            out.setdefault(key, s["id"])     # lowest id wins where a site has duplicates
        return out

    def author(self, who):
        return self.me if who == "me" else self.sup

    def ref(self, code):
        return self.ids[code]

    def create(self, c, slug, body, label, type_name):
        d = _site.ok(c.post(f"/entity/{slug}", headers=_site.JSON, json={
            "project": {"type": "Project", "id": self.project}, **body}), f"create {slug} {label}")
        self.made.append([slug, d["id"], label])
        self.ids[label] = {"type": type_name, "id": d["id"]}
        print(f"  {type_name:<8} {d['id']:>6}  {label}")
        return d

    def put(self, c, slug, i, patch, label):
        r = c.put(f"/entity/{slug}/{i}", headers=_site.JSON, json=patch)
        _site.ok(r, f"update {slug}/{i} {label}")
        print(f"  {slug:<8} {i:>6}  {label}: {json.dumps(patch)}")

    def thumb(self, c, slug, i, code):
        _site.upload(c, slug, i, "image", f"{code}.png", _site.png(code))

    # -- passes ---------------------------------------------------------------------------------

    def entities(self):
        print("\n# sequence, shots, assets")
        seq = self.create(self.script, "sequences", {"code": SEQUENCE}, SEQUENCE, "Sequence")
        for code, desc in SHOTS.items():
            self.create(self.script, "shots", {
                "code": code, "description": desc, "sg_shot_type": "VFX",
                "sg_sequence": {"type": "Sequence", "id": seq["id"]}}, code, "Shot")
            self.thumb(self.script, "shots", self.ids[code]["id"], code)
        for code, (kind, desc) in ASSETS.items():
            self.create(self.script, "assets", {
                "code": code, "description": desc, "sg_asset_type": kind}, code, "Asset")
            self.thumb(self.script, "assets", self.ids[code]["id"], code)

    def tasks(self):
        # The script creates Tasks: a coordinator's job, and the Artist permission set refuses it
        # (400 "Entity of type Task cannot be created by this user").
        print("\n# tasks, assigned to the artist, on the default status")
        for t in TASKS:
            ent = self.ref(t["entity"])
            step = self.steps.get((t["step"], ent["type"]))
            if step is None:
                raise SystemExit(f"no Step {t['step']} for {ent['type']} on this site")
            label = f"{t['entity']}/{t['step']}"
            body = {"content": t["step"], "entity": ent, "step": {"type": "Step", "id": step},
                    "task_assignees": [{"type": "HumanUser", "id": self.artist}],
                    "due_date": day(t["due"]), "sg_priority_1": t["priority"],
                    "sg_description": t["description"]}
            t["_id"] = self.create(self.script, "tasks", body, label, "Task")["id"]

    def versions(self):
        print("\n# versions, submitted by the artist")
        for t in TASKS:
            for v in t.get("versions", []):
                body = {"code": v["code"], "entity": self.ref(t["entity"]),
                        "sg_task": {"type": "Task", "id": t["_id"]},
                        "user": {"type": "HumanUser", "id": self.artist},
                        "description": f"{t['step']} for {t['entity']}"}
                v["_id"] = self.create(self.me, "versions", body, v["code"], "Version")["id"]
                self.thumb(self.me, "versions", v["_id"], v["code"])

    def notes(self):
        print("\n# notes and replies, as people")
        for t in TASKS:
            for v in t.get("versions", []):
                for n in v.get("notes", []):
                    self._note(n, t, links=[{"type": "Version", "id": v["_id"]}, self.ref(t["entity"])],
                               tasks=[{"type": "Task", "id": t["_id"]}], version=v)
            if t.get("orphan_note"):
                # No task, nobody addressed: the kind of note studios lose (research/02, implication 9).
                self._note(t["orphan_note"], t, links=[self.ref(t["entity"])], tasks=[], version=None)

    def _note(self, n, t, links, tasks, version):
        body = {"subject": n["subject"], "content": n["content"], "note_links": links, "tasks": tasks,
                "sg_note_type": "Internal"}
        if n.get("to") and self.artist:
            body["addressings_to"] = [{"type": "HumanUser", "id": self.artist}]
        label = f"note:{n['subject']}"
        d = self.create(self.author(n["author"]), "notes", body, label, "Note")
        n["_id"] = d["id"]
        if n.get("annotation") and version:
            # Annotations are Attachments on the Note; the frame is in the filename (research/02 §5).
            frame = n["annotation"]
            _site.upload(self.author(n["author"]), "notes", d["id"], None,
                         f"annot_version_{version['_id']}.{frame}.png", _site.png(f"annot {version['code']}"))
        for who, content in n.get("replies", []):
            r = _site.ok(self.author(who).post("/entity/replies", headers=_site.JSON, json={
                "entity": {"type": "Note", "id": d["id"]}, "content": content}), f"reply on {label}")
            self.made.append(["replies", r["id"], f"reply:{n['subject']}:{who}"])
            print(f"  Reply    {r['id']:>6}  on {n['subject']!r} by {who}")
            time.sleep(1)     # created_at has one-second resolution; replies sort on id anyway (entity_types/Reply)

    def mutate(self):
        """The second pass. Every status the plan ends on is written here as a change, never on create."""
        print("\n# mutations: the artist starts work, the supervisor reviews, notes close")
        for t in TASKS:
            if t["status"] != "wtg":
                # Statuses the artist sets (ip) come from the artist; the rest from the supervisor.
                who = self.me if t["status"] == "ip" else self.sup
                self.put(who, "tasks", t["_id"], {"sg_status_list": t["status"]}, f"{t['entity']}/{t['step']}")
            for v in t.get("versions", []):
                if v["status"] != "rev":
                    self.put(self.sup, "versions", v["_id"], {"sg_status_list": v["status"]}, v["code"])
                for n in v.get("notes", []):
                    if n["status"] != "opn":
                        self.put(self.author(n["author"]), "notes", n["_id"], {"sg_status_list": n["status"]}, n["subject"])
        # One late change so "since you left" has something newer than the rest.
        t = TASKS[0]
        self.put(self.sup, "tasks", t["_id"], {"due_date": day(1)}, f"{t['entity']}/{t['step']} due moved")

    def attachments(self):
        """Uploads leave Attachment rows the delete of their parent does not remove (recipe 013)."""
        for slug, i, label in list(self.made):
            if slug != "notes":
                continue
            for a in _site.search(self.script, "attachments",
                                  [["attachment_links", "is", {"type": "Note", "id": i}]], ["filename"]):
                self.made.append(["attachments", a["id"], f"attachment:{a['attributes'].get('filename')}"])

    def manifest(self):
        return {"project": self.project, "artist": self.artist, "supervisor": self.supervisor,
                "seeded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "today": TODAY.isoformat(), "created": self.made}


def clean(e):
    m = _site.read_manifest()
    if not m:
        raise SystemExit("nothing to clean: no fixtures/seed-manifest.json")
    c = _site.client(e)
    gone = 0
    for slug, i, label in reversed(m["created"]):
        r = c.delete(f"/entity/{slug}/{i}")
        gone += r.status_code == 204
        print(f"  {r.status_code}  {slug}/{i}  {label}")
    print(f"deleted {gone} of {len(m['created'])}")
    _site.MANIFEST.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write the rows; without it, print the plan")
    ap.add_argument("--clean", action="store_true", help="delete every row in the manifest and exit")
    ap.add_argument("--supervisor", default="", metavar="LOGIN",
                    help="HumanUser login the supervisor's notes and reviews are written as (sudo_as_login)")
    a = ap.parse_args()
    e = _site.env()
    if a.clean:
        return clean(e)
    if _site.read_manifest():
        raise SystemExit("fixtures/seed-manifest.json exists: run --clean first, the seed does not reuse rows")

    s = Seed(e, a.supervisor)
    print(f"project {s.project}, artist HumanUser {s.artist}, "
          f"supervisor {'HumanUser ' + str(s.supervisor) if s.supervisor else 'the script user (notes will not reach the stream, probe 067)'}")
    print(plan_summary())
    if not a.write:
        print("\ndry run. Pass --write to create these rows.")
        return
    try:
        s.entities()
        s.tasks()
        s.versions()
        s.notes()
        s.mutate()
        s.attachments()
    finally:
        _site.write_manifest(s.manifest())
        print(f"\nmanifest: {_site.MANIFEST} ({len(s.made)} rows)")


if __name__ == "__main__":
    sys.exit(main())
