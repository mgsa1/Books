"""Argon listens to each music loop: any vocals? does it match its brief? (Whisper hallucinates words on music.)

    BOOK=alice .venv/bin/python -I scripts/listen_music.py
"""
import base64
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
from argon import ARGON, client  # noqa: E402
from books import BOOK  # noqa: E402

out = BOOK.assets_dir / "music"
briefs = json.loads((out / "briefs.json").read_text())


def listen(k):
    data = base64.b64encode((out / f"{k}.mp3").read_bytes()).decode()
    it = client.interactions.create(model=ARGON, generation_config={"thinking_level": "low"}, input=[
        {"type": "audio", "data": data, "mime_type": "audio/mp3"},
        {"type": "text", "text": f"This is a background music loop for a video game. The brief was: {briefs[k]}\n"
         "Listen. Return only JSON: {\"vocals\": true/false (any singing or spoken words), \"heard\": \"instruments, tempo, mood in one line\", "
         "\"matches_brief\": true/false, \"issues\": \"abrupt ending, noise, silence… or empty\"}"}])
    t = it.output_text
    return k, json.loads(t[t.index("{"): t.rindex("}") + 1])


with ThreadPoolExecutor(6) as pool:
    results = dict(pool.map(listen, sorted(briefs)))
(out / "listen.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
for k, r in results.items():
    flag = "✓" if not r["vocals"] and r["matches_brief"] else "✗"
    print(f"  {flag} {k:<15} vocals={r['vocals']!s:<5} {r['heard'][:90]}" + (f"  [{r['issues']}]" if r.get("issues") else ""))
