"""Nano Banana paints the game's portraits (cut-outs) and key-moment cards, all in parallel.

    .venv/bin/python -I scripts/paint_game.py            # paint what is missing
    .venv/bin/python -I scripts/paint_game.py --only fantine,b05_candlesticks --force
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from paint import CUTOUT, cut_out, generate, paper_ok, soften  # noqa: E402
from books import BOOK  # noqa: E402  (BOOK env var picks the book)

STYLE = BOOK.style
OUT = BOOK.assets_dir
CARD = (" A full-bleed illustration filling the whole frame on aged paper, cinematic composition, no text, no border, no caption.")


def paint_with_checks(prompt, aspect, needs_white, log):
    for attempt in range(3):
        try:
            raw = generate(prompt, aspect)
        except Exception as ex:
            if "safety" in str(ex).lower() or "prohibited" in str(ex).lower():
                prompt = soften(prompt, str(ex)); log("blocked by safety filter, Argon rewrote the prompt"); continue
            raise
        if not needs_white:
            return raw
        ok, why = paper_ok(raw)
        if ok:
            return raw
        log(f"paper not keyable ({why}), repainting")
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--script", default=str(BOOK.game_dir / "script.json"))
    ap.add_argument("--towns", default="", help="only characters/cards appearing in these towns")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    raw_text = Path(a.script).read_text()
    g = json.loads(raw_text[raw_text.index("{"): raw_text.rindex("}") + 1])
    if a.towns:
        towns = set(a.towns.split(","))
        g["beats"] = [b for b in g["beats"] if b["town"] in towns]
        present = {n["character"] for b in g["beats"] for n in b["npcs"]} | {l["speaker"] for b in g["beats"] for l in b["lines"]} | {g["player"]["character"]}
        g["characters"] = [c for c in g["characters"] if c["id"] in present]
    (OUT / "portraits/raw").mkdir(parents=True, exist_ok=True)
    (OUT / "cards").mkdir(parents=True, exist_ok=True)
    mpath = OUT / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"portraits": {}, "cards": {}}

    jobs = []
    for c in g["characters"]:
        if (only and c["id"] not in only) or ((OUT / f"portraits/{c['id']}.png").exists() and not a.force):
            continue
        book_name = "Alice's Adventures in Wonderland" if BOOK.id == "alice" else "Les Misérables"
        jobs.append(("portrait", c["id"], f"Head-and-shoulders portrait of {c['name_fr']} from {book_name}: {c['portrait_prompt']} " + STYLE + CUTOUT, "3:4"))
    for b in g["beats"]:
        if not b.get("card_prompt") or (only and b["id"] not in only) or ((OUT / f"cards/{b['id']}.jpg").exists() and not a.force):
            continue
        jobs.append(("card", b["id"], b["card_prompt"] + " " + STYLE + CARD, "16:9"))

    t0 = time.time()

    def run(job):
        kind, key, prompt, aspect = job
        raw = paint_with_checks(prompt, aspect, kind == "portrait", lambda m: print(f"  ↻ {key}: {m}", flush=True))
        if kind == "portrait":
            (OUT / f"portraits/raw/{key}.jpg").write_bytes(raw)
            cut_out(raw).save(OUT / f"portraits/{key}.png", optimize=True)
        else:
            (OUT / f"cards/{key}.jpg").write_bytes(raw)
        return kind, key

    with ThreadPoolExecutor(8) as pool:
        futs = {pool.submit(run, j): j for j in jobs}
        for f in as_completed(futs):
            kind, key = futs[f][0], futs[f][1]
            try:
                f.result()
                manifest["portraits" if kind == "portrait" else "cards"][key] = True
                print(f"  {kind:<8} {key:<24} {time.time() - t0:.0f}s", flush=True)
            except Exception as ex:
                print(f"  ✗ {key}: {str(ex)[:160]}", flush=True)
    mpath.write_text(json.dumps(manifest, indent=1))
    print(f"done: {len(jobs)} images in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
