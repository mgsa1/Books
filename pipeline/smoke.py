"""Step 1 of PLAN.md: four smoke tests, one file each in builds/_smoke/.

Run all:      uv run pipeline/smoke.py
Run some:     uv run pipeline/smoke.py json image tts agent
"""
import base64
import json
import os
import sys
import tarfile
import time

import httpx
from dotenv import load_dotenv
from google import genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import config as C  # noqa: E402

load_dotenv(C.ROOT / ".env")
OUT = C.BUILDS / "_smoke"
OUT.mkdir(parents=True, exist_ok=True)
client = genai.Client()


def check_json():
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "characters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                    "required": ["id", "name"],
                },
            },
        },
        "required": ["title", "characters"],
    }
    t = time.time()
    r = client.interactions.create(
        model=C.ARGON,
        input="Name the book Alice's Adventures in Wonderland and list three of its characters.",
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "low"},
    )
    data = json.loads(r.output_text)
    assert data["characters"], data
    (OUT / "json.json").write_text(json.dumps(data, indent=2))
    print(f"  json ok {time.time()-t:.1f}s  {r.id}  {[c['name'] for c in data['characters']]}")


def check_image():
    t = time.time()
    r = client.interactions.create(
        model=C.IMAGE,
        input="A small original cartoon rabbit in a blue waistcoat holding a pocket watch, "
              "flat colours, soft watercolour, plain white background, full body, centered.",
        response_format={"type": "image", "mime_type": "image/jpeg", "aspect_ratio": "1:1", "image_size": "1K"},
    )
    img = base64.b64decode(r.output_image.data)
    (OUT / "image.jpg").write_bytes(img)
    print(f"  image ok {time.time()-t:.1f}s  {r.id}  {len(img)} bytes")


def check_tts():
    t = time.time()
    r = client.interactions.create(
        model=C.TTS,
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": "Oh dear! Oh dear! I shall be too late!",
                "annotations": [{"type": "speech_metadata", "style": "hurried and anxious"}],
            }],
        }],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": "Puck"}]},
    )
    wav = base64.b64decode(r.output_audio.data)
    (OUT / "tts.wav").write_bytes(wav)
    print(f"  tts ok {time.time()-t:.1f}s  {r.id}  {len(wav)} bytes {r.output_audio.mime_type}")


def download_environment(env_id: str, dest):
    """Whole-sandbox tar download. No SDK method yet, per the managed agents quickstart."""
    url = f"{C.API_BASE}/files/environment-{env_id}:download"
    with httpx.Client(follow_redirects=True, timeout=300) as h:
        resp = h.get(url, params={"alt": "media"}, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
        resp.raise_for_status()
    tar_path = dest / "environment.tar"
    tar_path.write_bytes(resp.content)
    with tarfile.open(tar_path) as tar:
        tar.extractall(path=dest / "environment", filter="data")
    return dest / "environment"


def check_agent():
    t = time.time()
    r = client.interactions.create(
        agent=C.AGENT,
        agent_config={**C.AGENT_CONFIG, "max_total_tokens": 200_000},
        environment={
            "type": "remote",
            "sources": [{"type": "inline", "target": "/workspace/hello.txt", "content": "hello from storyworld\n"}],
        },
        input="Read /workspace/hello.txt. Create /workspace/out/reply.json containing "
              '{"received": <the file contents as a string>, "ok": true}. '
              "Then print the file. Do nothing else.",
        background=True,
    )
    print(f"  agent started {r.id} env {r.environment_id}")
    while r.status in ("queued", "in_progress"):
        time.sleep(10)
        r = client.interactions.get(r.id)
    print(f"  agent {r.status} {time.time()-t:.1f}s")
    (OUT / "agent_output.txt").write_text(r.output_text or "")
    if r.status != "completed":
        raise RuntimeError(f"agent status {r.status}: {getattr(r, 'error', None)}")
    env_dir = download_environment(r.environment_id, OUT)
    found = list(env_dir.rglob("reply.json"))
    assert found, f"reply.json not in downloaded environment; files: {[str(p) for p in env_dir.rglob('*')][:30]}"
    (OUT / "agent.json").write_text(found[0].read_text())
    print(f"  agent ok  file retrieved: {found[0].relative_to(env_dir)} -> {found[0].read_text().strip()}")


CHECKS = {"json": check_json, "image": check_image, "tts": check_tts, "agent": check_agent}

if __name__ == "__main__":
    names = sys.argv[1:] or list(CHECKS)
    failed = []
    for n in names:
        print(f"[{n}]")
        try:
            CHECKS[n]()
        except Exception as e:  # keep going; report all
            failed.append(n)
            print(f"  {n} FAILED: {type(e).__name__}: {e}")
    print("\nfiles:", sorted(p.name for p in OUT.iterdir()))
    sys.exit(1 if failed else 0)
