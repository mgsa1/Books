"""Voice every dialogue line with Gemini TTS. Argon casts the voices; every clip is later
checked against its text by local Whisper (scripts/verify_audio.py) and failures are re-voiced.

    BOOK=alice .venv/bin/python -I scripts/voice_game.py              # cast (once) + voice missing lines
    BOOK=alice .venv/bin/python -I scripts/voice_game.py --only b02_watch_rabbit#0,b05_drink_and_eat#1 --force
Writes <assets>/audio/<beat>_<i>.mp3, <assets>/audio/casting.json, and marks the manifest.
"""
import argparse
import base64
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from argon import ask, client  # noqa: E402
from books import BOOK  # noqa: E402

TTS = "gemini-3.8-flash-tts"
LANG = {"alice": "en-GB", "lesmis": "fr-FR"}[BOOK.id]
VOICES = """Zephyr (bright), Puck (upbeat), Charon (informative), Kore (firm), Fenrir (excitable), Leda (youthful), Orus (firm),
Aoede (breezy), Callirrhoe (easy-going), Autonoe (bright), Enceladus (breathy), Iapetus (clear), Umbriel (easy-going),
Algieba (smooth), Despina (smooth), Erinome (clear), Algenib (gravelly), Rasalgethi (informative), Laomedeia (upbeat),
Achernar (soft), Alnilam (firm), Schedar (even), Gacrux (mature), Pulcherrima (forward), Achird (friendly),
Zubenelgenubi (casual), Vindemiatrix (gentle), Sadachbia (lively), Sadaltager (knowledgeable), Sulafat (warm)"""


def spoken(text):
    return text.replace("_", "")  # Gutenberg italics markers


def cast(g, out):
    path = out / "casting.json"
    if path.exists():
        return json.loads(path.read_text())
    chars = [{"id": c["id"], "name": c["name_fr"], "build": c.get("build"), "portrait": c.get("portrait_prompt", "")} for c in g["characters"]]
    narrator = g.get("narrator", BOOK.narrator)
    prompt = f"""Cast voices for a game adaptation of {'Alice in Wonderland' if BOOK.id == 'alice' else 'Les Misérables'} (spoken in {LANG}).
Available prebuilt voices (name: character): {VOICES}
Characters: {json.dumps(chars, ensure_ascii=False)}
Also cast the narrator (id "{narrator}"): a warm storyteller.
For each id return a voice name from the list and a short delivery tag in square brackets, in English, 2-5 words, e.g. "[fussy, out of breath]".
Make the voices distinct (the same voice at most twice, never for characters who share a scene). Children sound young.
Return only JSON: {{"<id>": {{"voice": "...", "tag": "[...]"}}, ...}}"""
    it = ask(prompt, level="low")
    t = it.output_text
    casting = json.loads(t[t.index("{"): t.rindex("}") + 1])
    path.write_text(json.dumps(casting, ensure_ascii=False, indent=1))
    return casting


def voice(text, voice_name, tag):
    it = client.interactions.create(model=TTS, input=f"{tag} {text}".strip(), response_modalities=["audio"],
                                    generation_config={"speech_config": {"voice": voice_name, "language": LANG}},
                                    response_format={"type": "audio", "mime_type": "audio/mp3"})
    if not it.output_audio or not it.output_audio.data:
        raise RuntimeError("no audio returned")
    d = it.output_audio.data
    return base64.b64decode(d) if isinstance(d, str) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-tag", action="store_true", help="voice without the delivery tag (some tags get read aloud)")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    g = json.loads((BOOK.game_dir / "script.json").read_text())
    out = BOOK.assets_dir / "audio"
    out.mkdir(parents=True, exist_ok=True)
    casting = cast(g, out)
    narrator = g.get("narrator", BOOK.narrator)
    print("casting:", ", ".join(f"{k}={v['voice']}" for k, v in casting.items()), flush=True)

    jobs = []
    for b in g["beats"]:
        for i, l in enumerate(b["lines"]):
            key = f"{b['id']}#{i}"
            f = out / f"{b['id']}_{i}.mp3"
            if (only and key not in only) or (f.exists() and not a.force):
                continue
            who = casting.get(l["speaker"]) or casting.get(narrator) or {"voice": "Charon", "tag": "[warm]"}
            jobs.append((key, f, spoken(l["text_fr"]), who["voice"], "" if a.no_tag else who["tag"]))

    t0 = time.time()

    def run(job):
        key, f, text, v, tag = job
        for attempt in range(3):
            try:
                f.write_bytes(voice(text, v, tag)); return key
            except Exception as ex:
                if attempt == 2:
                    raise
                time.sleep(2 + attempt * 3)

    done = 0
    with ThreadPoolExecutor(8) as pool:
        futs = {pool.submit(run, j): j[0] for j in jobs}
        for fut in as_completed(futs):
            try:
                fut.result(); done += 1
                if done % 10 == 0 or done == len(jobs):
                    print(f"  {done}/{len(jobs)} lines voiced · {time.time() - t0:.0f}s", flush=True)
            except Exception as ex:
                print(f"  ✗ {futs[fut]}: {str(ex)[:140]}", flush=True)
    mpath = BOOK.assets_dir / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    manifest["audio"] = sorted(f.stem for f in out.glob("*.mp3") if f.stat().st_size > 1000)  # engine only requests clips that exist
    mpath.write_text(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
