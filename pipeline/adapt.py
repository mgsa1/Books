"""Step [5] of the pipeline: starting game + story + style + assets -> a new game, by the Managed Agent.

Usage: uv run pipeline/adapt.py builds/<book> games/<game> [--fallback]

Packs the game's text files and the build's data into the agent's sandbox as inline sources,
runs the agent against prompts/adapt_contract.md, downloads the sandbox, and installs the result
at builds/<book>/game/ with the generated assets copied in. --fallback uses a direct Argon call
that returns the full file set as JSON instead of the agent.
"""
import argparse
import io
import json
import os
import shutil
import sys
import tarfile
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402

load_dotenv(C.ROOT / ".env")

TEXT_EXT = {".js", ".mjs", ".ts", ".json", ".html", ".htm", ".css", ".md", ".txt", ".glsl", ".xml", ".csv", ".yml", ".yaml"}
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".github", "lib", "libs", "vendor", "ios", "ios-native", "android", "tools"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "r.js"}
LICENSE_NAMES = {"LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE"}


SANDBOX_SKIP_DIRS = {".git", "node_modules", "dist", ".github"}  # the sandbox gets everything else that is text


def game_files(game_dir: Path, for_sandbox=False):
    """(relative path, content) text files, and a list of binary paths.

    for_sandbox=False: the files worth READING (no vendored libraries, no lockfiles, no native wrappers).
    for_sandbox=True: every text file the game needs to RUN, vendored libraries included."""
    texts, binaries = [], []
    skip_dirs = SANDBOX_SKIP_DIRS if for_sandbox else SKIP_DIRS
    for p in sorted(game_dir.rglob("*")):
        if not p.is_file() or any(part in skip_dirs for part in p.parts):
            continue
        rel = p.relative_to(game_dir).as_posix()
        if p.name in SKIP_FILES and not for_sandbox:
            continue
        if p.suffix.lower() in TEXT_EXT or p.name in LICENSE_NAMES:
            if for_sandbox or (p.stat().st_size < 400_000 and ".min." not in p.name):
                texts.append((rel, p.read_text(errors="ignore")))
            else:
                binaries.append(rel)
        else:
            binaries.append(rel)
    return texts, binaries


def git_remote(game_dir: Path):
    import subprocess
    r = subprocess.run(["git", "-C", str(game_dir), "config", "--get", "remote.origin.url"], capture_output=True, text=True)
    url = r.stdout.strip()
    return url if r.returncode == 0 and url.startswith("https://") else None


def workspace_sources(build: Path, game_dir: Path, texts, binaries, vendored=(), repo_url=None):
    if repo_url:  # the sandbox clones the game itself: complete repo, images included, no payload
        srcs = [{"type": "repository", "source": repo_url, "target": "/workspace/game"}]
    else:
        srcs = [{"type": "inline", "target": f"/workspace/game/{rel}", "content": content} for rel, content in texts]
    for name in ("story.json", "style.json", "selection.json", "slots.json"):
        if (build / name).exists():
            srcs.append({"type": "inline", "target": f"/workspace/{name}", "content": (build / name).read_text()})
    for name in ("manifest.json", "audio_manifest.json"):
        p = build / "assets" / name
        srcs.append({"type": "inline", "target": f"/workspace/assets/{name}",
                     "content": p.read_text() if p.exists() else "{}"})
    if not repo_url:
        srcs.append({"type": "inline", "target": "/workspace/UPSTREAM_BINARY_FILES.txt",
                     "content": "These upstream files exist but were not copied. Delete their references; replace with /workspace/assets.\n"
                                + "\n".join(binaries)})
    srcs.append({"type": "inline", "target": "/workspace/CONTRACT.md", "content": (C.PROMPTS / "adapt_contract.md").read_text()})
    srcs.append({"type": "inline", "target": "/workspace/VENDORED.txt",
                 "content": "Third-party libraries already present in the sandbox. Do not read, rewrite, or replace them.\n"
                            + "\n".join(vendored)})
    return srcs


def task_text(build: Path, game_dir: Path):
    sel = json.loads((build / "selection.json").read_text())["chapters"]
    story = json.loads((build / "story.json").read_text())
    return (f"Rewrite the game in /workspace/game (originally '{game_dir.name}') into a game called ExpLit that tells "
            f"'{story['title']}' from /workspace/story.json, chapters {sel} ONLY. Keep the scope minimal: one zone per listed "
            f"chapter, only the characters and items cast in the manifest, the chapter goal, nothing else from the original game's "
            f"world. The title screen and page title say 'ExpLit' with the book title under it; no trace of the original game's name. "
            f"Follow /workspace/CONTRACT.md exactly. "
            "Upstream image and audio files may be present; generated replacements are NOT. Their paths, sizes and texts are in "
            "/workspace/assets/manifest.json and /workspace/assets/audio_manifest.json, and they will be copied to "
            "/workspace/game/assets/ after you finish, so reference them by those relative paths. "
            "Third-party libraries listed in /workspace/VENDORED.txt are already in place; never rewrite them. "
            "Work in place. Delete upstream asset files and references. When done, write /workspace/CHECKS.md "
            "with one line per contract point and whether it holds.")


def download_environment(env_id: str, dest: Path) -> Path:
    url = f"{C.API_BASE}/files/environment-{env_id}:download"
    with httpx.Client(follow_redirects=True, timeout=600) as h:
        resp = h.get(url, params={"alt": "media"}, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
        resp.raise_for_status()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "environment.tar").write_bytes(resp.content)
    with tarfile.open(fileobj=io.BytesIO(resp.content)) as tar:
        tar.extractall(path=dest / "environment", filter="data")
    return dest / "environment"


def npm_build(game: Path):
    """If the game has a package.json with a build script, install and build it. Returns True if built."""
    import subprocess
    pkg = game / "package.json"
    if not pkg.exists() or "build" not in json.loads(pkg.read_text()).get("scripts", {}):
        return False
    for cmd in (["npm", "ci", "--no-audit", "--no-fund", "--silent"], ["npm", "run", "build", "--silent"]):
        r = subprocess.run(cmd, cwd=game, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            (game / "BUILD_ERROR.txt").write_text(r.stdout[-3000:] + "\n" + r.stderr[-3000:])
            print(f"  {' '.join(cmd)} failed; see {game / 'BUILD_ERROR.txt'}")
            return False
    print("  npm build ok")
    return True


def install(build: Path, workspace: Path):
    """Copy workspace/game into build/game, then overlay generated assets."""
    src = workspace / "game"
    if not src.exists():
        raise RuntimeError(f"no game folder in {workspace}")
    dst = build / "game"
    if dst.exists():
        shutil.move(str(dst), str(build / f"game.prev.{int(time.time())}"))
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("node_modules", ".git"))
    assets = build / "assets"
    if assets.exists():
        shutil.copytree(assets, dst / "assets", dirs_exist_ok=True)
        if (dst / "package.json").exists():  # Vite-style games copy public/ into dist/
            shutil.copytree(assets, dst / "public" / "assets", dirs_exist_ok=True)
    npm_build(dst)
    checks = workspace / "CHECKS.md"
    if checks.exists():
        shutil.copy(checks, build / "CHECKS.md")
    return dst


def run_agent(client, build, game_dir, max_tokens):
    texts, binaries = game_files(game_dir, for_sandbox=True)
    readable = {rel for rel, _ in game_files(game_dir)[0]}
    vendored = sorted(rel for rel, _ in texts if rel not in readable)
    print(f"packing {len(texts)} text files ({sum(len(c) for _, c in texts)//1000}k chars) into the sandbox, "
          f"{len(vendored)} vendored, {len(binaries)} binaries listed")
    t0 = time.time()
    repo_url = git_remote(game_dir)
    attempts = ([repo_url] if repo_url else []) + [None]
    for url in attempts:
        try:
            r = client.interactions.create(
                agent=C.AGENT,
                agent_config={**C.AGENT_CONFIG, "max_total_tokens": max_tokens},
                environment={"type": "remote", "sources": workspace_sources(build, game_dir, texts, binaries, vendored, url)},
                input=task_text(build, game_dir),
                background=True,
            )
            print(f"sandbox source: {'repository ' + url if url else 'inline files'}", flush=True)
            break
        except Exception as e:
            if url is None:
                raise
            print(f"repository source rejected ({str(e)[:120]}); falling back to inline files", flush=True)
    print(f"agent {r.id} env {r.environment_id}", flush=True)
    import signal
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        while r.status in ("queued", "in_progress"):
            time.sleep(20)
            r = client.interactions.get(r.id)
            print(f"  {r.status} {time.time()-t0:.0f}s", flush=True)
    except KeyboardInterrupt:  # Stop button or Ctrl-C: do not leave the agent running server-side
        try:
            client.interactions.cancel(r.id)
            print(f"  cancelled {r.id}", flush=True)
        finally:
            raise SystemExit(130)
    log = {"step": "adapt", "mode": "agent", "interaction_id": r.id, "environment_id": r.environment_id,
           "status": r.status, "seconds": round(time.time() - t0), "output_text": r.output_text}
    (build / "adapt.log.json").write_text(json.dumps(log, indent=1))
    if r.status not in ("completed", "incomplete"):
        raise RuntimeError(f"agent {r.status}")
    ws = download_environment(r.environment_id, build / "verification" / "adapt") / "workspace"
    return install(build, ws)


def run_fallback(client, build, game_dir):
    """Direct Argon call: whole repo in, whole repo out as {"files":[{"path","content"}]}."""
    texts, binaries = game_files(game_dir)
    schema = {"type": "object", "required": ["files", "checks"], "properties": {
        "files": {"type": "array", "items": {"type": "object", "required": ["path", "content"],
                  "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
        "checks": {"type": "string"}}}
    blob = "\n\n".join(f"===== {rel} =====\n{content}" for rel, content in texts)
    data = {n: (build / n).read_text() for n in ("story.json", "style.json", "selection.json", "slots.json") if (build / n).exists()}
    for n in ("manifest.json", "audio_manifest.json"):
        p = build / "assets" / n
        data[n] = p.read_text() if p.exists() else "{}"
    t0 = time.time()
    r = client.interactions.create(
        model=C.ARGON,
        system_instruction=(C.PROMPTS / "adapt_contract.md").read_text().replace("/workspace/", ""),
        input=f"{task_text(build, game_dir)}\n\nReturn every file of the new game (full content, no omissions) as JSON.\n\n"
              f"UPSTREAM BINARY FILES (not shown, delete references):\n{chr(10).join(binaries)}\n\n"
              + "".join(f"\n===== {k} =====\n{v}\n" for k, v in data.items()) + f"\n\nGAME SOURCE\n{blob}",
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "high"},
    )
    out = json.loads(r.output_text)
    ws = build / "verification" / "adapt" / "workspace"
    shutil.rmtree(ws, ignore_errors=True)
    for f in out["files"]:
        p = ws / "game" / f["path"].lstrip("/").removeprefix("game/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"])
    (ws / "CHECKS.md").write_text(out["checks"])
    (build / "adapt.log.json").write_text(json.dumps({"step": "adapt", "mode": "fallback", "interaction_id": r.id,
                                                      "seconds": round(time.time() - t0), "files": len(out["files"])}, indent=1))
    return install(build, ws)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("game_dir")
    ap.add_argument("--fallback", action="store_true", help="direct Argon call instead of the Managed Agent")
    ap.add_argument("--max-tokens", type=int, default=2_000_000)
    a = ap.parse_args()
    client = genai.Client()
    dst = (run_fallback if a.fallback else run_agent)(client, Path(a.build), Path(a.game_dir), *([] if a.fallback else [a.max_tokens]))
    print(f"installed -> {dst}")
