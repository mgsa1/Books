"""Headless play-through: for every beat, go to its trigger, play it, screenshot the first line.

    python3 -I scripts/playtest.py digne      -> renders_game/*.png + report
Fails loudly if a beat cannot be triggered (unreachable target, missing NPC...).
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from render import PORT, server  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--from=")]
START = next((int(a.split("=")[1]) for a in sys.argv[1:] if a.startswith("--from=")), 0)
towns = args[0] if args else "digne"
import os
OUT = ROOT / "renders_game"
OUT.mkdir(exist_ok=True)
NEIGH = [(0, 1, "ArrowUp"), (0, -1, "ArrowDown"), (1, 0, "ArrowLeft"), (-1, 0, "ArrowRight")]  # stand here, press this to step onto target

report = {"errors": [], "beats": []}
with server(), sync_playwright() as pw:
    b = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    p = b.new_page(viewport={"width": 1440, "height": 860})
    p.on("console", lambda m: m.type == "error" and report["errors"].append(m.text))
    p.on("pageerror", lambda e: report["errors"].append(str(e)))
    import os
    book = os.environ.get("BOOK")  # BOOK=alice → ?book=alice (default: Les Mis)
    p.goto(f"http://127.0.0.1:{PORT}/viewer/game.html?towns={towns}" + (f"&book={book}" if book and book != "lesmis" else ""))
    p.wait_for_function("window.__ready === true", timeout=60000)
    p.wait_for_timeout(1500)
    p.screenshot(path=OUT / "00_title.png")
    if START:
        p.evaluate(f"__game.skipTo({START})")
    else:
        p.keyboard.press("Space")
    p.wait_for_timeout(1500)
    n = p.evaluate("__game.script.beats.length")

    def drain(i):
        shot = False
        for _ in range(40):
            if p.evaluate("__game.S.beat") != i:  # a following "start" beat begins by itself: leave it to the next iteration
                return True
            if p.evaluate("__game.inDialogue()"):
                if not shot:
                    p.wait_for_timeout(900)
                    p.screenshot(path=OUT / f"{i + 1:02d}_{beat['id']}.png"); shot = True
                # one press at a time: a stray second press after the beat ends opens an idle chat line
                p.keyboard.press("Space"); p.wait_for_timeout(260)
            elif p.evaluate("__game.S.beat") != i:
                return True
            else:
                p.wait_for_timeout(400)
        return p.evaluate("__game.S.beat") != i

    for i in range(START, n):
        p.wait_for_function(f"__game.S.beat === {i} && (!__game.busy() || __game.inDialogue())", timeout=30000)
        beat = p.evaluate(f"__game.script.beats[{i}]")
        tr = beat["trigger"]
        entry = {"id": beat["id"], "trigger": tr}
        if tr["type"] != "start":
            # stray Space presses from the previous beat can open idle chatter with a bystander: close it first
            for _ in range(10):
                if not p.evaluate(f"__game.inDialogue() && __game.S.beat === {i} && !__game.busy()"):
                    break
                p.keyboard.press("Space"); p.wait_for_timeout(200); p.keyboard.press("Space"); p.wait_for_timeout(250)
        if tr["type"] == "start" or p.evaluate("__game.busy()"):
            ok = drain(i)
        else:
            w = p.evaluate("__game.world.m")
            if tr["type"] == "talk":
                target = p.evaluate("__game.npcs()").get(tr["target"])
            elif tr["type"] == "enter":
                target = next((bb["door"] for bb in w["buildings"] if bb["id"] == tr["target"]), None)
            else:
                target = w["spots"].get(tr["target"])
            if not target:
                entry["error"] = "trigger target not found on the map"; report["beats"].append(entry); break
            tx, ty = target
            placed = False
            for ox, oy, key in NEIGH:
                sx, sy = tx + ox, ty + oy
                if not p.evaluate(f"__game.occupied({sx},{sy})"):
                    p.evaluate(f"__game.teleport({sx},{sy})"); p.wait_for_timeout(300)
                    if tr["type"] == "talk":
                        for _ in range(3):  # retry: a key can land between animation frames
                            p.keyboard.press("Space"); p.wait_for_timeout(600)
                            if p.evaluate(f"__game.inDialogue() || __game.S.beat !== {i}"):
                                break
                    else:
                        for _ in range(4):  # retry the step if the frame loop missed the key
                            p.keyboard.down(key); p.wait_for_timeout(450); p.keyboard.up(key); p.wait_for_timeout(500)  # headless frames are slow: hold across several
                            if p.evaluate(f"__game.busy() || __game.S.beat !== {i}"):  # story dialogue, not idle chat
                                break
                            if p.evaluate("__game.inDialogue()"):  # an idle chat line swallowed the step: close it
                                p.keyboard.press("Space"); p.wait_for_timeout(300)
                            print("      retry", key, "from", (sx, sy), p.evaluate("__game.debug()"), flush=True)
                            p.evaluate(f"__game.teleport({sx},{sy})"); p.wait_for_timeout(200)
                    placed = True; break
            if not placed:
                entry["error"] = f"no free tile next to {tr['target']} at {target}"; report["beats"].append(entry); break
            p.wait_for_timeout(700)
            ok = drain(i)
        entry["ok"] = ok
        report["beats"].append(entry)
        print(f"  {'✓' if ok else '✗'} {beat['id']:<22} {tr['type']:<5} {tr.get('target') or ''}", flush=True)
        if not ok:
            print("    state:", p.evaluate("({beat: __game.S.beat, busy: __game.busy(), dlg: __game.inDialogue(), me: [__game.S.px, __game.S.py], npcs: __game.npcs(), title: document.querySelector('#title').style.display, travel: document.querySelector('#travel').style.display, card: document.querySelector('#card').style.display})"))
            print("    debug:", p.evaluate("__game.debug()"))
            if tr["type"] in ("enter", "reach"):
                print("    occupied(target):", p.evaluate(f"__game.occupied({tx},{ty})"), "target", (tx, ty))
                p.keyboard.down("ArrowRight"); p.wait_for_timeout(450)
                print("    while holding →:", p.evaluate("__game.debug()"))
                p.keyboard.up("ArrowRight"); p.wait_for_timeout(600)
                print("    after:", p.evaluate("__game.debug()"))
            p.screenshot(path=OUT / f"{i + 1:02d}_{beat['id']}_STUCK.png"); break
    p.wait_for_timeout(1500)
    p.screenshot(path=OUT / "99_end.png")
    b.close()
(OUT / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
print("errors:", report["errors"] or "none")
