"""Steps [3b] and [3c]: look + slots -> style.json (bible), cast.json (story into slots), filled assets + manifest.

Usage: uv run pipeline/style.py builds/<book> [--brief "text"] [--refs ressources/style] [--dry-run] [--fill-tilesets]
Needs builds/<book>/slots.json (from slots.py) and story.json. Requires a brief or reference images.

Fill rules for the MVP:
- image slots: one picture per subject, resized and padded to the slot's exact size, background keyed out when transparent.
- sheet slots: one pose per facing, repeated across every frame of that facing's animation rows (static, not animated),
  composed at the sheet's frame grid, plus every scaled copy upstream has. Metadata files are untouched.
- tileset slots: kept from upstream (libre, attributed) unless --fill-tilesets, which tiles one generated texture.
- colour / material / parameter slots: a palette value chosen by the cast.
- model, audio, font, text slots: left to the adapter, listed as unfilled.
A required slot that cannot be filled gets a flat palette shape and is listed under "missing".
"""
import argparse
import base64
import hashlib
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402

load_dotenv(C.ROOT / ".env")

BLOCKLIST = ["mario", "nintendo", "disney", "pokemon", "pokémon", "zelda", "ghibli", "pixar",
             "tenniel", "burton", "dreamworks", "marvel", "minecraft"]
SPRITE_ROLES = {"player", "npc", "enemy", "pickup", "portrait", "decoration"}
FACING_WORDS = {"right": "seen from the side, facing right", "left": "seen from the side, facing left",
                "up": "seen from behind, facing away", "down": "seen from the front, facing the viewer",
                "front": "seen from the front", "side": "seen from the side, facing right", "back": "seen from behind"}


def check_prompt(p):
    hit = [w for w in BLOCKLIST if w in p.lower()]
    if hit:
        raise ValueError(f"prompt names a franchise or artist {hit}: {p[:80]}")
    return p


# ---------- [3b] style bible ----------

def style_key(brief, refs, slots):
    kinds = sorted({(s["kind"], s["role"]) for s in slots["slots"]})
    return hashlib.sha1(json.dumps([brief or "", [r.name for r in refs], kinds]).encode()).hexdigest()[:12]


def write_bible(client, build, slots, brief, refs):
    schema = json.loads((C.SCHEMA / "style.schema.json").read_text())
    kinds = sorted({s["kind"] for s in slots["slots"]})
    examples = "\n".join(f"- {s['id']}: {s['kind']} for {s['role']}, {s['format'].get('notes', '')[:120]}"
                         for s in slots["slots"][:40])
    parts = [{"type": "text", "text":
              "You are the art director for a game made from a book, for a dyslexic player. Write a style bible as JSON.\n"
              "`palette`: 5 to 8 hex colours. `prompt_prefix`: one sentence every image prompt starts with: medium, line, "
              "colour, mood. `avoid`: a short list no prompt may include. `rules`: exactly one rule per slot kind listed "
              "below, saying how that kind is drawn inside its constraint (framing, anchor, background, how a tile reads "
              "next to its neighbours, how a portrait is cropped). The rule describes the look; it never changes the "
              "format. `ui`: hex colours from the palette for the subtitle box background, subtitle text (must contrast "
              "strongly with the background), an accent, and general chrome.\n"
              "Never name a franchise, studio, film, game, illustrator, or living artist; describe the look instead.\n\n"
              f"Slot kinds present in this game: {kinds}\nEngine notes: {slots.get('engine_notes', '')}\n"
              f"Some slots:\n{examples}\n\nBrief from the user: {brief or '(none, infer from the reference images)'}"}]
    for p in refs:
        parts.append({"type": "image", "data": base64.b64encode(p.read_bytes()).decode(),
                      "mime_type": "image/png" if p.suffix.lower() == ".png" else "image/jpeg"})
    r = client.interactions.create(
        model=C.ARGON, input=parts,
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "medium"},
    )
    style = json.loads(r.output_text)
    style["rules"] = {x["kind"]: x["rule"] for x in style["rules"]}
    style.update({"key": style_key(brief, refs, slots), "refs": [p.name for p in refs], "brief": brief,
                  "interaction_id": r.id, "game": slots["game"]})
    check_prompt(" ".join([style["prompt_prefix"], *style["rules"].values()]))
    (build / "style.json").write_text(json.dumps(style, ensure_ascii=False, indent=1))
    return style


# ---------- [3c] cast ----------

def subjects(story, sel):
    chars = [c for c in story["characters"] if any(c["first_chapter"] <= ch <= c["last_chapter"] for ch in sel)]
    chapters = [c for c in story["chapters"] if c["id"] in sel]
    items = [i for i in story["items"] if i["chapter"] in sel]
    return chars, chapters, items


def write_cast(client, build, story, slots, style, sel):
    schema = json.loads((C.SCHEMA / "cast.schema.json").read_text())
    chars, chapters, items = subjects(story, sel)
    slot_lines = "\n".join(
        f"- {s['id']}: role {s['role']}, kind {s['kind']}, count {s['count']}, required {s['required']}, "
        f"upstream depicts '{s['subject_hint']}'" + (" [synthetic]" if s.get("synthetic") else "")
        for s in slots["slots"])
    prompt = (
        "Cast the story into the game's asset slots. Return one assignment per (slot, subject) pair.\n"
        "Rules: every player slot (including armour or outfit variants) gets the protagonist (the first character). "
        "Every character gets exactly one 'portrait' assignment. Every chapter gets exactly one 'backdrop' assignment. "
        "Each other character goes into exactly ONE npc or enemy slot, the one whose upstream subject it resembles most "
        "(an animal slot for an animal); every remaining npc and enemy slot gets subject_type 'none' and will be removed. "
        "Enemies in this game do no damage, so an enemy slot may hold a friendly character. Each item goes into exactly "
        "ONE pickup slot; if the game also shows a held or equipped version of that same item, that slot may take it too. "
        "Every other pickup slot gets 'none'. UI images such as cursors, spinners, banners and favicons get 'none'. "
        "Terrain, decoration and tileset slots get the chapter whose setting they fit, or 'none' to keep upstream. "
        "Effects get 'none'. Colour, material and parameter slots get subject_type 'ui' with `value` set to a hex colour from the "
        f"palette {style['palette']} that suits the slot. Audio, font, model and text slots get 'none'. "
        "`value` is an empty string unless it is a colour. `why` is one short phrase.\n\n"
        f"CHARACTERS\n" + "\n".join(f"- {c['id']}: {c['name']}. {c['look']}" for c in chars) +
        f"\n\nCHAPTERS\n" + "\n".join(f"- {c['id']}: {c['title']}. {c['summary']}" for c in chapters) +
        f"\n\nITEMS\n" + "\n".join(f"- {i['id']}: {i['name']}. {i['meaning']}" for i in items) +
        f"\n\nSLOTS\n{slot_lines}\n\nEngine notes: {slots.get('engine_notes', '')}")
    r = client.interactions.create(
        model=C.ARGON, input=prompt,
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "medium"},
    )
    cast = json.loads(r.output_text)
    ids = {s["id"] for s in slots["slots"]}
    known = {c["id"] for c in chars} | {c["id"] for c in chapters} | {i["id"] for i in items} | {"narrator", "ui", "none", ""}
    cast["assignments"] = [a for a in cast["assignments"] if a["slot_id"] in ids and (a["subject_id"] in known or a["subject_type"] in ("ui", "none"))]
    by_id = {s["id"]: s for s in slots["slots"]}
    protagonist = chars[0]["id"] if chars else None
    seen, kept = {}, []
    player_slots = [a["slot_id"] for a in cast["assignments"] if a["subject_type"] == "character" and by_id[a["slot_id"]]["role"] == "player"]
    keep_player = next((x for x in player_slots if "weapon" not in x and any(w in x for w in ("cloth", "default", "base", "player"))), player_slots[0] if player_slots else None)
    for a in cast["assignments"]:
        s = by_id[a["slot_id"]]
        key = (a["subject_type"], a["subject_id"], "npc" if s["role"] in ("npc", "enemy") else s["role"])
        if s["role"] == "player" and a["slot_id"] != keep_player:
            a = {**a, "subject_type": "none", "subject_id": "", "why": "one player sprite set only; variant removed"}
        elif a["subject_type"] == "character" and s["role"] in ("npc", "enemy") and a["subject_id"] != protagonist:
            if key in seen:
                a = {**a, "subject_type": "none", "subject_id": "", "why": "duplicate cast, removed"}
        elif a["subject_type"] == "item" and s["role"] == "pickup":
            if key in seen:
                a = {**a, "subject_type": "none", "subject_id": "", "why": "duplicate cast, removed"}
        elif a["subject_type"] in ("character", "item", "chapter") and s["role"] == "ui":
            a = {**a, "subject_type": "none", "subject_id": "", "why": "ui image, kept or removed by adapter"}
        seen[key] = True
        kept.append(a)
    cast["assignments"] = kept
    cast["interaction_id"], cast["selection"] = r.id, sel
    (build / "cast.json").write_text(json.dumps(cast, ensure_ascii=False, indent=1))
    return cast


# ---------- image helpers ----------

def key_white(im: Image.Image, thresh=225, grain=200):
    """Make the white background transparent, including light grey paper grain (bright and unsaturated)."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            lo, hi = min(r, g, b), max(r, g, b)
            if lo > thresh or (lo > grain and hi - lo < 22):
                px[x, y] = (r, g, b, 0)
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def fit(im: Image.Image, w, h, anchor="bottom", cover=False):
    """Scale into (w, h). Transparent padding, anchored at the bottom centre unless cover."""
    im = im.convert("RGBA")
    if not cover and im.getbbox():
        im = im.crop(im.getbbox())  # anchor on visible pixels, not on transparent margin
    sw, sh = im.size
    scale = max(w / sw, h / sh) if cover else min(w / sw, h / sh)
    im = im.resize((max(1, round(sw * scale)), max(1, round(sh * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = (w - im.width) // 2
    y = (h - im.height) if anchor == "bottom" else (h - im.height) // 2
    out.paste(im, (x, y), im)
    return out


def compose_sheet(poses: dict, fmt: dict) -> Image.Image:
    """poses: facing -> RGBA pose image. Static sheet: each animation row repeats its facing's pose."""
    fw, fh = fmt["frame_width"], fmt["frame_height"]
    anims = fmt.get("animations") or [{"name": "idle", "row": 0, "frames": 1}]
    cols = max(a["frames"] for a in anims)
    rows = max(a["row"] for a in anims) + 1
    if fmt.get("sheet_width") and fmt.get("sheet_height"):
        cols, rows = max(cols, fmt["sheet_width"] // fw), max(rows, fmt["sheet_height"] // fh)
    sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
    default = next(iter(poses.values()))
    for a in anims:
        facing = next((f for f in poses if a["name"].endswith("_" + f) or a["name"] == f), None)
        pose = fit(poses.get(facing, default), fw, fh)
        for i in range(a["frames"]):
            bob = 1 if ("walk" in a["name"] or "atk" in a["name"]) and i % 2 else 0  # tiny step so motion reads
            sheet.paste(pose, (i * fw, a["row"] * fh - bob), pose)
    return sheet


def flat_shape(w, h, colour):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.2, h * 0.1, w * 0.8, h * 0.95], fill=colour)
    return im


# ---------- [3c] fill ----------

import threading
_POSES: dict = {}
_LOCKS: dict = {}
_LOCK = threading.Lock()


def gen_pose(client, build, prompt, aspect, key) -> Image.Image:
    """Generate once per key (subject + view) and reuse across slots; cached on disk under assets/_poses/.
    One lock per key, so concurrent slots wanting the same pose wait for a single generation."""
    d = build / "assets" / "_poses"
    d.mkdir(parents=True, exist_ok=True)
    path = d / (hashlib.sha1(f"{key}|{prompt}".encode()).hexdigest()[:16] + ".png")
    with _LOCK:
        lock = _LOCKS.setdefault(path, threading.Lock())
    with lock:
        if path not in _POSES:
            if not path.exists():
                tmp = path.with_suffix(".tmp.png")
                gen_image(client, prompt, aspect).save(tmp, format="PNG")
                tmp.replace(path)
            _POSES[path] = Image.open(path).convert("RGBA")
        return _POSES[path].copy()


def gen_image(client, prompt, aspect) -> Image.Image:
    check_prompt(prompt)
    r = client.interactions.create(
        model=C.IMAGE, input=prompt,
        response_format={"type": "image", "mime_type": "image/jpeg", "aspect_ratio": aspect, "image_size": "1K"},
    )
    return Image.open(io.BytesIO(base64.b64decode(r.output_image.data)))


def subject_text(story, a):
    if a["subject_type"] == "character":
        c = next(x for x in story["characters"] if x["id"] == a["subject_id"]); return f"Character: {c['name']}. {c['look']}"
    if a["subject_type"] == "chapter":
        c = next(x for x in story["chapters"] if x["id"] == a["subject_id"]); return f"Scene: {c['summary']}"
    if a["subject_type"] == "item":
        i = next(x for x in story["items"] if x["id"] == a["subject_id"]); return f"Object: {i['name']}. {i['meaning']}"
    return ""


def aspect_of(fmt, default="1:1"):
    if fmt.get("aspect_ratio") in ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"):
        return fmt["aspect_ratio"]
    w, h = fmt.get("width"), fmt.get("height")
    if w and h:
        r = w / h
        return "16:9" if r > 1.6 else "4:3" if r > 1.15 else "3:4" if r < 0.85 else "1:1"
    return default


def fill(client, build, story, slots, style, cast, game_dir: Path | None, fill_tilesets=False, dry_run=False):
    out_root = build / "assets"
    out_root.mkdir(exist_ok=True)
    manifest_path = out_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() and json.loads(manifest_path.read_text()).get("style_key") == style["key"] \
        else {"style_key": style["key"], "fills": {}, "replaces": {}, "parameters": {}, "kept_upstream": [], "remove": [], "unfilled": [], "missing": []}
    by_id = {s["id"]: s for s in slots["slots"]}
    pre, avoid, rules = style["prompt_prefix"], style["avoid"], style["rules"]
    jobs = []
    for a in cast["assignments"]:
        s = by_id[a["slot_id"]]
        kind, fmt = s["kind"], s["format"]
        if kind in ("colour", "material") or s["role"] == "parameter":
            if a["value"]:
                manifest["parameters"][s["id"]] = a["value"]
            continue
        if a["subject_type"] == "none" or kind in ("audio", "font", "text", "model"):
            if s["role"] in ("npc", "enemy", "pickup", "player", "portrait", "backdrop") and kind in ("sheet", "image"):
                manifest.setdefault("remove", []).append(s["id"])  # uncast character and item art leaves the game
            else:
                (manifest["kept_upstream"] if s["where"]["files"] else manifest["unfilled"]).append(s["id"])
            continue
        if kind == "tileset" and not fill_tilesets:
            manifest["kept_upstream"].append(s["id"]); continue
        jobs.append((s, a))
    manifest["kept_upstream"] = sorted(set(manifest["kept_upstream"]))
    manifest["remove"] = sorted(set(manifest.get("remove", [])))
    manifest["unfilled"] = sorted(set(manifest["unfilled"]))
    if dry_run:
        for s, a in jobs:
            print(f"  [{s['id']} {s['kind']} <- {a['subject_type']}:{a['subject_id']}] {pre[:60]}... {subject_text(story, a)[:70]}")
        print(f"{len(jobs)} slot fills would run ({sum(len(by_id[s['id']]['format'].get('facings') or ['x']) if s['kind']=='sheet' else 1 for s, a in jobs)} images); "
              f"parameters {len(manifest['parameters'])}, kept upstream {manifest['kept_upstream']}, unfilled {manifest['unfilled']}")
        return manifest
    t0 = time.time()

    def work(job):
        s, a = job
        kind, fmt, sid, subj = s["kind"], s["format"], s["id"], a["subject_id"]
        d = out_root / s["role"]
        d.mkdir(parents=True, exist_ok=True)
        texture = kind == "tileset" or any(w in (fmt.get("notes", "") + " " + s["subject_hint"]).lower() for w in ("seamless", "tileable", "texture", "pattern"))
        rule = rules.get("tileset" if texture else kind, "")
        base_prompt = f"{pre} {rule} {subject_text(story, a)} No interface elements, no icons, no bars, no frames, no text. Avoid: {avoid}."
        existing = manifest["fills"].get(sid, {}).get(subj)
        if existing and not existing.get("missing") and existing.get("prompt") == base_prompt and Path(build / existing["path"]).exists():
            return f"  {sid}/{subj} cached"
        entry = {"subject_type": a["subject_type"], "prompt": base_prompt, "paths": []}
        try:
            transparent = fmt.get("transparent", s["role"] in SPRITE_ROLES)
            if kind == "sheet":
                facings = [f.strip().lower() for f in (fmt.get("facings") or []) if f.strip().lower() in FACING_WORDS]
                facings = facings or sorted({x["name"].rsplit("_", 1)[-1] for x in (fmt.get("animations") or [])} & set(FACING_WORDS)) or ["right"]
                facings = [f for f in facings if f != "left" or "left" in {x["name"].rsplit("_", 1)[-1] for x in (fmt.get("animations") or [])}]
                poses = {}
                for f in facings:
                    im = gen_pose(client, build, f"{base_prompt} Full body, {FACING_WORDS.get(f, f)}, standing, plain pure white background.", "1:1", f"{subj}|{f}")
                    poses[f] = key_white(im)
                sheet = compose_sheet(poses, fmt)
                path = d / f"{sid}_{subj}.png"
                sheet.save(path)
                entry.update(path=path.relative_to(build).as_posix(), width=sheet.width, height=sheet.height, facings=facings, degraded="static frames")
                # one file per upstream copy, at that copy's measured size
                for up, (w, h) in (fmt.get("measured") or {}).items():
                    k = round(w / sheet.width) if sheet.width else 1
                    p2 = d / f"{sid}_{subj}@{k}x.png" if k != 1 else path
                    if k != 1:
                        sheet.resize((sheet.width * k, sheet.height * k), Image.NEAREST).save(p2)
                    manifest["replaces"][up] = p2.relative_to(build).as_posix()
                    entry["paths"].append(p2.relative_to(build).as_posix())
            elif kind == "tileset":
                im = gen_pose(client, build, f"{base_prompt} Seamless repeating ground texture, top-down, no objects.", "1:1", f"{subj}|tile")
                w, h = fmt.get("width"), fmt.get("height")
                ts = fmt.get("tile_size") or 32
                tile = im.convert("RGBA").resize((ts, ts), Image.LANCZOS)
                sheet = Image.new("RGBA", (w or ts * 8, h or ts * 8))
                for y in range(0, sheet.height, ts):
                    for x in range(0, sheet.width, ts):
                        sheet.paste(tile, (x, y))
                path = d / f"{sid}_{subj}.png"
                sheet.save(path)
                entry.update(path=path.relative_to(build).as_posix(), width=sheet.width, height=sheet.height, degraded="single texture tiled")
                for up in s["where"]["files"]:
                    manifest["replaces"][up] = entry["path"]
            elif texture:  # a seamless texture slot: one tile-able image, resized to each upstream copy
                tex_prompt = (f"{pre} {rule} Seamless repeating flat surface texture only: {s['subject_hint']}. Colours {', '.join(style['palette'][:4])}. "
                              f"No objects, no figures, no scene, no perspective, no interface elements, no text. Avoid: {avoid}.")
                im = gen_pose(client, build, tex_prompt, "1:1", f"{subj}|texture|{sid}")
                w, h = fmt.get("width") or 128, fmt.get("height") or 128
                im = im.convert("RGBA").resize((w, h), Image.LANCZOS)
                path = d / f"{sid}_{subj}.png"
                im.save(path)
                entry.update(path=path.relative_to(build).as_posix(), width=w, height=h, degraded="texture, not seamless")
                for up, (uw, uh) in (fmt.get("measured") or {}).items():
                    p2 = d / f"{sid}_{subj}_{uw}.png"
                    im.resize((uw, uh), Image.LANCZOS).save(p2)
                    manifest["replaces"][up] = p2.relative_to(build).as_posix()
                    entry["paths"].append(p2.relative_to(build).as_posix())
            else:  # image
                view = "portrait" if s["role"] == "portrait" else f"image|{aspect_of(fmt)}|{int(transparent)}"
                im = gen_pose(client, build, base_prompt + (" Plain pure white background." if transparent else ""), aspect_of(fmt), f"{subj}|{view}")
                if transparent:
                    im = key_white(im)
                w, h = fmt.get("width"), fmt.get("height")
                if w and h:
                    im = fit(im, w, h, anchor="bottom" if s["role"] in SPRITE_ROLES else "center", cover=not transparent)
                ext = "png" if transparent else "jpg"
                path = d / f"{sid}_{subj}.{ext}"
                (im if transparent else im.convert("RGB")).save(path)
                entry.update(path=path.relative_to(build).as_posix(), width=im.width, height=im.height)
                for up in s["where"]["files"]:
                    manifest["replaces"][up] = entry["path"]
            manifest["fills"].setdefault(sid, {})[subj] = entry
            return f"  {sid}/{subj} ok {entry['width']}x{entry['height']}"
        except Exception as e:
            if s["required"]:
                w, h = fmt.get("width") or fmt.get("frame_width") or 256, fmt.get("height") or fmt.get("frame_height") or 256
                path = d / f"{sid}_{subj}_missing.png"
                flat_shape(w, h, style["palette"][0]).save(path)
                entry.update(path=path.relative_to(build).as_posix(), width=w, height=h, missing=True, error=str(e)[:200])
                manifest["fills"].setdefault(sid, {})[subj] = entry
                manifest["missing"].append(f"{sid}/{subj}")
            return f"  {sid}/{subj} FAILED {str(e)[:100]}"

    with ThreadPoolExecutor(max_workers=4) as ex:
        for line in ex.map(work, jobs):
            print(line, flush=True)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    manifest["missing"] = sorted(set(manifest["missing"]))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    cp = build / "cast.json"
    cast["filled"] = True
    cp.write_text(json.dumps(cast, ensure_ascii=False, indent=1))
    print(f"{len(jobs)} fills in {time.time()-t0:.0f}s; parameters {len(manifest['parameters'])}, kept upstream {len(manifest['kept_upstream'])}, missing {manifest['missing']}")
    return manifest


def run(build: Path, brief, refs_dir: Path, dry_run=False, fill_tilesets=False, force_style=False):
    story = json.loads((build / "story.json").read_text())
    slots = json.loads((build / "slots.json").read_text())
    sel = json.loads((build / "selection.json").read_text())["chapters"]
    refs = sorted(p for p in refs_dir.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not refs and not brief:
        sys.exit("need --brief text or reference images in " + str(refs_dir))
    client = genai.Client()
    sp = build / "style.json"
    style = json.loads(sp.read_text()) if sp.exists() else None
    if force_style or not style or style.get("key") != style_key(brief, refs, slots):
        print("writing style bible...")
        style = write_bible(client, build, slots, brief, refs)
    print(f"style: {style['name']} | key {style['key']} | palette {style['palette']} | rules for {sorted(style['rules'])}")
    cp = build / "cast.json"
    cast = json.loads(cp.read_text()) if cp.exists() and json.loads(cp.read_text()).get("selection") == sel else None
    if not cast:
        print("casting story into slots...")
        cast = write_cast(client, build, story, slots, style, sel)
    print(f"cast: {len(cast['assignments'])} assignments")
    return fill(client, build, story, slots, style, cast, None, fill_tilesets, dry_run)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--brief", default=None)
    ap.add_argument("--refs", default=str(C.RESSOURCES / "style"))
    ap.add_argument("--dry-run", action="store_true", help="bible and cast only; list what would be generated")
    ap.add_argument("--fill-tilesets", action="store_true")
    ap.add_argument("--force-style", action="store_true")
    a = ap.parse_args()
    run(Path(a.build), a.brief, Path(a.refs), a.dry_run, a.fill_tilesets, a.force_style)
