"""One command, all steps, resumable. Each step is skipped when its output already exists.

Usage:
  uv run pipeline/run.py ressources/alice_in_wonderland.epub --game veilspire \
      --chapters c01 c02 --brief "soft watercolour storybook" [--refs ressources/style] [--fallback] [--only story voice]

Steps: ingest -> story -> slots -> style -> voice -> adapt -> verify
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402
from pipeline.ingest import ingest  # noqa: E402

STEPS = ["ingest", "story", "slots", "style", "voice", "adapt", "verify"]


def sh(*args):
    print("$", " ".join(str(a) for a in args), flush=True)
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    subprocess.run([sys.executable, *[str(a) for a in args]], check=True, cwd=C.ROOT, env=env)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book", help="EPUB path")
    ap.add_argument("--game", required=True, help="folder name under games/")
    ap.add_argument("--chapters", nargs="+", required=True)
    ap.add_argument("--brief", default=None)
    ap.add_argument("--refs", default=str(C.RESSOURCES / "style"))
    ap.add_argument("--fallback", action="store_true", help="adapt with a direct Argon call instead of the Managed Agent")
    ap.add_argument("--only", nargs="+", choices=STEPS, default=STEPS)
    ap.add_argument("--force", nargs="*", choices=STEPS, default=[], help="rerun these even if output exists")
    a = ap.parse_args()
    game_dir = C.GAMES / a.game
    if not game_dir.exists():
        sys.exit(f"clone the starting game first: git clone --depth 1 <repo> {game_dir}")

    def want(step, output: Path):
        return step in a.only and (step in a.force or not output.exists())

    book, build = ingest(Path(a.book))  # cheap and deterministic, always run
    (build / "selection.json").write_text(json.dumps({"chapters": a.chapters}))
    print(f"build: {build}  chapters {a.chapters}")
    P = C.ROOT / "pipeline"
    if want("story", build / "story.json"):
        sh(P / "story.py", build)
    needs_slots = want("slots", build / "slots.json") or (
        ("style" in a.only or "adapt" in a.only) and not (build / "slots.json").exists())
    if needs_slots:
        sh(P / "slots.py", game_dir, "--out", build / "slots.json")
    cast = build / "cast.json"
    style_done = (build / "assets" / "manifest.json").exists() and cast.exists() and \
        json.loads(cast.read_text()).get("selection") == a.chapters and json.loads(cast.read_text()).get("filled") is True
    if "style" in a.only and ("style" in a.force or not style_done):
        sh(P / "style.py", build, *(["--brief", a.brief] if a.brief else []), "--refs", a.refs)
    am = build / "assets" / "audio_manifest.json"
    voiced = set(json.loads(am.read_text()).get("_chapters", [])) if am.exists() else set()
    if "voice" in a.only and ("voice" in a.force or not set(a.chapters) <= voiced):
        sh(P / "voice.py", build, *a.chapters)
    if want("adapt", build / "game" / "index.html"):
        sh(P / "adapt.py", build, game_dir, *(["--fallback"] if a.fallback else []))
    if want("verify", build / "verification" / "report.json"):
        sh(P / "verify.py", build)
    print(f"\ndone. play:  cd {build / 'game'} && python -m http.server 8000")
    print(f"watch a session:  uv run pipeline/watch.py {build} <session.json>")


if __name__ == "__main__":
    main()
