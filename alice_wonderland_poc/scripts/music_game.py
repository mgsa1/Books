"""Background music: Argon writes a brief per area (from the script), Lyria composes a 30 s loop for
each area plus a title theme. Checked afterwards (duration, no vocals) by scripts/verify_audio.py --music.

    BOOK=alice .venv/bin/python -I scripts/music_game.py          # writes <assets>/music/<town>.mp3, title.mp3
"""
import argparse
import base64
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from argon import ask, client  # noqa: E402
from books import BOOK  # noqa: E402

LYRIA = "lyria-3-clip-preview"


def briefs(g, out):
    path = out / "briefs.json"
    if path.exists():
        return json.loads(path.read_text())
    towns = [{"id": t["id"], "name": t["name_fr"], "layout": t.get("layout_en", ""),
              "beats": [b["objective_en"] for b in g["beats"] if b["town"] == t["id"]]} for t in g["towns"]]
    book = "Alice's Adventures in Wonderland (1865)" if BOOK.id == "alice" else "Les Misérables (Victor Hugo, 1815-1823)"
    it = ask(f"""Write music briefs for the background loops of a cosy retro top-down video game adapting {book}.
Areas: {json.dumps(towns, ensure_ascii=False)}
For each area id, and for "title" (the title screen), write ONE prompt for a music model: instrumental only, seamless loop,
instruments, tempo, mood, period colour; 25-45 words; no artist names. Keep them recognisably one soundtrack (shared motif/palette).
Return only JSON: {{"title": "...", "<area id>": "..."}}""", level="low")
    t = it.output_text
    b = json.loads(t[t.index("{"): t.rindex("}") + 1])
    path.write_text(json.dumps(b, ensure_ascii=False, indent=1))
    return b


def compose(prompt):
    it = client.interactions.create(model=LYRIA, input=prompt + " Instrumental, no vocals, seamless loop for a video game.",
                                    response_modalities=["audio"])
    d = it.output_audio.data
    return base64.b64decode(d) if isinstance(d, str) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    g = json.loads((BOOK.game_dir / "script.json").read_text())
    out = BOOK.assets_dir / "music"
    out.mkdir(parents=True, exist_ok=True)
    b = briefs(g, out)
    todo = [k for k in b if (not only or k in only) and (a.force or not (out / f"{k}.mp3").exists())]
    t0 = time.time()

    def run(k):
        for attempt in range(3):
            try:
                (out / f"{k}.mp3").write_bytes(compose(b[k])); return k
            except Exception as ex:
                if attempt == 2:
                    raise
                time.sleep(3)

    with ThreadPoolExecutor(6) as pool:
        for k in pool.map(run, todo):
            print(f"  ♪ {k:<16} {time.time() - t0:.0f}s  — {b[k][:80]}", flush=True)
    mpath = BOOK.assets_dir / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    manifest["music"] = sorted(p.stem for p in out.glob("*.mp3"))
    mpath.write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
