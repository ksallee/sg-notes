"""The month the seed writes: records, tasks, versions, notes, replies, attachments, timestamps.

Pure: one `random.Random` seeded with a constant, no clock beyond the anchor date passed in, no
network. The same anchor and the same seed produce the same site, so a reseed is a reseed.

Names are invented. Nothing here is a real show, a real person or a real studio.
"""
import datetime as dt
import random

SEED = 20260915
WEEKS = 5

SEQUENCES = {
    "sq010": ("The kitchen, night", 8),
    "sq020": ("The stairwell chase", 8),
    "sq030": ("Rooftop, dawn", 6),
}
SHOT_BEATS = [
    "Hero walks in, practical lamp flickers", "Reverse on the window, rain added in comp",
    "Wide of the room, full CG lamp", "Insert on the light switch",
    "Hero takes the first flight of stairs", "Whip pan to the landing",
    "Handheld push-in on the door", "Low angle, rig removal on the banister",
    "Hero clears frame left, set extension behind", "Two-shot on the landing, bounce from below",
    "Tilt up to the skylight", "Close on the hand on the rail",
    "Dawn wide, city set extension", "Hero silhouette against the sun",
    "Over-shoulder on the antenna mast", "Crane down to the ledge",
    "Insert on the phone screen", "Final wide, matte painting background",
    "Cut-in on the boots", "Rack focus to the far tower",
    "Pull back to reveal the roofline", "Static on the empty doorway",
]
ASSETS = [
    ("char_hero", "Character", "Hero character, look-dev approved"),
    ("char_second", "Character", "Second lead, shares the hero rig"),
    ("char_crowd_a", "Character", "Crowd variant A"),
    ("env_kitchen", "Environment", "The kitchen set extension"),
    ("env_stairwell", "Environment", "Stairwell, six floors, modular"),
    ("env_rooftop", "Environment", "Rooftop and the city beyond"),
    ("env_city_far", "Environment", "Far city, matte painting with cards"),
    ("prop_lamp", "Prop", "Practical lamp, hero prop"),
    ("prop_phone", "Prop", "Phone, screen replaced in comp"),
    ("prop_keys", "Prop", "Keyring, background"),
    ("veh_sedan", "Vehicle", "Sedan, street level only"),
    ("veh_van", "Vehicle", "Van, parked, no interior"),
]

# Steps that exist on the test site for each type, with the short name a version code carries.
SHOT_STEPS = [("Layout", "layout"), ("Animation", "anim"), ("Tracking", "track"), ("Roto", "roto"),
              ("FX", "fx"), ("Light", "light"), ("Comp", "comp")]
ASSET_STEPS = [("Design", "dsgn"), ("Model", "model"), ("Texture", "txtr"), ("Rigging", "rig"),
               ("Art", "art")]

TASK_STATUSES = ["wtg", "ready", "ip", "ip", "rev", "fin", "apr", "hld", "omt"]
TASK_WEIGHTS = [14, 10, 22, 0, 16, 18, 12, 5, 3]
VERSION_STATUSES = ["rev", "vwd", "apr", "fin", "ip", "na", "cmpt"]
VERSION_WEIGHTS = [30, 16, 22, 14, 10, 4, 4]
NOTE_STATUSES = ["opn", "ip", "clsd"]
NOTE_WEIGHTS = [45, 19, 36]
PRIORITIES = ["1_Tier", "2_Tier", "3_Tier"]

TASK_DESCRIPTIONS = {
    "Layout": "Block the camera and the set pieces from the previs.",
    "Animation": "Blocking to spline; hold the eyeline through the turn.",
    "Tracking": "Solve the handheld move, survey the set for the extension.",
    "Roto": "Roto the foreground for the hold-out.",
    "FX": "Simulate the practical elements, hand off caches to Light.",
    "Light": "Key from the practical, fill from the window. Match the neighbouring shot.",
    "Comp": "Assemble the renders, integrate the elements, final grade.",
    "Design": "Concept pass from the art department brief.",
    "Model": "Build to the approved concept, keep the topology quad-dominant.",
    "Texture": "Texture and shade to the look-dev turntable.",
    "Rigging": "Rig to the animation brief, deliver a picker.",
    "Art": "Paint the key art for the sequence.",
}

# Review notes, by the step whose work they are about. `{t}` is the thing the record is about.
NOTES_BY_STEP = {
    "Comp": [
        ("edge on {t}", "The matte edge is chattering along {t}. Soften by a pixel and check it against the plate at 200%."),
        ("grain mismatch", "Grain sits on top rather than in the image. Match the plate's grain size and regrain after the grade."),
        ("black levels", "Blacks are crushed in the lower third. Lift them to match the reference frame."),
        ("despill", "Green is still in the hair on the left side. Despill and rebuild the edge colour."),
        ("screen insert", "The screen insert slides against the tracked corners. Re-track the two right markers."),
        ("rain density", "Rain is too even across frame. Cluster it toward the top and let it thin toward the floor."),
        ("lens distortion", "The CG is undistorted against a distorted plate. Apply the shot's lens grid."),
        ("flicker timing", "The flicker reads mechanical. Three uneven pulses over 24 frames, and lift the wall spill 10%."),
        ("wire removal", "There is a residual wire over the shoulder from 1042. Patch and track the fix."),
        ("edge of frame", "Left edge goes soft for six frames at the end of the move."),
    ],
    "Light": [
        ("key direction", "The key is too frontal. Bring it round 20 degrees to match the practical."),
        ("shadow density", "Contact shadow under the foot is missing. Add an occlusion pass."),
        ("colour temperature", "Fill is too cool against the plate. Warm it toward the window."),
        ("spec breakup", "Speculars are clean to the point of plastic. Break them up with a roughness map."),
        ("exposure", "The whole frame is half a stop hot against the neighbouring shot."),
        ("bounce", "No bounce off the floor. The lower half of the character reads flat."),
        ("rim", "Rim light is fighting the composition. Pull it back and let the silhouette do the work."),
    ],
    "Animation": [
        ("timing on the turn", "The turn is a beat late against the cut. Pull it four frames earlier."),
        ("contact", "The foot slides on contact between 1018 and 1026. Lock it."),
        ("weight", "The character reads light on the landing. Add a settle and a small overshoot."),
        ("arcs", "The hand arc breaks halfway through the reach. Smooth it in the graph editor."),
        ("eyeline", "Eyeline drifts off the mark through the pan. Hold it on the door."),
        ("blink", "No blinks in the whole shot. Add two, one on the head turn."),
    ],
    "Model": [
        ("silhouette", "The silhouette is soft at the shoulder. Sharpen it against the concept."),
        ("topology", "Topology at the elbow will not deform. Reflow the loops."),
        ("proportion", "Hands read small against the reference sheet, page 2."),
        ("bevels", "Hard edges everywhere. Bevel anything the camera gets close to."),
        ("scale", "The model is built at 1.4 of the rig scale. Rebuild at the show unit."),
    ],
    "Texture": [
        ("grout wear", "Grout reads brand new. Add wear along the traffic line to the sink."),
        ("tiling", "The wall texture tiles visibly at the top of frame. Break it up."),
        ("UV seam", "A seam is visible down the inside of the arm."),
        ("spec map", "Everything is uniformly glossy. Vary the roughness by material."),
        ("colour drift", "The albedo is more saturated than the concept. Pull it back."),
    ],
    "FX": [
        ("dissipation", "The smoke dissipates too quickly. Double the lifetime and lower the dissipation."),
        ("collision", "Particles pass through the rail. Fix the collider."),
        ("density", "The sim is too dense to read the character behind it."),
        ("timing", "The burst lands two frames after the cue. Shift the cache."),
    ],
    "Roto": [
        ("hold-out", "The hold-out is soft on the right shoulder for the last 30 frames."),
        ("garbage matte", "Garbage matte clips the elbow at the end of the move."),
        ("edge quality", "The edge is too hard against a motion-blurred plate."),
    ],
    "Layout": [
        ("headroom", "Too much headroom against the previs. Reframe a touch lower."),
        ("lens", "This is cut at 35mm; the previs is 50mm. Confirm with the DP's notes."),
        ("set dressing", "The table is blocking the doorway the hero exits through."),
    ],
    "Tracking": [
        ("solve drift", "The solve drifts in the last 40 frames. Add survey points on the far wall."),
        ("jitter", "There is a one-pixel jitter on the vertical. Smooth the solve."),
        ("survey", "No survey for the set extension. Track the floor plane as well."),
    ],
    "Rigging": [
        ("deformation", "The shoulder collapses past 60 degrees."),
        ("picker", "The picker is missing the finger controls."),
    ],
    "Design": [
        ("silhouette read", "The silhouette does not read at a distance. Simplify the upper half."),
        ("palette", "The palette fights the sequence's key. Bring it toward the warm side."),
    ],
    "Art": [
        ("depth", "The far city has no atmospheric depth. Add haze by distance."),
        ("focal point", "Nothing draws the eye. Put a light source at the third."),
    ],
}

# Notes a client writes. `sg_note_type` Client, `client_note` set, no pipeline vocabulary.
CLIENT_NOTES = [
    ("Overall note", "We like where this is going. The performance sells it."),
    ("Too dark", "The whole sequence is playing darker than the last cut. Can we lift it?"),
    ("Pacing", "This runs long. Is there a version that gets to the door faster?"),
    ("Colour", "The greens are reading a little sickly on our monitor."),
    ("Approved for the cut", "Happy with this one. Please cut it in."),
    ("One more pass", "Nearly there. One more pass on the background and we will sign it off."),
    ("Question", "Is the reflection in the window a real element or built?"),
    ("Brand", "The logo on the van has to be legible in the wide."),
    ("Continuity", "The lamp is off here and on in the next shot."),
    ("Sound", "Note for editorial rather than you: the music drops out under this."),
]

# Notes that hang off nothing in particular: the kind a studio loses (research/02).
LOOSE_NOTES = [
    ("Dailies at 10", "Dailies moved to 10:00 for the rest of the week. Same room."),
    ("Render farm", "The farm is down for maintenance Saturday morning. Submit long jobs Friday."),
    ("Show LUT updated", "The show LUT changed this morning. Pull the new one before you grade anything."),
    ("Handover", "I am out Thursday and Friday. Anything urgent goes to the supervisor."),
    ("Naming", "Version names are drifting. Keep to <record>_<step>_v###."),
    ("Client visit", "Client in the building Wednesday afternoon. Playlists ready by noon."),
    ("Storage", "Scratch is at 90%. Clear your caches older than two weeks."),
    ("Turnover", "New turnover landed for the rooftop sequence. Plates are on the server."),
]

REPLIES_ARTIST = [
    "On it. New version this afternoon.", "Fixed and rendering now.",
    "I read that differently. Can we look at it in dailies?",
    "Done. The change is in the next version.",
    "That was a render artefact, not comp. Re-submitting.",
    "Will need the updated cache from FX before I can do that.",
    "Pushed 8%. Turntable coming.", "Agreed, that was sloppy. Corrected.",
    "This one is blocked on the new plate.", "Addressed everything except the last point.",
    "Can you point me at the reference frame?", "Took two passes but it holds now.",
]
REPLIES_REVIEWER = [
    "Better. Ship it.", "Closer. One more pass on the edge.",
    "Yes, let us look at it in dailies.", "That works. Approved.",
    "Still reading heavy to me. Compare against the neighbouring shot.",
    "Good. Keep the speed, the slower version read better.",
    "Fine for the client version; we will revisit for final.",
    "Thanks. Closing this.", "Hold until the turnover lands.",
    "Talk to Light before you change that.",
]
REPLIES_CLIENT = [
    "Thanks, that answers it.", "Yes please.", "We will look at it in the next review.",
    "Much better.", "Can we see it against the previous version?",
]

ATTACHMENT_KINDS = ["reference frame", "grade chart", "paint-out", "diagram"]


def _weighted(rng, values, weights):
    return rng.choices(values, weights=weights, k=1)[0]


class Calendar:
    """Timestamps over the last `WEEKS` weeks, with a working week's rhythm.

    `created_at` is accepted on a Note and a Reply create under `sudo_as_login` and read back exactly,
    though `Note.created_at` reports `editable: false` in `/schema` (`field_types/date_time`).
    """

    HOURS = [9, 10, 10, 10, 11, 11, 12, 13, 14, 15, 15, 16, 17, 17, 18, 19]

    def __init__(self, rng, anchor):
        self.rng = rng
        self.end = anchor
        self.start = anchor - dt.timedelta(weeks=WEEKS)
        self.days = [self.start + dt.timedelta(days=i) for i in range((anchor - self.start).days + 1)]
        self.cap = dt.datetime.combine(anchor, dt.time(12, 59, 59))
        # Weekdays carry the work; the recent weeks carry more of it than the first.
        self.weights = [(0.06 if d.weekday() == 5 else 0.04 if d.weekday() == 6 else 1.0)
                        * (0.6 + 0.8 * i / max(1, len(self.days) - 1))
                        for i, d in enumerate(self.days)]

    def moment(self, after=None, within_days=None):
        """A timestamp in the window, optionally on or after `after` and within `within_days` of it."""
        return min(self._moment(after, within_days), self.cap)

    def _moment(self, after, within_days):
        if after is not None and within_days is not None:
            for _ in range(8):
                day = self._workday(after.date() + dt.timedelta(
                    days=self.rng.choices(range(within_days + 1), k=1)[0]))
                if day is None:
                    continue
                t = self._at(day)
                if t > after:
                    return t
            return after + dt.timedelta(minutes=self.rng.randint(3, 400))
        for _ in range(20):
            t = self._at(self.rng.choices(self.days, weights=self.weights, k=1)[0])
            if after is None or t > after:
                return t
        return (after or self.start_of_window()) + dt.timedelta(hours=self.rng.randint(1, 30))

    def start_of_window(self):
        return dt.datetime.combine(self.start, dt.time(9, 0))

    def _workday(self, day):
        """Weekends carry a little work and push most of it to the Monday. None means redraw."""
        while day.weekday() >= 5 and self.rng.random() > 0.08:
            day += dt.timedelta(days=1)
        return None if day > self.end else day

    def _at(self, day):
        # The anchor day is only half over, so nothing lands in its evening.
        hours = [h for h in self.HOURS if h <= 12] if day == self.end else self.HOURS
        return dt.datetime.combine(day, dt.time(
            self.rng.choice(hours), self.rng.randrange(60), self.rng.randrange(60)))


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def build(anchor, people):
    """The whole month as plain data. `people` maps a role to a key the seed resolves to a user id.

    Roles: `artist`, `artist2`, `sup`, `script`. Every row carries the role that writes it.
    """
    rng = random.Random(SEED)
    cal = Calendar(rng, anchor)
    plan = {"anchor": anchor.isoformat(), "seed": SEED, "weeks": WEEKS,
            "sequences": [], "shots": [], "assets": [], "tasks": [], "versions": [], "notes": []}

    for code, (desc, count) in SEQUENCES.items():
        plan["sequences"].append({"code": code, "description": desc})
    beats = list(SHOT_BEATS)
    for code, (_, count) in SEQUENCES.items():
        for n in range(1, count + 1):
            plan["shots"].append({"code": f"{code}_sh{n * 10:03d}", "sequence": code,
                                  "description": beats.pop(0) if beats else "",
                                  "status": _weighted(rng, ["ip", "rev", "fin", "hld"], [50, 25, 20, 5])})
    for code, kind, desc in ASSETS:
        plan["assets"].append({"code": code, "kind": kind, "description": desc,
                               "status": _weighted(rng, ["ip", "rev", "fin"], [50, 25, 25])})

    records = [(s["code"], "Shot") for s in plan["shots"]] + [(a["code"], "Asset") for a in plan["assets"]]

    # Tasks: two to four steps per record, assigned to one of the two artists.
    for code, typ in records:
        steps = SHOT_STEPS if typ == "Shot" else ASSET_STEPS
        chosen = sorted(rng.sample(range(len(steps)), rng.choice([2, 3, 3, 4])))
        for i in chosen:
            step, short = steps[i]
            plan["tasks"].append({
                "key": f"{code}/{step}", "entity": code, "step": step, "short": short,
                "assignee": _weighted(rng, ["artist", "artist2"], [62, 38]),
                "status": _weighted(rng, TASK_STATUSES, TASK_WEIGHTS),
                "due": (cal.end + dt.timedelta(days=rng.randint(-21, 21))).isoformat(),
                "priority": _weighted(rng, PRIORITIES, [25, 45, 30]),
                "description": TASK_DESCRIPTIONS.get(step, ""),
                "created_at": iso(cal.moment())})

    # Versions: on the tasks that have reached review or beyond, one to three each.
    for t in plan["tasks"]:
        if t["status"] in ("wtg", "ready"):
            continue
        for n in range(1, rng.choice([1, 1, 2, 2, 3]) + 1):
            plan["versions"].append({
                "code": f"{t['entity']}_{t['short']}_v{n:03d}", "entity": t["entity"], "task": t["key"],
                "user": t["assignee"], "status": _weighted(rng, VERSION_STATUSES, VERSION_WEIGHTS),
                "description": f"{t['step']} for {t['entity']}",
                "created_at": iso(cal.moment())})

    _notes(plan, rng, cal, records)
    return plan


def _tail(rng, n, hot, hot_counts, rest_counts, rest_weights):
    """A long tail over `n` slots: `hot` of them carry `hot_counts`, the rest one or two."""
    order = list(range(n))
    rng.shuffle(order)
    counts = [0] * n
    for i, slot in enumerate(order[:hot]):
        counts[slot] = hot_counts[i % len(hot_counts)]
    for slot in order[hot:]:
        counts[slot] = _weighted(rng, rest_counts, rest_weights)
    return counts


def _notes(plan, rng, cal, records):
    by_code = {t["entity"]: [] for t in plan["tasks"]}
    for t in plan["tasks"]:
        by_code[t["entity"]].append(t)
    step_of = {v["code"]: next(t["step"] for t in plan["tasks"] if t["key"] == v["task"])
               for v in plan["versions"]}

    targets = []    # (kind, code, step, floor timestamp)
    counts = _tail(rng, len(records), 5, [19, 15, 13, 11, 9], [0, 1, 2, 3], [22, 34, 28, 16])
    for (code, typ), c in zip(records, counts):
        step = rng.choice([t["step"] for t in by_code.get(code, [])] or ["Comp"])
        targets += [("record", code, step, None)] * c
    vcounts = _tail(rng, len(plan["versions"]), 4, [6, 5, 5, 4], [0, 1, 1, 2], [14, 40, 0, 46])
    for v, c in zip(plan["versions"], vcounts):
        targets += [("version", v["code"], step_of[v["code"]],
                     dt.datetime.strptime(v["created_at"], "%Y-%m-%dT%H:%M:%SZ"))] * c
    targets += [("project", None, "Comp", None)] * 8
    targets += [("loose", None, "Comp", None)] * 5
    rng.shuffle(targets)

    used = {}
    for kind, code, step, floor in targets:
        client = rng.random() < 0.33
        if kind == "loose":
            subject, content = LOOSE_NOTES[len(used.setdefault("loose", [])) % len(LOOSE_NOTES)]
            used["loose"].append(subject)
            client = False
        elif client:
            subject, content = rng.choice(CLIENT_NOTES)
        else:
            bank = NOTES_BY_STEP.get(step) or NOTES_BY_STEP["Comp"]
            subject, content = rng.choice(bank)
            subject = subject.format(t=rng.choice(["the shoulder", "the rail", "the doorway", "the edge"]))
            content = content.format(t=rng.choice(["the shoulder", "the rail", "the doorway", "the edge"]))

        entity = code if kind == "record" else (
            next(v["entity"] for v in plan["versions"] if v["code"] == code) if kind == "version" else None)
        tasks = [t["key"] for t in by_code.get(entity, [])] if entity else []
        # `tasks` is filled on about half the notes; the Review Notes app fills it, hand-written notes
        # often do not (research/07).
        tasks = [rng.choice(tasks)] if tasks and rng.random() < 0.52 else []
        assignee = next((t["assignee"] for t in by_code.get(entity, []) if t["key"] in tasks), None)

        # Most review notes come from the supervisor; artists write on each other's work, and a few
        # arrive from an integration running as the script user.
        author = _weighted(rng, ["sup", "artist", "artist2", "script"], [58, 16, 22, 4])
        if kind == "loose" or client:
            author = _weighted(rng, ["sup", "artist2", "script"], [78, 16, 6])
        elif author == assignee:
            author = "sup"

        to, cc = [], []
        if rng.random() > 0.33:                      # a third of a site's notes address nobody
            pool = [p for p in ("artist", "artist2", "sup") if p != author]
            if assignee and assignee != author and rng.random() < 0.7:
                to = [assignee]
            else:
                to = rng.sample(pool, 1)
            if rng.random() < 0.22:
                to += [p for p in rng.sample(pool, 1) if p not in to]
            if rng.random() < 0.18:
                cc = [p for p in rng.sample(pool, 1) if p not in to]

        created = cal.moment(after=floor + dt.timedelta(minutes=20) if floor else None,
                             within_days=3 if floor else None)
        status = _weighted(rng, NOTE_STATUSES, NOTE_WEIGHTS)
        note = {
            "subject": subject, "content": content, "author": author, "kind": kind,
            "record": entity, "version": code if kind == "version" else None,
            "tasks": tasks, "to": to, "cc": cc, "status": status,
            "client_note": client,
            # `sg_note_type` is often unset on a real project (research/07).
            "note_type": "Client" if client else rng.choice(["Internal"] * 5 + [None]),
            "created_at": iso(created), "replies": [], "attachments": [], "read_by": [],
        }
        n_replies = _weighted(rng, [0, 1, 2, 3, 4, 5], [40, 24, 15, 10, 7, 4])
        last = created
        for i in range(n_replies):
            if client:
                who = "sup" if i % 2 == 0 else rng.choice(["artist", "artist2"])
                bank = REPLIES_CLIENT if who == "sup" else REPLIES_ARTIST
            else:
                who = (assignee or "artist") if i % 2 == 0 else ("sup" if author != "sup" else assignee or "artist")
                bank = REPLIES_ARTIST if who in ("artist", "artist2") else REPLIES_REVIEWER
            last = cal.moment(after=last + dt.timedelta(minutes=11), within_days=2)
            note["replies"].append({"author": who, "content": rng.choice(bank), "created_at": iso(last)})

        if rng.random() < 0.33:
            if kind == "version" and rng.random() < 0.7:
                # Legacy annotation frames are Attachments named for the Version and the frame
                # (research/08 §1; the filename convention is Autodesk's own).
                note["attachments"].append({"annotation": True, "version": code,
                                            "frame": rng.choice([0, 1, 12, 24, 48, 1012, 1044])})
            else:
                note["attachments"].append({"annotation": False, "kind": rng.choice(ATTACHMENT_KINDS)})
            if rng.random() < 0.15:
                note["attachments"].append({"annotation": False, "kind": rng.choice(ATTACHMENT_KINDS)})

        # Read state is per-person. An author reads their own note; an addressee has read about half.
        for who in to:
            if rng.random() < 0.45:
                note["read_by"].append(who)
        plan["notes"].append(note)

    plan["notes"].sort(key=lambda n: n["created_at"])
    # The last few days carry the changes the event log can still see: everything else is history.
    plan["mutations"] = _mutations(plan, rng)


def _mutations(plan, rng):
    """Changes written after every row exists, so streams and the event log have something to show.

    Event-log timestamps cannot be authored, so only changes made after the seed are measurable as
    "what changed since" (finding 025).
    """
    out = []
    for n in rng.sample([n for n in plan["notes"] if n["status"] == "opn"], 14):
        out.append({"type": "note", "key": n["subject"] + "@" + n["created_at"],
                    "field": "sg_status_list", "value": rng.choice(["ip", "clsd"])})
    for t in rng.sample([t for t in plan["tasks"] if t["status"] in ("ip", "rev")], 10):
        out.append({"type": "task", "key": t["key"], "field": "sg_status_list",
                    "value": rng.choice(["rev", "fin", "apr"])})
    for v in rng.sample([v for v in plan["versions"] if v["status"] == "rev"], 8):
        out.append({"type": "version", "key": v["code"], "field": "sg_status_list",
                    "value": rng.choice(["vwd", "apr"])})
    return out


def summary(plan):
    n = plan["notes"]
    counts = {}
    for note in n:
        counts[note["kind"]] = counts.get(note["kind"], 0) + 1
    replies = sum(len(x["replies"]) for x in n)
    attach = sum(len(x["attachments"]) for x in n)
    annot = sum(1 for x in n for a in x["attachments"] if a["annotation"])
    lines = [
        f"seed {plan['seed']}, {plan['weeks']} weeks to {plan['anchor']}",
        f"{len(plan['sequences'])} sequences, {len(plan['shots'])} shots, {len(plan['assets'])} assets, "
        f"{len(plan['tasks'])} tasks, {len(plan['versions'])} versions",
        f"{len(n)} notes ({', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}), "
        f"{replies} replies, {attach} attachments ({annot} annotation frames)",
        f"unaddressed {sum(1 for x in n if not x['to'] and not x['cc'])}, "
        f"client {sum(1 for x in n if x['client_note'])}, "
        f"with tasks {sum(1 for x in n if x['tasks'])}, "
        f"read by someone {sum(1 for x in n if x['read_by'])}",
        "note status " + ", ".join(f"{s} {sum(1 for x in n if x['status'] == s)}" for s in NOTE_STATUSES),
        "thread lengths " + ", ".join(
            f"{k} {sum(1 for x in n if len(x['replies']) == k)}" for k in range(6)),
        "authors " + ", ".join(f"{a} {sum(1 for x in n if x['author'] == a)}"
                               for a in ("sup", "artist", "artist2", "script")),
        f"{len(plan['mutations'])} mutations after the write, so the event log has a window",
    ]
    return "\n".join(lines)
