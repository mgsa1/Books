"""Argon watches a recorded play-through (video + event log) and reports bugs, with timestamps.

    .venv/bin/python -I scripts/review_video.py recordings/alice_0-12
-> recordings/<rec>/review.json
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from argon import ARGON, client  # noqa: E402

rec = ROOT / sys.argv[1]
HIGHLIGHT = sys.argv[2] if len(sys.argv) > 2 else "the most charming 20 seconds"
d = json.loads((rec / "events.json").read_text())
small = rec / "review_720p.mp4"
if not small.exists():  # 720p / 12 fps keeps UI text legible and the upload small
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(rec / "video.mp4"), "-vf", "scale=1280:-2,fps=12", "-c:v", "libx264",
                    "-crf", "30", "-preset", "veryfast", "-c:a", "aac", "-b:a", "64k", str(small)], check=True)
print(f"uploading {small.name} ({small.stat().st_size / 1e6:.1f} MB)", flush=True)
f = client.files.upload(file=str(small))
while getattr(f, "state", None) and str(f.state).endswith("PROCESSING"):
    time.sleep(3); f = client.files.get(name=f.name)
print("file:", f.name, f.state, flush=True)

keep = ("beat_start", "beat_play", "beat_end", "line", "voice", "voice_end", "voice_cut", "music", "travel", "blocked", "violation", "error", "autopilot_plan")
log = "\n".join(f"{e['video_s']:7.1f}s {e['type']:<14} beat={e['beat']} " + " ".join(f"{k}={v}" for k, v in e.items()
                if k in ("id", "key", "speaker", "track", "from", "to", "steps", "act", "rule", "message", "card"))
                for e in d["events"] if e["type"] in keep)
script = json.loads((ROOT / "game" / "script.json").read_text())
beats = [{"i": i, "id": b["id"], "objective": b["objective_fr"], "trigger": b["trigger"], "lines": len(b["lines"]),
          "card": bool(b.get("card_prompt"))} for i, b in enumerate(script["beats"])]

prompt = f"""You are QA for a small isometric story game (Alice in Wonderland; the player character is steered by an autopilot).
Attached: a screen recording of beats {d['meta']['from']}–{d['meta']['until']} with its audio (voices + music), and below
the game's own event log with times in VIDEO SECONDS, plus the beat list.

Watch the whole video. Report every bug or rough edge a player or a hackathon judge would notice, e.g.:
- visual: clipping, z-fighting, characters inside walls/buildings, overlapping NPCs, labels covering things, unreadable text,
  dialogue text overflowing its box, wrong portrait for the speaker, flicker, black/empty frames, camera problems;
- story/logic: a scene that doesn't match its objective, someone speaking who isn't on screen, card/illustration mismatching the line;
- pacing/audio: long dead time, voice cut off, music too loud over voice, silence, abrupt transitions;
- the log: violations, blocked moves, odd timings (compare log vs. what you see).
Be concrete: give the video timestamp, what you see, why it matters, and the likely cause/fix.
Do not invent problems; if something is fine, don't list it.

Also: we want a 20-second highlight for the hackathon video: {HIGHLIGHT}. Propose the best window (start, end):
start and end on sentence boundaries (never cut a voice line), and say why.

Return only JSON:
{{"bugs": [{{"t": seconds, "severity": "high|medium|low", "category": "visual|logic|pacing|audio|performance", "what": "...", "why": "...", "fix": "..."}}],
  "highlight": {{"start": s, "end": e, "why": "..."}}, "overall": "two sentences"}}

BEATS: {json.dumps(beats, ensure_ascii=False)}

EVENT LOG:
{log}"""

t0 = time.time()
it = client.interactions.create(model=ARGON, generation_config={"thinking_level": "high", "max_output_tokens": 30000},
                                input=[{"type": "video", "uri": f.uri, "mime_type": "video/mp4"}, {"type": "text", "text": prompt}])
t = it.output_text
review = json.loads(t[t.index("{"): t.rindex("}") + 1])
(rec / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1))
u = it.usage
print(f"review in {time.time() - t0:.0f}s · in {u.total_input_tokens:,} · out {u.total_output_tokens:,}")
for b in sorted(review["bugs"], key=lambda b: ({"high": 0, "medium": 1, "low": 2}[b["severity"]], b["t"])):
    print(f"  [{b['severity']:<6}] {b['t']:6.1f}s {b['category']:<11} {b['what']}")
print("highlight:", review["highlight"])
print("overall:", review["overall"])
