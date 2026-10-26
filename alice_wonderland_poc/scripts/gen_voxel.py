"""Argon looks at a character's full-body painting and designs a voxel model (layers of characters).
A validator checks the grid; problems go back to Argon.

    BOOK=alice .venv/bin/python -I scripts/gen_voxel.py alice white_rabbit
-> <assets>/voxel/<id>.json  {"palette": {"a": "#hex", ...}, "w": 14, "d": 10, "h": 30, "layers": [[row strings] x d] x h}
"""
import base64
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from argon import ARGON, client  # noqa: E402
from books import BOOK  # noqa: E402

OUT = BOOK.assets_dir / "voxel"
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = """Design a voxel model (like MagicaVoxel / Crossy Road) of this character for an isometric game, based on the attached painting.

Grid: w = 14 (x, left→right as the character faces you), d = 10 (z, back→front: row 0 is the BACK, row 9 is the FRONT/face side),
h = 30 (y, layer 0 = the floor under the feet, layer 29 = top). Chibi proportions: the head is about 40% of the height.
Return JSON:
{"palette": {"a": "#hex", "b": "#hex", ...},      // up to 14 single-letter keys; "." = empty
 "w": 14, "d": 10, "h": 30,
 "layers": [ layer0, layer1, ..., layer29 ]}       // each layer = 10 strings (z = 0..9) of exactly 14 chars (x = 0..13)
Rules: solid, connected shapes (no floating voxels); symmetric left/right except deliberate details (a watch in one hand);
the face (eyes, nose, mouth) on the FRONT rows; show the costume details you see (apron, collar, ribbon, waistcoat, buttons,
ears with pink insides, spectacles, pocket-watch...). Colours taken from the painting. Return only the JSON."""


def validate(m):
    errs = []
    w, d, h = m.get("w"), m.get("d"), m.get("h")
    pal = set(m.get("palette", {}))
    L = m.get("layers", [])
    if len(L) != h:
        errs.append(f"{len(L)} layers, expected h={h}")
    filled = set()
    for y, layer in enumerate(L):
        if len(layer) != d:
            errs.append(f"layer {y} has {len(layer)} rows, expected d={d}"); continue
        for z, row in enumerate(layer):
            if len(row) != w:
                errs.append(f"layer {y} row {z} has {len(row)} chars, expected w={w}")
            for x, c in enumerate(row):
                if c != ".":
                    if c not in pal:
                        errs.append(f"layer {y} row {z} col {x}: '{c}' not in palette")
                    filled.add((x, y, z))
    if errs:
        return errs[:30], 0
    # connectivity: flood from the lowest voxel; anything unreached floats
    if filled:
        start = min(filled, key=lambda p: p[1])
        seen, stack = {start}, [start]
        while stack:
            x, y, z = stack.pop()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                n = (x + dx, y + dy, z + dz)
                if n in filled and n not in seen:
                    seen.add(n); stack.append(n)
        floating = len(filled) - len(seen)
        if floating > 3:
            errs.append(f"{floating} voxels are not connected to the body (floating)")
    if len(filled) < 300:
        errs.append(f"only {len(filled)} voxels: too sparse, fill the volume")
    return errs, len(filled)


def parse(text):
    text = re.sub(r"//.*", "", text)
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def build(cid):
    img = (BOOK.assets_dir / "fullbody" / f"{cid}.png").read_bytes()
    t0 = time.time()
    it = client.interactions.create(model=ARGON, generation_config={"thinking_level": "high", "max_output_tokens": 40000}, input=[
        {"type": "image", "data": base64.b64encode(img).decode(), "mime_type": "image/png"}, {"type": "text", "text": PROMPT}])
    m = parse(it.output_text)
    for rnd in range(3):
        errs, n = validate(m)
        print(f"  {cid} round {rnd}: {time.time() - t0:.0f}s · {n} voxels · {len(errs)} problems {errs[:3]}", flush=True)
        if not errs:
            break
        it = client.interactions.create(model=ARGON, previous_interaction_id=it.id, generation_config={"thinking_level": "medium", "max_output_tokens": 40000},
                                        input="A program validated your voxel model. Fix these and return the full JSON:\n" + "\n".join(f"- {e}" for e in errs))
        m = parse(it.output_text)
    (OUT / f"{cid}.json").write_text(json.dumps(m))
    return cid


if __name__ == "__main__":
    with ThreadPoolExecutor(4) as pool:
        print(list(pool.map(build, sys.argv[1:])))
