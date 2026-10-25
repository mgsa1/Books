"""Peek at a build while it runs: snapshot the agent's sandbox as a preview game, and build an asset gallery.

Usage: uv run pipeline/peek.py builds/<book>
Writes builds/_preview_<slug>/game (served at /play/_preview_<slug>/) and builds/_preview_<slug>/gallery.html
(served at /evidence/_preview_<slug>/gallery.html). Safe to run repeatedly.
"""
import json
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402
from pipeline.adapt import download_environment  # noqa: E402

load_dotenv(C.ROOT / ".env")


def gallery(build: Path, out: Path):
    m = json.loads((build / "assets" / "manifest.json").read_text())
    rows = []
    for sid, subjects in m["fills"].items():
        for subj, e in subjects.items():
            if not e.get("path"):
                continue
            rows.append(f'<figure><img src="/evidence/{build.name}/{e["path"]}" loading="lazy"><figcaption><b>{sid}</b> ← {subj}'
                        f'<br><small>{e.get("width")}×{e.get("height")} {e.get("degraded", "")} {"MISSING" if e.get("missing") else ""}</small></figcaption></figure>')
    html = ("<!doctype html><meta charset=utf-8><title>Fills</title><style>body{font-family:Verdana,sans-serif;background:#eee;margin:16px}"
            ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}figure{margin:0;background:#fff;padding:8px;border-radius:8px}"
            "img{max-width:100%;image-rendering:pixelated;background:repeating-conic-gradient(#ddd 0 25%,#fff 0 50%) 0 0/16px 16px}figcaption{font-size:13px}</style>"
            f"<h2>{len(rows)} filled slots · removed {len(m.get('remove', []))} · kept upstream {len(m.get('kept_upstream', []))} · missing {m.get('missing')}</h2>"
            f"<div class=g>{''.join(rows)}</div>")
    out.write_text(html)


def snapshot(build: Path, out_game: Path):
    log = build / "run.log"
    envs = re.findall(r"agent (\S+) env ([0-9a-f]+)", log.read_text()) if log.exists() else []
    if not envs:
        print("no agent environment in the log yet"); return None
    iid, env = envs[-1]
    ws = download_environment(env, build / "verification" / "peek") / "workspace"
    if not (ws / "game").exists():
        print("sandbox has no workspace/game yet"); return None
    shutil.rmtree(out_game, ignore_errors=True)
    shutil.copytree(ws / "game", out_game, ignore=shutil.ignore_patterns("node_modules", ".git"))
    if (build / "assets").exists():
        shutil.copytree(build / "assets", out_game / "assets", dirs_exist_ok=True)
    checks = ws / "CHECKS.md"
    print(f"snapshot of {env} (interaction {iid[:16]}…): {sum(1 for _ in out_game.rglob('*'))} files")
    if checks.exists():
        print("--- CHECKS.md ---\n" + checks.read_text()[:2000])
    return out_game


if __name__ == "__main__":
    build = Path(sys.argv[1])
    out = C.BUILDS / f"_preview_{build.name}"
    out.mkdir(parents=True, exist_ok=True)
    gallery(build, out / "gallery.html")
    print(f"gallery:  http://127.0.0.1:8765/evidence/{out.name}/gallery.html")
    if snapshot(build, out / "game"):
        print(f"preview:  http://127.0.0.1:8765/play/{out.name}/")
