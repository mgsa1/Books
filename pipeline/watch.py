"""Step [7] of the pipeline: a real play session -> Argon review -> same patch loop as verify.

Usage: uv run pipeline/watch.py builds/<book> path/to/session.json [--rounds 2]
The game writes the session log (see contract point 15); the player downloads it from the page.
Screenshots inside the log are data URLs; they are unpacked to verification/session_<ts>/shots/.
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402
from pipeline.playtest import data_url_to_png  # noqa: E402
from pipeline.verify import repair_loop  # noqa: E402

load_dotenv(C.ROOT / ".env")

REVIEW_FOCUS = """This evidence is a REAL play session by the player, not a scripted test.
Answer three questions with evidence: where did the game break (errors, missing audio, unreachable goal);
where did the player get stuck (no progress for more than 60 seconds, repeated actions, backtracking);
where was the player confused (same character talked to many times, item never found). Treat a stuck or
confused moment as a defect of kind 'stuck' and propose a fix that makes the next step obvious: a hint
line, a visible marker, a moved object, or a removed obstacle."""


def unpack_session(session_path: Path, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    shots = dest / "shots"
    shots.mkdir(exist_ok=True)
    log = json.loads(session_path.read_text())
    events = log.get("events", log if isinstance(log, list) else [])
    out, n = [], 0
    for e in events:
        if isinstance(e, dict) and isinstance(e.get("screenshot"), str) and e["screenshot"].startswith("data:image"):
            n += 1
            name = f"{n:03d}_t{int(e.get('t', 0))}.png"
            data_url_to_png(e["screenshot"], shots / name)
            e = {**e, "screenshot": name}
        out.append(e)
    (dest / "events.jsonl").write_text("\n".join(json.dumps(e) for e in out))
    (dest / "result.json").write_text(json.dumps({"score": 0, "total": 0, "errors": [
        str(e.get("text", e)) for e in out if isinstance(e, dict) and e.get("kind") in ("console_error", "error")][:20],
        "source": "real session", "events": len(out)}, indent=1))
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("session")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()
    b = Path(a.build)
    ev = unpack_session(Path(a.session), b / "verification" / f"session_{int(time.time())}")
    shutil.copy(a.session, ev / "session.json")
    rep = repair_loop(genai.Client(), b, b / "game", a.rounds, True, first_evidence=ev, extra_context=REVIEW_FOCUS)
    print(json.dumps(rep, indent=1))
