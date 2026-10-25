"""Shared playthrough driver: serve a game folder, drive window.playtest with Playwright, record evidence.

evidence dir gets: shots/NNN_label.png, events.jsonl, result.json {score, errors, steps}.
Score counts passed steps so repairs can be compared objectively.
"""
import base64
import functools
import http.server
import json
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a, **k):
        pass


class Server:
    def __init__(self, root: Path):
        handler = functools.partial(Quiet, directory=str(root))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def playthrough(game_dir: Path, evidence: Path, story: dict, selection: list, per_step_wait=0.8, timeout_s=90):
    evidence.mkdir(parents=True, exist_ok=True)
    shots = evidence / "shots"
    shots.mkdir(exist_ok=True)
    events, steps, errors = [], [], []
    n = [0]
    server = Server(game_dir)

    def log(kind, **kw):
        events.append({"t": round(time.time() - t0, 2), "kind": kind, **kw})

    def shot(page, label):
        n[0] += 1
        p = shots / f"{n[0]:03d}_{label}.png"
        page.screenshot(path=str(p))
        log("screenshot", file=p.name)
        return p.name

    def step(name, ok, detail=""):
        steps.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
        log("step", name=name, ok=bool(ok), detail=str(detail)[:300])

    t0 = time.time()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.on("console", lambda m: (errors.append(m.text), log("console_error", text=m.text)) if m.type == "error" else None)
        page.on("pageerror", lambda e: (errors.append(str(e)), log("page_error", text=str(e))))
        try:
            page.goto(f"http://127.0.0.1:{server.port}/index.html", wait_until="load", timeout=30_000)
            try:
                page.wait_for_function("() => window.playtest && typeof window.playtest.state === 'function'", timeout=20_000)
                step("playtest_api", True)
            except Exception as e:
                step("playtest_api", False, e)
                shot(page, "no_playtest")
                raise
            page.keyboard.press("Space")  # dismiss a start screen if any
            time.sleep(per_step_wait)
            shot(page, "start")
            api = "window.playtest"
            chars = page.evaluate(f"() => {api}.characters()") or []
            items = page.evaluate(f"() => {api}.items()") or []
            log("inventory", characters=chars, items=items)
            wanted_chars = [c["id"] for c in story["characters"]
                            if any(c["first_chapter"] <= ch <= c["last_chapter"] for ch in selection)]
            wanted_items = [i["id"] for i in story["items"] if i["chapter"] in selection]
            have_chars = {c["id"] if isinstance(c, dict) else c for c in chars}
            have_items = {i["id"] if isinstance(i, dict) else i for i in items}
            for cid in wanted_chars:
                step(f"character_present:{cid}", cid in have_chars)
            for iid in wanted_items:
                step(f"item_present:{iid}", iid in have_items)
            for cid in wanted_chars:
                if cid not in have_chars or time.time() - t0 > timeout_s:
                    continue
                page.evaluate(f"() => {api}.goto('{cid}')")
                time.sleep(per_step_wait)
                before = page.evaluate(f"() => JSON.stringify({api}.state())")
                page.evaluate(f"() => {api}.talk()")
                time.sleep(per_step_wait)
                after = page.evaluate(f"() => JSON.stringify({api}.state())")
                shot(page, f"talk_{cid}")
                step(f"talk:{cid}", before != after, "state unchanged after talk" if before == after else "")
            for iid in wanted_items:
                if iid not in have_items or time.time() - t0 > timeout_s:
                    continue
                page.evaluate(f"() => {api}.goto('{iid}')")
                time.sleep(per_step_wait)
                page.evaluate(f"() => {api}.collect()")
                time.sleep(per_step_wait)
                st = page.evaluate(f"() => {api}.state()") or {}
                got = []
                for k in ("items_collected", "itemsCollected", "collected", "inventory", "items"):
                    v = st.get(k)
                    if isinstance(v, list):
                        got += [x.get("id", x) if isinstance(x, dict) else x for x in v]
                    elif isinstance(v, dict):
                        got += [k2 for k2, v2 in v.items() if v2]
                collected = iid in got
                shot(page, f"collect_{iid}")
                step(f"collect:{iid}", collected, json.dumps(st)[:200])
            st = page.evaluate(f"() => {api}.state()") or {}
            log("final_state", state=st)
            shot(page, "end")
            step("no_console_errors", not errors, errors[:3])
        except Exception as e:
            log("abort", error=str(e)[:300])
        finally:
            browser.close()
            server.close()
    (evidence / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
    result = {"score": sum(s["ok"] for s in steps), "total": len(steps), "errors": errors[:20], "steps": steps,
              "seconds": round(time.time() - t0, 1)}
    (evidence / "result.json").write_text(json.dumps(result, indent=1))
    return result


def data_url_to_png(data_url: str, path: Path):
    path.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
