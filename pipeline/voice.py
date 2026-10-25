"""Step [4] of the pipeline: every line, beat, meaning, summary, and goal in story.json -> WAV.

Usage: uv run pipeline/voice.py builds/alice_s_adventures_in_wonderland [c01 c02 ...]
Writes assets/audio/<sha1>.wav and assets/audio_manifest.json {text_key: {path, voice, text}}.
Cached by text hash: rerunning only generates what is missing.
"""
import base64
import hashlib
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402

load_dotenv(C.ROOT / ".env")

# Prebuilt voices, assigned round-robin by character order. The narrator is fixed.
VOICE_POOL = ["Puck", "Kore", "Zephyr", "Leda", "Fenrir", "Aoede", "Orus", "Callirrhoe", "Enceladus", "Iapetus"]


def voice_for(story):
    chars = [c for c in story["characters"]]
    assignment = {}
    for i, c in enumerate(chars):
        assignment[c["id"]] = VOICE_POOL[i % len(VOICE_POOL)]
    return assignment


def utterances(story, chapters):
    """Yield (key, text, voice_id or 'narrator', style)."""
    for ch in story["chapters"]:
        if ch["id"] not in chapters:
            continue
        yield f"{ch['id']}.summary", ch["summary"], "narrator", "calm storyteller"
        yield f"{ch['id']}.goal", ch["goal"], "narrator", "calm storyteller"
        for b in ch["beats"]:
            yield f"{b['id']}.plain", b["plain"], "narrator", "calm storyteller"
            if b["original"]:
                yield f"{b['id']}.original", b["original"], "narrator", "calm storyteller, reading from the book"
    for it in story["items"]:
        if it["chapter"] in chapters:
            yield f"item.{it['id']}.meaning", it["meaning"], "narrator", "calm storyteller"
    counts = {}
    for ln in story["lines"]:
        if ln["chapter"] not in chapters:
            continue
        k = (ln["character"], ln["chapter"])
        counts[k] = counts.get(k, 0) + 1
        key = f"line.{ln['character']}.{ln['chapter']}.{counts[k]}"
        style = next(c["voice"] for c in story["characters"] if c["id"] == ln["character"])
        yield f"{key}.plain", ln["plain"], ln["character"], style
        if ln["original"]:
            yield f"{key}.original", ln["original"], ln["character"], style


def tts(client, text, voice, style):
    r = client.interactions.create(
        model=C.TTS,
        input=[{"type": "user_input", "content": [{"type": "text", "text": text,
                "annotations": [{"type": "speech_metadata", "style": style}]}]}],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voice}]},
    )
    return base64.b64decode(r.output_audio.data), r.id


def run(build: Path, chapters=None):
    story = json.loads((build / "story.json").read_text())
    chapters = set(chapters or [c["id"] for c in story["chapters"]])
    out = build / "assets" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = build / "assets" / "audio_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    voices = voice_for(story)
    client = genai.Client()
    todo = [(k, t, v, s) for k, t, v, s in utterances(story, chapters)]
    made, t0, failed = 0, time.time(), []
    for key, text, who, style in todo:
        voice = C.NARRATOR_VOICE if who == "narrator" else voices[who]
        h = hashlib.sha1(f"{voice}|{text}".encode()).hexdigest()[:16]
        path = out / f"{h}.wav"
        if not path.exists():
            try:
                wav, iid = tts(client, text, voice, style)
            except Exception as e:  # blocked or transient: record and move on
                print(f"  FAILED {key} ({voice}): {str(e)[:80]} | {text[:60]}")
                manifest[key] = {"path": None, "voice": voice, "speaker": who, "text": text, "error": str(e)[:200]}
                failed.append(key)
                continue
            path.write_bytes(wav)
            made += 1
        manifest[key] = {"path": f"assets/audio/{path.name}", "voice": voice, "speaker": who, "text": text}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    if all(k.endswith(".original") for k in failed):  # originals are optional; plain lines must all succeed
        manifest["_chapters"] = sorted(set(manifest.get("_chapters", [])) | chapters)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"{len(todo)} utterances for {sorted(chapters)}, {made} generated, {len(failed)} failed, {time.time()-t0:.0f}s, "
          f"{sum(p.stat().st_size for p in out.glob('*.wav'))/1e6:.1f} MB total")
    return failed


if __name__ == "__main__":
    run(Path(sys.argv[1]), sys.argv[2:] or None)
