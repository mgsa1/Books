"""Local UI for ExpLit. Standard library only.

Run: uv run server.py   then open http://127.0.0.1:8765
Serves web/index.html, a small JSON API, and the built games under /play/<build>/.
"""
import json
import os
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import config as C  # noqa: E402

PORT = int(os.environ.get("PORT", 8765))
JOBS = {}  # build slug -> {"proc", "log", "started", "args"}
STEP_FILES = [("ingest", "book.json"), ("story", "story.json"), ("slots", "slots.json"), ("style", "assets/manifest.json"),
              ("voice", "assets/audio_manifest.json"), ("adapt", "game/index.html"), ("verify", "verification/report.json")]
# a game's own build output (dist/) is detected by config.playable_dir


def build_status(b: Path):
    job = JOBS.get(b.name)
    running = bool(job and job["proc"].poll() is None)
    steps = {name: (b / f).exists() for name, f in STEP_FILES}
    info = {"slug": b.name, "steps": steps, "running": running, "title": b.name}
    if (b / "book.json").exists():
        bk = json.loads((b / "book.json").read_text())
        info.update(title=bk["title"], author=bk["author"], chapters=[{"id": c["id"], "title": c["title"]} for c in bk["chapters"]])
    if (b / "selection.json").exists():
        info["selection"] = json.loads((b / "selection.json").read_text())["chapters"]
    if (b / "story.json").exists():
        st = json.loads((b / "story.json").read_text())
        info["story"] = {"characters": len(st["characters"]), "beats": sum(len(c["beats"]) for c in st["chapters"]),
                         "lines": len(st["lines"]), "items": len(st["items"])}
    if (b / "verification" / "report.json").exists():
        info["report"] = json.loads((b / "verification" / "report.json").read_text())
    if job:
        info["exit"] = job["proc"].poll()
    return info


def library():
    """Playable games: finished builds plus sandbox previews from pipeline/peek.py."""
    out = []
    for b in sorted(C.BUILDS.iterdir()):
        if not b.is_dir():
            continue
        preview = b.name.startswith("_preview_")
        if b.name.startswith("_") and not preview:
            continue
        index = C.playable_dir(b) / "index.html"
        if not index.exists():
            continue
        src = C.BUILDS / b.name[len("_preview_"):] if preview else b  # previews borrow the parent build's book and art
        info = build_status(src) if src.exists() else {"slug": b.name, "title": b.name}
        a = src / "assets"
        covers = sorted(a.glob("backdrop/chapter_backdrop_*.jpg")) + sorted(a.glob("backdrop/*.jpg")) + sorted(a.glob("backdrop/*.png"))
        titles = {c["id"]: c["title"] for c in info.get("chapters", [])}
        out.append({
            "slug": b.name, "preview": preview, "title": info.get("title", b.name), "author": info.get("author", ""),
            "chapters": [{"id": c, "title": titles.get(c, c)} for c in info.get("selection", [])],
            "cover": f"/evidence/{src.name}/{covers[0].relative_to(src)}" if covers else None,
            "portraits": [f"/evidence/{src.name}/{q.relative_to(src)}" for q in sorted(a.glob("portrait/*.png"))[:6]],
            "score": (info.get("report") or {}).get("final_score"),
            "running": info.get("running", False),
            "built": time.strftime("%d %b %H:%M", time.localtime(index.stat().st_mtime)),
        })
    out.sort(key=lambda e: (e["preview"], e["title"]))
    return out


def start_job(slug, args):
    b = C.BUILDS / slug
    b.mkdir(parents=True, exist_ok=True)
    log = open(b / "run.log", "a")
    log.write(f"\n=== {time.strftime('%H:%M:%S')} $ {' '.join(args)}\n")
    log.flush()
    proc = subprocess.Popen([sys.executable, *args], cwd=C.ROOT, stdout=log, stderr=subprocess.STDOUT,
                            env={**os.environ, "PYTHONUNBUFFERED": "1"})
    JOBS[slug] = {"proc": proc, "log": b / "run.log", "started": time.time(), "args": args}
    return proc


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(C.ROOT / "web"), **k)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/state":
            books = sorted(p.name for p in C.RESSOURCES.glob("*.epub"))
            games = sorted(p.name for p in C.GAMES.iterdir() if p.is_dir()) if C.GAMES.exists() else []
            refs = sorted(p.name for p in (C.RESSOURCES / "style").glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
            builds = [build_status(b) for b in sorted(C.BUILDS.iterdir()) if b.is_dir() and not b.name.startswith("_")]
            return self.send_json({"books": books, "games": games, "refs": refs, "builds": builds, "library": library(),
                                   "has_key": bool(os.environ.get("GEMINI_API_KEY"))})
        if u.path == "/api/log":
            p = C.BUILDS / q["build"][0] / "run.log"
            text = p.read_text(errors="ignore") if p.exists() else ""
            if "all" not in q and "\n=== " in text:
                text = "=== " + text.rsplit("\n=== ", 1)[1]  # latest run only; ?all=1 for the full file
            text = text[-20000:]
            return self.send_json({"log": text, **build_status(C.BUILDS / q["build"][0])})
        if u.path == "/api/story":
            p = C.BUILDS / q["build"][0] / "story.json"
            return self.send_json(json.loads(p.read_text()) if p.exists() else {})
        if u.path.startswith("/play/"):
            rel = u.path[len("/play/"):]
            slug, _, rest = rel.partition("/")
            target = (C.playable_dir(C.BUILDS / slug) / (rest or "index.html")).resolve()
            if not str(target).startswith(str(C.BUILDS.resolve())) or not target.is_file():
                return self.send_error(404)
            self.directory = str(target.parent)
            self.path = "/" + target.name
            return super().do_GET()
        if u.path.startswith("/evidence/"):
            target = (C.BUILDS / u.path[len("/evidence/"):]).resolve()
            if not str(target).startswith(str(C.BUILDS.resolve())) or not target.is_file():
                return self.send_error(404)
            self.directory = str(target.parent)
            self.path = "/" + target.name
            return super().do_GET()
        if u.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/upload":  # raw body, ?kind=book|style|session&name=file
            kind, name = q["kind"][0], Path(q["name"][0]).name
            dest = {"book": C.RESSOURCES, "style": C.RESSOURCES / "style", "session": C.BUILDS / "_sessions"}[kind]
            dest.mkdir(parents=True, exist_ok=True)
            (dest / name).write_bytes(self.body())
            return self.send_json({"saved": str(dest / name)})
        req = json.loads(self.body() or b"{}")
        if u.path == "/api/run":
            from pipeline.ingest import ingest
            book, b = ingest(C.RESSOURCES / Path(req["book"]).name)
            if b.name in JOBS and JOBS[b.name]["proc"].poll() is None:
                return self.send_json({"error": "already running"}, 409)
            refs = [p for p in (C.RESSOURCES / "style").glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")]
            if "style" in (req.get("only") or ["style"]) and not req.get("brief") and not refs:
                return self.send_json({"error": "Give a style brief or upload reference images before building."}, 400)
            args = [str(C.ROOT / "pipeline" / "run.py"), str(C.RESSOURCES / Path(req["book"]).name),
                    "--game", req["game"], "--chapters", *req["chapters"]]
            if req.get("brief", "").strip():
                args += ["--brief", req["brief"].strip()]
            if req.get("fallback"):
                args.append("--fallback")
            if req.get("only"):
                args += ["--only", *req["only"]]
            if req.get("force"):
                args += ["--force", *req["force"]]
            start_job(b.name, args)
            return self.send_json({"build": b.name})
        if u.path == "/api/watch":
            slug, session = req["build"], C.BUILDS / "_sessions" / Path(req["session"]).name
            start_job(slug, [str(C.ROOT / "pipeline" / "watch.py"), str(C.BUILDS / slug), str(session)])
            return self.send_json({"build": slug})
        if u.path == "/api/stop":
            job = JOBS.get(req["build"])
            if job and job["proc"].poll() is None:
                job["proc"].terminate()
            return self.send_json({"stopped": True})
        return self.send_error(404)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(C.ROOT / ".env")
    C.BUILDS.mkdir(exist_ok=True)
    print(f"ExpLit UI: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
