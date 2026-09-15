"""Shared plumbing for the seed and capture scripts: the corpus client, env, uploads, thumbnails.

Everything goes through `../sg-groundtruth`'s `FPT` client so what these scripts do is what the
corpus measured. Credentials are that repo's `.env.local`; nothing here reads or prints them.
"""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUNDTRUTH = ROOT.parent / "sg-groundtruth"
sys.path.insert(0, str(GROUNDTRUTH / "src"))

from sg_groundtruth.client import FPT, FPTError  # noqa: E402
from sg_groundtruth.env import load  # noqa: E402

JSON = {"Content-Type": "application/json"}
# `_search` takes the vendor array type; every other write takes plain JSON (probe 014).
ARR = {"Content-Type": "application/vnd+shotgun.api3_array+json"}
MANIFEST = ROOT / "fixtures" / "seed-manifest.json"


def env():
    if not (GROUNDTRUTH / ".env.local").exists():
        raise SystemExit(f"no {GROUNDTRUTH / '.env.local'}: the seed reads the corpus repo's credentials")
    return load(GROUNDTRUTH)


def client(e, as_login=""):
    """The script user, or the script acting as `as_login` (probe 027: an OAuth scope, never a body field)."""
    return FPT.from_env(e, sudo_as_login=as_login)


def ok(r, what):
    if not r.ok:
        raise SystemExit(f"{what} -> {r.status_code} {r.text[:400]}")
    return r.json()["data"] if r.content else None


def search(c, slug, filters, fields, size=200, sort=None):
    body = {"filters": filters, "fields": fields, "page": {"size": size}}
    if sort:
        body["sort"] = sort
    return ok(c.post(f"/entity/{slug}/_search", headers=ARR, json=body), f"search {slug}")


def project_id(c, e):
    """The one project the seed may write into, by the name the corpus repo's env names."""
    name = (e.get("FPT_PROBE_SANDBOX_PROJECT") or "").strip()
    if not name:
        raise SystemExit("set FPT_PROBE_SANDBOX_PROJECT in sg-groundtruth/.env.local")
    rows = search(c, "projects", [["name", "is", name]], ["name"])
    if not rows:
        raise SystemExit(f"no project named {name!r}")
    return rows[0]["id"]


def user_id(c, login):
    rows = search(c, "human_users", [["login", "is", login]], ["login", "name"])
    if not rows:
        raise SystemExit(f"no HumanUser with login {login!r}")
    return rows[0]["id"]


def upload(c, slug, entity_id, field, filename, payload):
    """The three-call upload of recipe 001. `field` None attaches a generic Attachment (probe 014)."""
    import requests

    path = f"/entity/{slug}/{entity_id}/_upload" if field is None else f"/entity/{slug}/{entity_id}/{field}/_upload"
    b = c.get(path, params={"filename": filename})
    b = ok(b, f"upload ticket {path}") and c.get(path, params={"filename": filename}).json()
    requests.put(b["links"]["upload"], data=payload, timeout=60).raise_for_status()
    r = c.post(b["links"]["complete_upload"], headers=JSON, json={"upload_info": b["data"], "upload_data": {}})
    if r.status_code != 201:
        raise SystemExit(f"complete_upload {path} -> {r.status_code} {r.text[:300]}")


def png(label, w=320, h=180):
    """A flat-colour thumbnail with a diagonal band, coloured from the label. Standard library only.

    Generated media, so the public demo carries no one else's licensing. A real thumbnail is a
    transcode away (`field_types/image`); this is what the field holds until then.
    """
    hue = int(hashlib.sha1(label.encode()).hexdigest()[:6], 16)
    base = ((hue >> 16) & 255, (hue >> 8) & 255, hue & 255)
    band = tuple(min(255, v + 70) for v in base)
    rows = []
    for y in range(h):
        row = bytearray([0])
        for x in range(w):
            on_band = 40 < (x + y) % 160 < 80
            row.extend(band if on_band else base)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def read_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else None


def write_manifest(m):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1) + "\n")
