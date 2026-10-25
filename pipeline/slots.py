"""Step [3a] of the pipeline: game repo -> slots.json. Argon reads the code; we ground every claim against real files.

Usage: uv run pipeline/slots.py games/<game> [--out builds/<book>/slots.json]
slots.json is cached next to the clone as games/<game>.slots.json (keyed by the repo's text hash) and copied to the build.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402
from pipeline.adapt import game_files  # noqa: E402

load_dotenv(C.ROOT / ".env")

# Every game gets these two, added by the adapter if upstream has nothing like them. They carry the look
# into games whose art is procedural: a portrait next to each spoken line, a backdrop when a chapter opens.
SYNTHETIC = [
    {"id": "dialogue_portrait", "role": "portrait", "kind": "image", "required": True, "count": 99, "synthetic": True,
     "subject_hint": "portrait of the speaking character, shown beside the subtitle",
     "where": {"files": [], "code": []},
     "format": {"file_type": "png", "width": 512, "height": 512, "transparent": True, "aspect_ratio": "1:1",
                "notes": "Added by the adapter: a square portrait shown next to the subtitle box while a character speaks."}},
    {"id": "chapter_backdrop", "role": "backdrop", "kind": "image", "required": True, "count": 99, "synthetic": True,
     "subject_hint": "full-screen illustration shown when a chapter starts",
     "where": {"files": [], "code": []},
     "format": {"file_type": "jpg", "width": 1280, "height": 720, "transparent": False, "aspect_ratio": "16:9",
                "notes": "Added by the adapter: shown full screen with the narrator reading the chapter summary."}},
]


def repo_hash(texts):
    h = hashlib.sha256()
    for rel, content in texts:
        h.update(rel.encode()); h.update(content.encode())
    return h.hexdigest()[:16]


def ask_argon(client, game_dir: Path, texts):
    schema = json.loads((C.SCHEMA / "slots.schema.json").read_text())
    blob = "\n\n".join(f"===== {rel} =====\n{c}" for rel, c in texts)
    listing = "\n".join(sorted(p.relative_to(game_dir).as_posix() for p in game_dir.rglob("*")
                               if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts))
    t = time.time()
    r = client.interactions.create(
        model=C.ARGON, system_instruction=(C.PROMPTS / "slots.md").read_text(),
        input=f"GAME: {game_dir.name}\n\nALL FILES IN THE REPOSITORY\n{listing}\n\nSOURCE\n{blob}",
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "high"},
    )
    out = json.loads(r.output_text)
    out["interaction_id"], out["seconds"] = r.id, round(time.time() - t)
    return out


def ground(slot, game_dir: Path):
    """Check the slot's claims against the real files. Returns (ok, reasons)."""
    reasons, fmt = [], slot["format"]
    files = [game_dir / f for f in slot["where"]["files"]]
    missing = [f.relative_to(game_dir).as_posix() for f in files if not f.exists()]
    if missing:
        reasons.append(f"missing files {missing[:3]}")
    images = [f for f in files if f.exists() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if images:
        sizes = {}
        for f in images:
            try:
                sizes[f.relative_to(game_dir).as_posix()] = Image.open(f).size
            except Exception as e:
                reasons.append(f"unreadable {f.name}: {e}")
        slot["format"]["measured"] = {k: list(v) for k, v in sizes.items()}
        base = min(sizes.values(), key=lambda s: s[0] * s[1]) if sizes else None
        if base and fmt.get("width") and fmt.get("height") and slot["kind"] == "image":
            if (fmt["width"], fmt["height"]) not in sizes.values():
                reasons.append(f"claimed {fmt['width']}x{fmt['height']}, files are {sorted(set(sizes.values()))}")
        if base and slot["kind"] == "sheet" and fmt.get("frame_width") and fmt.get("frame_height"):
            fw, fh = fmt["frame_width"], fmt["frame_height"]
            if base[0] % fw or base[1] % fh:
                reasons.append(f"sheet {base} not a multiple of frame {fw}x{fh}")
            else:
                rows = base[1] // fh
                anims = fmt.get("animations") or []
                if anims and max(a["row"] for a in anims) >= rows:
                    reasons.append(f"animation row beyond sheet rows ({rows})")
                if anims and max(a["frames"] for a in anims) > base[0] // fw:
                    reasons.append(f"frames exceed sheet columns ({base[0] // fw})")
                fmt["sheet_width"], fmt["sheet_height"] = base
    meta = fmt.get("metadata_file")
    if meta and not (game_dir / meta).exists():
        reasons.append(f"metadata file missing {meta}")
    for ref in slot["where"]["code"][:6]:
        path = ref.split(":")[0]
        if not (game_dir / path).exists():
            reasons.append(f"code ref missing {path}")
            break
    if slot["kind"] == "colour" and fmt.get("current_value") and slot["where"]["code"]:
        path = slot["where"]["code"][0].split(":")[0]
        p = game_dir / path
        if p.exists() and fmt["current_value"].lower() not in p.read_text(errors="ignore").lower():
            reasons.append(f"value {fmt['current_value']} not found in {path}")
    return not reasons, reasons


def run(game_dir: Path, out: Path | None = None, force=False):
    texts, _ = game_files(game_dir)
    h = repo_hash(texts)
    cache = game_dir.parent / f"{game_dir.name}.slots.json"
    data = json.loads(cache.read_text()) if cache.exists() and not force else None
    if not data or data.get("repo_hash") != h:
        print(f"reading {len(texts)} files (~{sum(len(c) for _, c in texts)//4000}k tokens) with Argon...")
        data = ask_argon(genai.Client(), game_dir, texts)
        data["repo_hash"] = h
    grounded, rejected = [], []
    for s in data["slots"]:
        ok, why = ground(s, game_dir)
        (grounded if ok else rejected).append({**s, "grounded": ok, "ground_reasons": why})
    have_ids = {s["id"] for s in grounded}
    for syn in SYNTHETIC:
        if syn["id"] not in have_ids:
            grounded.append({**syn, "grounded": True, "ground_reasons": []})
    data["slots"], data["rejected"] = grounded, rejected
    cache.write_text(json.dumps(data, indent=1))
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=1))
    by_kind = {}
    for s in grounded:
        by_kind[s["kind"]] = by_kind.get(s["kind"], 0) + 1
    print(f"{len(grounded)} slots grounded {by_kind}, {len(rejected)} rejected")
    for s in rejected[:8]:
        print(f"  rejected {s['id']} ({s['kind']}): {s['ground_reasons'][0]}")
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("game_dir")
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    run(Path(a.game_dir), Path(a.out) if a.out else None, a.force)
