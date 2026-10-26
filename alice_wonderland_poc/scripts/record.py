"""Record an autopilot play-through on localhost: 1080p video (visible Chrome, real GPU) + the event log.

    python3 -I scripts/record.py alice --from 0 --until 12        # beats [from, until)
-> recordings/<book>_<from>-<until>/video.webm, events.json (event times already mapped to video seconds)
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from render import PORT, server  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("book")
ap.add_argument("--from", dest="start", type=int, default=0)
ap.add_argument("--until", type=int, default=None)
ap.add_argument("--width", type=int, default=1920)
ap.add_argument("--height", type=int, default=1080)
ap.add_argument("--zoom", type=float, default=0, help="tiles visible vertically (game default 15; ~10 for video)")
ap.add_argument("--title", type=float, default=0, help="seconds to hold the title screen (with its theme) before starting")
a = ap.parse_args()

out = ROOT / "recordings" / f"{a.book}_{a.start}-{a.until if a.until is not None else 'end'}"
if out.exists():
    shutil.rmtree(out)
(out / "raw").mkdir(parents=True)
query = ("book=" + a.book + "&" if a.book != "lesmis" else "") + "autopilot=1" + (f"&zoom={a.zoom}" if a.zoom else "")

with server(), sync_playwright() as pw:
    # headless but on the real GPU (ANGLE/Metal): 60 fps, and no oversized window popping up on a laptop screen
    browser = pw.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required", "--mute-audio",
                                                      "--use-angle=metal", "--enable-gpu", "--ignore-gpu-blocklist"])
    ctx = browser.new_context(viewport={"width": a.width, "height": a.height}, device_scale_factor=1,
                              record_video_dir=str(out / "raw"), record_video_size={"width": a.width, "height": a.height})
    page = ctx.new_page()
    t_video0 = time.time()  # the video starts when the page is created
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://127.0.0.1:{PORT}/viewer/game.html?{query}")
    page.wait_for_function("window.__ready === true", timeout=60000)
    origin = page.evaluate("performance.timeOrigin") / 1000  # epoch seconds of performance.now() == 0
    page.wait_for_timeout(1200)
    if a.start:
        page.evaluate(f"__game.skipTo({a.start})")
    else:
        if a.title:  # any non-space key starts the title theme (browsers need a gesture), then hold on the title
            page.keyboard.press("Shift"); page.wait_for_timeout(int(a.title * 1000))
        page.keyboard.press("Space")
    n = page.evaluate("__game.script.beats.length")
    until = min(a.until if a.until is not None else n, n)
    # every beat should finish within ~3 min; the whole run has a hard cap
    page.wait_for_function(f"__game.S.beat >= {until} || __game.S.beat >= __game.script.beats.length", timeout=1200000, polling=500)
    page.wait_for_timeout(2500)
    events = page.evaluate("__game.events")
    duration = time.time() - t_video0
    ctx.close()  # flushes the video
    browser.close()

offset = origin - t_video0
for e in events:
    e["video_s"] = round(e["t"] / 1000 + offset, 3)
vid = next((out / "raw").glob("*.webm"))
vid.rename(out / "video.webm")
(out / "raw").rmdir()
meta = {"book": a.book, "from": a.start, "until": until, "duration_s": round(duration, 1), "offset_s": round(offset, 3),
        "size": [a.width, a.height], "errors": errors}
(out / "events.json").write_text(json.dumps({"meta": meta, "events": events}, ensure_ascii=False, indent=1))
print(json.dumps(meta, indent=1))
print(f"{len(events)} events · violations: {[e for e in events if e['type'] in ('violation', 'error')] or 'none'}")
print(out.relative_to(ROOT))
