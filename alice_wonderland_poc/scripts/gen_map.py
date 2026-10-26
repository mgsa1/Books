"""Argon designs each town's tile map from the chapters that describe it; a validator checks it is
playable (bounds, overlaps, every door/spot reachable by BFS) and errors go back to Argon.

    .venv/bin/python -I scripts/gen_map.py              # all towns in game/script.json, in parallel
    .venv/bin/python -I scripts/gen_map.py digne
"""
import json
import re
import sys
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from argon import ARGON, client  # noqa: E402
from books import BOOK as lesmis  # noqa: E402  (BOOK env var picks the book)

GAME = lesmis.game_dir
WALKABLE = set(".=*:")
LEGEND = """Tiles (one character each):
  .  ground (grass, dirt, or snow — the renderer picks by season)   walkable
  =  street / road / paved square                                    walkable
  *  garden, flowerbed, field                                        walkable
  :  bridge or ford                                                  walkable
  ~  water (river, pond, spring basin)                               blocked
  T  tree / dense wood                                               blocked
  #  wall, fence, hedge, cliff                                       blocked
Buildings are NOT drawn in the grid; list them in `buildings` and leave their footprint as ground."""

FORMAT = """{
  "town": "<id>", "w": 32, "h": 24,
  "season": "SEASONS",
  "tiles": ["32 characters", "... exactly h rows ..."],
  "buildings": [{"id": "<building id from the spec>", "x": 3, "y": 4, "w": 5, "d": 4, "floors": 2,
                 "wall": "#hex", "roof": "#hex", "door": [5, 8], "sign_fr": "optional short sign text"}],
  "spots": {"<spot id>": [x, y]},
  "props": [{"type": "fountain|well|lamp|bench|cart|cross|barrel|stall|haystack|statue|gate|mushroom|tea_table|rose_bush|throne|clock|door_small|bottle", "x": 10, "y": 12}],
  "exits": [{"x": 0, "y": 12, "label_fr": "Route de ..."}]
}
Coordinates: x = column (0 = west), y = row (0 = north). A building occupies x..x+w-1, y..y+d-1.
`door` is the WALKABLE tile directly outside the building's front wall where the player stands to enter (adjacent to the footprint)."""

INSTRUCTIONS = """You design the top-down tile map for one town of a Pokémon-style BOOKNAME game. Above are the chapters of the novel that describe this town.

Town spec (from the game script):
{spec}

Story beats that happen here (characters stand on these spots; triggers use these spots/buildings):
{beats}

""" + LEGEND + """

Return ONE JSON object:
""" + FORMAT + """

Rules:
1. Size 28-36 wide, 20-26 high. Follow Hugo's geography where he gives it (what is next to what, the square, the main street, the gate, the woods), compressed to fit.
2. Include every building and every spot of the spec, with exactly those ids. Spots must be walkable tiles, not inside a building footprint.
3. Every spot, every door tile and every exit must be reachable on foot from the entry spot ({entry}). Streets connect things; walls and water shape them.
4. Buildings must not overlap each other or water/trees; leave at least one walkable tile around each door.
5. Colours: COLOURS
6. 6-20 props that Hugo mentions or that make the place legible. 1-2 exits at the map edge.
Return only the JSON object."""


def validate(m, spec):
    errs = []
    w, h = m.get("w"), m.get("h")
    rows = m.get("tiles", [])
    if len(rows) != h:
        errs.append(f"tiles has {len(rows)} rows, expected h={h}")
    for i, r in enumerate(rows):
        if len(r) != w:
            errs.append(f"row {i} has {len(r)} chars, expected w={w}")
    if errs:
        return errs
    for b in m.get("buildings", []):  # malformed entries become feedback, not crashes
        for k in ("id", "x", "y", "w", "d", "door"):
            if k not in b:
                errs.append(f"building {b.get('id', '?')} is missing '{k}' (every building needs a door tile, even if not enterable)")
    for k in ("spots", "buildings"):
        if not isinstance(m.get(k), (dict if k == "spots" else list)):
            errs.append(f"'{k}' missing or wrong type")
    if errs:
        return errs
    occ = {}
    for b in m["buildings"]:
        for x in range(b["x"], b["x"] + b["w"]):
            for y in range(b["y"], b["y"] + b["d"]):
                if not (0 <= x < w and 0 <= y < h):
                    errs.append(f"building {b['id']} out of bounds at {x},{y}"); continue
                if (x, y) in occ:
                    errs.append(f"building {b['id']} overlaps {occ[(x, y)]} at {x},{y}")
                if rows[y][x] not in WALKABLE:
                    errs.append(f"building {b['id']} sits on '{rows[y][x]}' at {x},{y}")
                occ[(x, y)] = b["id"]
    blocked = lambda x, y: not (0 <= x < w and 0 <= y < h) or rows[y][x] not in WALKABLE or (x, y) in occ
    for p in m.get("props", []):
        occ.setdefault((p["x"], p["y"]), "prop:" + p["type"])  # props block too
    want_b = {b["id"] for b in spec["buildings"]}
    have_b = {b["id"] for b in m["buildings"]}
    for missing in want_b - have_b:
        errs.append(f"missing building {missing}")
    want_s = {s["id"] for s in spec["spots"]}
    for missing in want_s - set(m["spots"]):
        errs.append(f"missing spot {missing}")
    for sid, (x, y) in m["spots"].items():
        if blocked(x, y):
            errs.append(f"spot {sid} at {x},{y} is not walkable ({'building/prop ' + occ[(x, y)] if (x, y) in occ else repr(rows[y][x]) if 0 <= y < h and 0 <= x < w else 'out of bounds'})")
    targets = {f"spot {k}": tuple(v) for k, v in m["spots"].items()}
    for b in m["buildings"]:
        dx, dy = b["door"]
        adjacent = any((dx + ox, dy + oy) in occ and occ[(dx + ox, dy + oy)] == b["id"] for ox, oy in ((0, -1), (0, 1), (-1, 0), (1, 0)))
        if not adjacent:
            errs.append(f"door of {b['id']} at {dx},{dy} is not next to its footprint")
        if blocked(dx, dy):
            errs.append(f"door of {b['id']} at {dx},{dy} is not walkable")
        targets[f"door of {b['id']}"] = (dx, dy)
    for i, e in enumerate(m.get("exits", [])):
        targets[f"exit {i}"] = (e["x"], e["y"])
    start = m["spots"].get(spec["entry_spot"])
    if not start or blocked(*start):
        errs.append(f"entry spot {spec['entry_spot']} missing or blocked")
        return errs
    seen, q = {tuple(start)}, deque([tuple(start)])
    while q:
        x, y = q.popleft()
        for ox, oy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            n = (x + ox, y + oy)
            if n not in seen and not blocked(*n):
                seen.add(n); q.append(n)
    for name, t in targets.items():
        if t not in seen and not blocked(*t):
            errs.append(f"{name} at {t[0]},{t[1]} is not reachable from the entry spot")
    return errs


def parse_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def build_town(script, tid):
    spec = next(t for t in script["towns"] if t["id"] == tid)
    beats = [{k: b[k] for k in ("id", "objective_en", "trigger", "npcs")} for b in script["beats"] if b["town"] == tid]
    refs = sorted(set(spec["refs"]) | {l["ref"] for b in script["beats"] if b["town"] == tid for l in b["lines"]})
    chapters = "\n\n".join(f"【{r}】 {lesmis.BY_REF[r]['title']}\n{lesmis.BY_REF[r]['text']}" for r in refs if r in lesmis.BY_REF)
    # plain replace: the FORMAT example is full of JSON braces that str.format would choke on
    seasons = lesmis.seasons or "autumn-dusk | day | winter-night"
    name = "Alice's Adventures in Wonderland" if lesmis.id == "alice" else "Les Misérables"
    colours = ("storybook, Tenniel-like: soft greens, rose reds, cream; houses can be whimsical (the March Hare's has chimneys like ears and a fur-thatched roof)."
               if lesmis.id == "alice" else "muted, period-appropriate; the church/cathedral should read as the biggest building if there is one.")
    prompt = chapters + "\n\n" + (INSTRUCTIONS.replace("SEASONS", seasons).replace("BOOKNAME", name).replace("COLOURS", colours).replace("{spec}", json.dumps(spec, ensure_ascii=False, indent=1))
                                  .replace("{beats}", json.dumps(beats, ensure_ascii=False)).replace("{entry}", spec["entry_spot"]))
    log = []
    t0 = time.time()
    it = client.interactions.create(model=ARGON, input=prompt, generation_config={"thinking_level": "high", "max_output_tokens": 40000})
    (GAME / f"map_{tid}_raw_0.json").write_text(it.output_text)
    m = parse_json(it.output_text)
    for rnd in range(5):
        errs = validate(m, spec)
        log.append(f"{tid} round {rnd}: {time.time() - t0:.0f}s · {len(errs)} problems")
        print(log[-1], *(f"\n    {e}" for e in errs[:8]), flush=True)
        if not errs:
            break
        fb = "A program validated your map. Fix these problems, keep the rest, return the full JSON:\n" + "\n".join(f"- {e}" for e in errs[:40])
        it = client.interactions.create(model=ARGON, input=fb, previous_interaction_id=it.id,
                                        generation_config={"thinking_level": "medium", "max_output_tokens": 40000})
        (GAME / f"map_{tid}_raw_{rnd + 1}.json").write_text(it.output_text)
        m = parse_json(it.output_text)
    m["valid"] = not validate(m, spec)
    (GAME / f"map_{tid}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote game/map_{tid}.json ({'valid' if m['valid'] else 'STILL INVALID'})", flush=True)
    return m


if __name__ == "__main__":
    args = sys.argv[1:]
    src = GAME / "script.json"
    if args and args[0].startswith("--script="):  # e.g. build from a draft while the script is still being repaired
        src = Path(args.pop(0).split("=", 1)[1])
    script = parse_json(src.read_text())
    towns = args or [t["id"] for t in script["towns"]]
    with ThreadPoolExecutor(len(towns)) as pool:
        list(pool.map(lambda t: build_town(script, t), towns))
