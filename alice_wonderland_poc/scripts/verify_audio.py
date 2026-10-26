"""Check every voiced line: local Whisper transcribes the clip; the words must match the text.
Catches spoken stage directions, truncations and garbled clips. Prints the keys to re-voice.

    BOOK=alice python3 -I scripts/verify_audio.py        # system python: it has mlx_whisper
"""
import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import mlx_whisper

ROOT = Path(__file__).resolve().parent.parent
BOOK = os.environ.get("BOOK", "alice")
GAME = ROOT / "game"
ASSETS = ROOT / "game" / "assets"
LANG = {"alice": "en", "lesmis": "fr"}[BOOK]


def words(t):
    t = t.lower().replace("’", "'").replace("_", "")
    return re.findall(r"[a-zà-ÿœæ0-9']+", t)


g = json.loads((GAME / "script.json").read_text())
bad, results = [], {}
for b in g["beats"]:
    for i, l in enumerate(b["lines"]):
        f = ASSETS / "audio" / f"{b['id']}_{i}.mp3"
        key = f"{b['id']}#{i}"
        if not f.exists():
            bad.append(key); results[key] = {"score": 0, "heard": "(missing)"}; continue
        heard = mlx_whisper.transcribe(str(f), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language=LANG)["text"]
        want, got = words(l["text_fr"]), words(heard)
        score = SequenceMatcher(None, want, got).ratio()
        extra = len(got) - len(want)
        results[key] = {"score": round(score, 3), "heard": heard.strip(), "extra_words": extra}
        # a spoken delivery tag shows up as extra words at the start, often the tag's own words (Argon's review caught a
        # 4-word tag that slipped under the old "> 4 extra words" rule)
        casting = json.loads((ASSETS / "audio" / "casting.json").read_text()) if (ASSETS / "audio" / "casting.json").exists() else {}
        tag = words((casting.get(l["speaker"]) or casting.get(g.get("narrator", "")) or {}).get("tag", ""))
        tag_spoken = len(tag) > 0 and sum(w in got[:len(tag) + 3] for w in tag) >= max(2, len(tag) // 2) and not any(w in want[:len(tag) + 3] for w in tag[:1])
        results[key]["tag_spoken"] = tag_spoken
        if score < 0.8 or extra > 2 or tag_spoken:
            bad.append(key)
            print(f"  ✗ {key}: {score:.2f} (+{extra} words) heard «{heard.strip()[:90]}»", flush=True)
(ASSETS / "audio" / "verify.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
n = len(results)
print(f"{n - len(bad)}/{n} clips match their text")
print("REVOICE:", ",".join(bad))
