"""Pokémon-style pixel sprites for every character: front first, then back + side with the front as a
reference (keeps the character consistent), green-screen keyed, snapped to a 64 px grid, 20-colour palette.

    BOOK=alice .venv/bin/python -I scripts/pixel_game.py               # all characters missing sprites
    BOOK=alice .venv/bin/python -I scripts/pixel_game.py --only alice --force
-> <assets>/pixel/<id>_{front,back,side}.png, manifest["pixel"]
"""
import argparse
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from paint import GREEN, chroma_key, generate, green_ok, soften  # noqa: E402
from books import BOOK  # noqa: E402

STYLE = ("16-bit pixel art overworld sprite in the style of Pokemon HeartGold / SoulSilver: chibi proportions (big head), "
         "crisp square pixels, limited palette, dark 1-pixel outline, no anti-aliasing, no dithering noise.")
VIEWS = {"front": "facing the viewer (walking down)", "back": "seen from behind (walking up, facing away)",
         "side": "in profile facing to the right (walking right)"}
BOOK_NAME = {"alice": "Alice's Adventures in Wonderland (Tenniel's illustrations)", "lesmis": "Les Misérables (France, 1815-1823)"}[BOOK.id]
OUT = BOOK.assets_dir / "pixel"


def snap(img_bytes, h=64):
    im = chroma_key(img_bytes)
    w = max(8, round(im.width * h / im.height))
    small = im.resize((w, h), Image.BOX)
    alpha = small.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    rgb = small.convert("RGB").quantize(colors=20, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = rgb.convert("RGBA"); out.putalpha(alpha)
    return out


def paint_view(c, view, ref=None):
    desc = f"{c['name_fr']} from {BOOK_NAME}: {c.get('portrait_prompt', '')}"
    p = (f"A single {STYLE} Character: {desc}. Full body from head to feet, standing, {VIEWS[view]}."
         + (" Exactly the same character, colours, clothes and proportions as the reference sprite." if ref else "") + GREEN)
    for _ in range(3):
        try:
            raw = generate(p, "1:1", ref_image=ref)
        except Exception as ex:  # content filter: Argon rewrites the description, keeping the visual details
            if "blocked" in str(ex).lower() or "prohibited" in str(ex).lower() or "safety" in str(ex).lower():
                p = soften(p, str(ex)); print(f"  ↻ {c['id']} {view}: blocked, Argon rewrote the prompt", flush=True); continue
            raise
        ok, why = green_ok(raw)
        if ok:
            break
    (OUT / "raw" / f"{c['id']}_{view}.jpg").write_bytes(raw)
    snap(raw).save(OUT / f"{c['id']}_{view}.png")
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    g = json.loads((BOOK.game_dir / "script.json").read_text())
    todo = [c for c in g["characters"] if (not only or c["id"] in only) and (a.force or not (OUT / f"{c['id']}_side.png").exists())]
    t0 = time.time()

    def run(c):
        front = paint_view(c, "front")
        with ThreadPoolExecutor(2) as ex:
            list(ex.map(lambda v: paint_view(c, v, front), ["back", "side"]))
        return c["id"]

    with ThreadPoolExecutor(6) as pool:
        futs = [pool.submit(run, c) for c in todo]
        for f in futs:
            try:
                print(f"  ✓ {f.result():<20} {time.time() - t0:.0f}s", flush=True)
            except Exception as ex:
                print(f"  ✗ {str(ex)[:150]}", flush=True)
    mpath = BOOK.assets_dir / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    manifest["pixel"] = sorted({p.stem.rsplit("_", 1)[0] for p in OUT.glob("*_side.png")})
    mpath.write_text(json.dumps(manifest, indent=1))
    print(f"done: {len(manifest['pixel'])} characters with sprites")


if __name__ == "__main__":
    main()
