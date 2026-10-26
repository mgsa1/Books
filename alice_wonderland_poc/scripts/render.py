"""Render a scene headlessly: screenshots + a machine-readable report.

    python3 scripts/render.py huaguoshan            # writes renders/huaguoshan/*.png + report.json

Report: console errors, bible objects with no mesh, and per-object visibility
(fraction of a close-up view the object fills). Used by the verification loop.
Needs a static server on :8765 serving the project root (started automatically).
"""
import contextlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765


@contextlib.contextmanager
def server():
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", PORT)) == 0:  # already running
            yield
            return
    p = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
                         cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    try:
        yield
    finally:
        p.terminate()


# Renders each object alone (others hidden) from the current camera and counts covered pixels.
COVERAGE_JS = """
async () => {
  const { meshes } = window.__scene;
  const canvas = document.querySelector('canvas');
  const out = {};
  const all = Object.entries(meshes);
  const prev = all.map(([id, o]) => o.visible);
  const grab = async () => {
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const c = document.createElement('canvas'); c.width = 160; c.height = 100;
    const g = c.getContext('2d'); g.drawImage(canvas, 0, 0, 160, 100);
    return g.getImageData(0, 0, 160, 100).data;
  };
  // baseline: every registered object hidden (ground, decor, sky remain)
  all.forEach(([_, m]) => m.visible = false);
  const base = await grab();
  for (const [id, o] of all) {
    all.forEach(([_, m]) => m.visible = (m === o));
    const d = await grab();
    let n = 0;  // pixels this object changes vs. the baseline
    for (let i = 0; i < d.length; i += 4)
      if (Math.abs(d[i]-base[i]) + Math.abs(d[i+1]-base[i+1]) + Math.abs(d[i+2]-base[i+2]) > 30) n++;
    out[id] = +(n / 16000).toFixed(4);
  }
  all.forEach(([_, m], i) => m.visible = prev[i]);
  return out;
}
"""


def render(world_id, views=("start",)):
    outdir = ROOT / "renders" / world_id
    outdir.mkdir(parents=True, exist_ok=True)
    report = {"world": world_id, "errors": [], "shots": []}
    with server(), sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = browser.new_page(viewport={"width": 1440, "height": 860})
        page.on("console", lambda m: m.type == "error" and report["errors"].append(m.text))
        page.on("pageerror", lambda e: report["errors"].append(str(e)))
        page.goto(f"http://127.0.0.1:{PORT}/viewer/index.html?world={world_id}")
        try:
            page.wait_for_function("window.__ready === true", timeout=60000)
        except Exception as e:
            report["errors"].append(f"scene never became ready: {e}")
            page.screenshot(path=outdir / "start.png")
            browser.close()
            return report
        page.wait_for_timeout(2500)
        page.screenshot(path=outdir / "start.png")
        report["shots"].append(str(outdir / "start.png"))
        report["missing_meshes"] = page.evaluate("window.__scene.missing")
        report["coverage_from_start"] = page.evaluate(COVERAGE_JS)
        # close-up of each object via the panel index (exercises the fly-to + selection path)
        ids = page.evaluate("window.__scene.world.objects.map(o => o.id)")
        for oid in ids:
            page.click(f'#index li[data-id="{oid}"]')
            page.wait_for_timeout(1700)
            shot = outdir / f"obj_{oid}.png"
            page.locator("#stage").screenshot(path=shot)
            report["shots"].append(str(shot))
        browser.close()
    (outdir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == "__main__":
    r = render(sys.argv[1] if len(sys.argv) > 1 else "huaguoshan")
    print(json.dumps({k: v for k, v in r.items() if k != "shots"}, indent=2, ensure_ascii=False))
