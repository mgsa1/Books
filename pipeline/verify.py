"""Step [6] of the pipeline: play -> screenshot -> Argon critique -> patch -> replay, at most 3 rounds.

Usage: uv run pipeline/verify.py builds/<book> [--rounds 3] [--no-fix]
Evidence under builds/<book>/verification/round_N/{before,after}/ and verification/report.json.
A patch is kept only if the replay score does not drop and no new console error appears.
"""
import argparse
import base64
import json
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402
from pipeline.adapt import game_files, npm_build  # noqa: E402
from pipeline.playtest import playthrough  # noqa: E402

load_dotenv(C.ROOT / ".env")
PROTECTED = {"story.json", "selection.json", "manifest.json", "audio_manifest.json", "LICENSE", "NOTICE"}


def serve_dir(game: Path) -> Path:
    for d in ("dist", "build", "public"):
        if (game / d / "index.html").exists():
            return game / d
    return game


def critique(client, build: Path, game: Path, evidence: Path, extra_context: str = ""):
    """Ask Argon for defects with evidence and search/replace fixes."""
    schema = json.loads((C.SCHEMA / "critique.schema.json").read_text())
    story = (build / "story.json").read_text()
    contract = (C.PROMPTS / "adapt_contract.md").read_text()
    texts, _ = game_files(game)
    src = "\n\n".join(f"===== {rel} =====\n{c}" for rel, c in texts if rel.split("/")[-1] not in PROTECTED)
    events = (evidence / "events.jsonl").read_text() if (evidence / "events.jsonl").exists() else ""
    result = (evidence / "result.json").read_text() if (evidence / "result.json").exists() else "{}"
    parts = [{"type": "text", "text": f"{extra_context}\n\nPLAYTEST RESULT\n{result}\n\nEVENT LOG (line numbers start at 1)\n"
              + "\n".join(f"{i+1}: {l}" for i, l in enumerate(events.splitlines()))}]
    shots = sorted((evidence / "shots").glob("*.png")) if (evidence / "shots").exists() else []
    for p in shots[:24]:
        parts.append({"type": "text", "text": f"SCREENSHOT {p.name}"})
        parts.append({"type": "image", "data": base64.b64encode(p.read_bytes()).decode(), "mime_type": "image/png"})
    extra = "".join(f"\n{n.upper()}\n{(build / n).read_text()}\n" for n in ("slots.json", "style.json") if (build / n).exists())
    manifest = build / "assets" / "manifest.json"
    if manifest.exists():
        extra += f"\nASSET MANIFEST\n{manifest.read_text()}\n"
    parts.append({"type": "text", "text": f"\nSTORY DATA\n{story}\n{extra}\nCONTRACT\n{contract}\n\nGAME SOURCE\n{src}"})
    r = client.interactions.create(
        model=C.ARGON, system_instruction=(C.PROMPTS / "critique.md").read_text(), input=parts,
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "medium"},
    )
    out = json.loads(r.output_text)
    out["interaction_id"] = r.id
    return out


def apply_fixes(game: Path, defect: dict):
    """Apply search/replace edits. Returns list of changed files, or raises if any edit cannot apply."""
    changed = []
    for fx in defect["fixes"]:
        rel = fx["path"].lstrip("/").removeprefix("workspace/").removeprefix("game/")
        p = game / rel
        if p.name in PROTECTED or not p.exists() or ".." in rel:
            raise ValueError(f"refused edit to {rel}")
        s = p.read_text()
        if s.count(fx["search"]) != 1:
            raise ValueError(f"search text not unique or absent in {rel}")
        p.write_text(s.replace(fx["search"], fx["replace"]))
        changed.append(rel)
    return changed


def better_or_equal(before, after):
    new_errors = [e for e in after["errors"] if e not in before["errors"]]
    return after["score"] >= before["score"] and not new_errors


def repair_loop(client, build: Path, game: Path, rounds: int, fix: bool, first_evidence: Path | None = None,
                extra_context: str = "", reuse: bool = False):
    """Generic loop used by verify (scripted playthrough) and watch (real session)."""
    story = json.loads((build / "story.json").read_text())
    sel = json.loads((build / "selection.json").read_text())["chapters"]
    vdir = build / "verification"
    report = {"rounds": [], "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    evidence = first_evidence or vdir / "round_0" / "before"
    if first_evidence is None:
        print("baseline playthrough...")
        base = playthrough(serve_dir(game), evidence, story, sel)
        print(f"  score {base['score']}/{base['total']}, errors {len(base['errors'])}")
    base = json.loads((evidence / "result.json").read_text()) if (evidence / "result.json").exists() else {"score": 0, "errors": []}
    for n in range(1, rounds + 1):
        rdir = vdir / f"round_{n}"
        rdir.mkdir(parents=True, exist_ok=True)
        if reuse and (rdir / "critique.json").exists():
            print(f"round {n}: reusing critique")
            crit = json.loads((rdir / "critique.json").read_text())
        else:
            print(f"round {n}: critique...")
            crit = critique(client, build, game, evidence, extra_context)
        (rdir / "critique.json").write_text(json.dumps(crit, indent=1))
        defects = [d for d in crit["defects"] if d["evidence"]]
        print(f"  {len(crit['defects'])} defects, {len(defects)} with evidence")
        for d in defects[:5]:
            print(f"   [{d['severity']}] {d['kind']} {d['id']}: {d['observed'][:90]}")
        entry = {"round": n, "defects": len(defects), "applied": None, "kept": False}
        report["rounds"].append(entry)
        if not fix or not defects:
            break
        candidates = [d for d in defects if d["fixes"]][:3]
        if not candidates:
            print("  no defect has an applicable fix; stopping")
            break
        entry["attempts"], kept_any = [], False
        for i, target in enumerate(candidates, 1):
            staging = rdir / f"staging_{i}"
            shutil.rmtree(staging, ignore_errors=True)
            shutil.copytree(game, staging, symlinks=True, ignore_dangling_symlinks=True,
                            ignore=shutil.ignore_patterns("node_modules", "sessions"))
            attempt = {"defect": target["id"]}
            entry["attempts"].append(attempt)
            try:
                changed = apply_fixes(staging, target)
                if (staging / "package.json").exists():
                    if (game / "node_modules").exists() and not (staging / "node_modules").exists():
                        (staging / "node_modules").symlink_to(game / "node_modules")
                    if npm_build(staging) is False:
                        raise ValueError("patched game does not build")
            except ValueError as e:
                print(f"  {target['id']}: fix rejected: {e}")
                attempt["rejected"] = str(e)
                continue
            after_dir = rdir / f"after_{i}"
            after = playthrough(serve_dir(staging), after_dir, story, sel)
            ok = better_or_equal(base, after)
            attempt.update(files=changed, score_before=base["score"], score_after=after["score"],
                           new_errors=[e for e in after["errors"] if e not in base["errors"]], kept=ok)
            print(f"  {target['id']} -> {changed}: score {base['score']} -> {after['score']} {'KEPT' if ok else 'REVERTED'}")
            (rdir / f"patch_{i}.json").write_text(json.dumps(target, indent=1))
            if ok:
                for rel in changed:
                    shutil.copy(staging / rel, game / rel)
                base, evidence, kept_any = after, after_dir, True
        entry["kept"] = kept_any
        if not kept_any:
            break
    report["final_score"] = base.get("score")
    (vdir / "report.json").write_text(json.dumps(report, indent=1))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--no-fix", action="store_true")
    ap.add_argument("--reuse-critique", action="store_true", help="reuse round_N/critique.json when present")
    a = ap.parse_args()
    b = Path(a.build)
    rep = repair_loop(genai.Client(), b, b / "game", a.rounds, not a.no_fix, reuse=a.reuse_critique)
    print(json.dumps(rep, indent=1))
