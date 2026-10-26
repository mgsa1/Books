"""Rebuild a recording's soundtrack from its event log (Playwright video has no audio):
voice clips at the moment each line was spoken, music loops per area, music ducked under speech.

    python3 -I scripts/mix_audio.py recordings/alice_0-12            -> video.mp4 (H.264 + AAC)
    python3 -I scripts/mix_audio.py recordings/alice_0-12 --clip 297 20 --name rabbit
                                                                     -> clip_rabbit.mp4 (20 s from 297 s)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("rec")
ap.add_argument("--clip", nargs=2, type=float, metavar=("START", "LENGTH"))
ap.add_argument("--name", default="clip")
a = ap.parse_args()
rec = ROOT / a.rec if not Path(a.rec).is_absolute() else Path(a.rec)
d = json.loads((rec / "events.json").read_text())
book = d["meta"]["book"]
assets = ROOT / "game" / "assets"
ev = d["events"]
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(rec / "video.webm")]).decode())

# voice segments: start at "voice", end at its voice_end / voice_cut / the next voice
voices = []
for i, e in enumerate(ev):
    if e["type"] != "voice":
        continue
    end = next((x["video_s"] for x in ev[i + 1:] if x["type"] in ("voice_end", "voice_cut", "voice")), total)
    f = assets / "audio" / f"{e['key']}.mp3"
    if f.exists():
        voices.append((e["video_s"], end, f))
# music segments: each "music" event until the next one (skip the title flash at the start)
music = []
mev = [e for e in ev if e["type"] == "music"]
for i, e in enumerate(mev):
    end = mev[i + 1]["video_s"] if i + 1 < len(mev) else total
    f = assets / "music" / f"{e['track']}.mp3"
    if end - e["video_s"] > 1 and f.exists():
        music.append((e["video_s"], end, f))

inputs, filters, vlabels, mlabels = ["-i", str(rec / "video.webm")], [], [], []
n = 1
for k, (s, e, f) in enumerate(voices):
    inputs += ["-i", str(f)]
    ms = int(s * 1000)
    filters.append(f"[{n}:a]atrim=0:{max(0.1, e - s):.3f},aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    vlabels.append(f"[v{k}]"); n += 1
for k, (s, e, f) in enumerate(music):
    inputs += ["-stream_loop", "-1", "-i", str(f)]
    ms, dur = int(s * 1000), e - s
    filters.append(f"[{n}:a]atrim=0:{dur:.3f},afade=t=in:d=1.5,afade=t=out:st={max(0, dur - 2):.3f}:d=2,volume=0.30,"
                   f"aformat=channel_layouts=stereo,adelay={ms}|{ms}[m{k}]")
    mlabels.append(f"[m{k}]"); n += 1
filters.append(f"{''.join(vlabels)}amix=inputs={len(vlabels)}:normalize=0,apad=whole_dur={total:.3f},asplit=2[voice][key]")
filters.append(f"{''.join(mlabels)}amix=inputs={len(mlabels)}:normalize=0,apad=whole_dur={total:.3f}[musicbus]")
# duck the music whenever someone speaks
filters.append("[musicbus][key]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=600[ducked]")
filters.append(f"[voice][ducked]amix=inputs=2:normalize=0,atrim=0:{total:.3f},alimiter=limit=0.95[aout]")
graph = rec / "mix.filter"
graph.write_text(";\n".join(filters))

out = rec / "video.mp4"
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", str(graph), "-map", "0:v", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
if not out.exists() or out.stat().st_mtime < (rec / "events.json").stat().st_mtime:
    subprocess.run(cmd, check=True)
print(f"{out.relative_to(ROOT)}: {len(voices)} voice clips, {len(music)} music segments, {total:.0f}s")

if a.clip:
    start, length = a.clip
    clip = rec / f"clip_{a.name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start}", "-i", str(out), "-t", f"{length}",
                    "-vf", "fade=t=in:d=0.4,fade=t=out:st=" + f"{length - 0.6}:d=0.6",
                    "-af", f"afade=t=in:d=0.4,afade=t=out:st={length - 0.8}:d=0.8",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(clip)], check=True)
    print(f"{clip.relative_to(ROOT)}: {length:.0f}s from {start:.1f}s")
