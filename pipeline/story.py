"""Step [2] of the pipeline: whole book -> story.json (Argon, JSON schema, thinking high).

Usage: uv run pipeline/story.py builds/alice_s_adventures_in_wonderland
"""
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402

load_dotenv(C.ROOT / ".env")


def validate(story, book):
    """Reference checks the API cannot do. Returns a list of problems."""
    problems = []
    para_ids = {p["id"] for c in book["chapters"] for p in c["paragraphs"]}
    chapter_ids = [c["id"] for c in book["chapters"]]
    if [c["id"] for c in story["chapters"]] != chapter_ids:
        problems.append(f"chapter ids differ: {[c['id'] for c in story['chapters']]}")
    char_ids = [c["id"] for c in story["characters"]]
    if len(set(char_ids)) != len(char_ids):
        problems.append("duplicate character ids")
    beat_ids = [b["id"] for c in story["chapters"] for b in c["beats"]]
    if len(set(beat_ids)) != len(beat_ids):
        problems.append("duplicate beat ids")

    def check_sources(label, ids):
        bad = [i for i in ids if i not in para_ids]
        if bad:
            problems.append(f"{label}: unknown source ids {bad[:5]}")

    for c in story["chapters"]:
        for b in c["beats"]:
            check_sources(f"beat {b['id']}", b["source_ids"])
            if not b["source_ids"]:
                problems.append(f"beat {b['id']} has no source")
            if not all(s.startswith(c["id"] + ".") for s in b["source_ids"]):
                problems.append(f"beat {b['id']} cites outside its chapter")
        if len(c["beats"]) < 3:
            problems.append(f"chapter {c['id']} has only {len(c['beats'])} beats")
    for it in story["items"]:
        check_sources(f"item {it['id']}", it["source_ids"])
        if it["chapter"] not in chapter_ids:
            problems.append(f"item {it['id']} bad chapter {it['chapter']}")
    for ch in story["characters"]:
        for k in ("first_chapter", "last_chapter"):
            if ch[k] not in chapter_ids:
                problems.append(f"character {ch['id']} bad {k} {ch[k]}")
    for ln in story["lines"]:
        if ln["character"] not in char_ids:
            problems.append(f"line by unknown character {ln['character']}")
        if ln["chapter"] not in chapter_ids:
            problems.append(f"line bad chapter {ln['chapter']}")
        check_sources(f"line {ln['character']}/{ln['chapter']}", ln["source_ids"])
        if len(ln["plain"].split()) > 14:
            problems.append(f"line too long ({len(ln['plain'].split())} words): {ln['plain'][:50]}")
        ch = next((c for c in story["characters"] if c["id"] == ln["character"]), None)
        if ch and not (ch["first_chapter"] <= ln["chapter"] <= ch["last_chapter"]):
            problems.append(f"line for {ln['character']} in {ln['chapter']} outside {ch['first_chapter']}..{ch['last_chapter']}")
    return problems


def run(build: Path):
    book = json.loads((build / "book.json").read_text())
    text = (build / "book.txt").read_text()
    schema = json.loads((C.SCHEMA / "story.schema.json").read_text())
    prompt = (C.PROMPTS / "story.md").read_text()
    client = genai.Client()
    t = time.time()
    r = client.interactions.create(
        model=C.ARGON,
        system_instruction=prompt,
        input=f"THE BOOK\n\n{text}",
        response_format={"type": "text", "mime_type": "application/json", "schema": schema},
        generation_config={"thinking_level": "high"},
    )
    dt = time.time() - t
    story = json.loads(r.output_text)
    (build / "story.json").write_text(json.dumps(story, ensure_ascii=False, indent=1))
    usage = getattr(r, "usage", None)
    log = {
        "step": "story", "model": C.ARGON, "interaction_id": r.id, "seconds": round(dt, 1),
        "input_sha256": book["sha256"],
        "usage": usage.model_dump() if hasattr(usage, "model_dump") else str(usage),
    }
    problems = validate(story, book)
    log["problems"] = problems
    (build / "story.log.json").write_text(json.dumps(log, indent=1))
    n_beats = sum(len(c["beats"]) for c in story["chapters"])
    print(f"story.json: {len(story['characters'])} characters, {n_beats} beats, "
          f"{len(story['items'])} items, {len(story['lines'])} lines, {dt:.0f}s")
    print("usage:", log["usage"])
    print(f"{len(problems)} problems" + (":\n  " + "\n  ".join(problems[:20]) if problems else ""))
    return story, problems


if __name__ == "__main__":
    _, problems = run(Path(sys.argv[1]))
    sys.exit(1 if problems else 0)
