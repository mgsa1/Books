"""Backend checks that need no model calls.  Run: uv run tests/test_backend.py"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pipeline.adapt import game_files, workspace_sources  # noqa: E402
from pipeline.playtest import playthrough  # noqa: E402
from pipeline.verify import apply_fixes, better_or_equal  # noqa: E402
from pipeline.ingest import chapters_from_docs  # noqa: E402
from pipeline.slots import ground  # noqa: E402
from pipeline.style import compose_sheet, fit, key_white  # noqa: E402
from PIL import Image  # noqa: E402

STORY = {"title": "fixture", "characters": [
    {"id": "hero", "first_chapter": "c01", "last_chapter": "c01"},
    {"id": "friend", "first_chapter": "c01", "last_chapter": "c01"},
    {"id": "ghost", "first_chapter": "c02", "last_chapter": "c02"}],
    "items": [{"id": "key", "chapter": "c01"}, {"id": "cake", "chapter": "c02"}], "chapters": []}


def test_playthrough():
    ev = Path(tempfile.mkdtemp()) / "ev"
    res = playthrough(ROOT / "tests" / "fixture_game", ev, STORY, ["c01"], per_step_wait=0.2)
    names = {s["name"]: s["ok"] for s in res["steps"]}
    assert names["playtest_api"], res
    assert names["character_present:hero"] and names["character_present:friend"]
    assert "character_present:ghost" not in names, "chapter filter failed"
    assert names["talk:friend"], res
    assert not names["talk:hero"], "hero has no lines, talk should not change state"
    assert names["collect:key"], res
    assert names["no_console_errors"], res["errors"]
    assert len(list((ev / "shots").glob("*.png"))) >= 4
    assert (ev / "events.jsonl").exists() and (ev / "result.json").exists()
    print(f"playthrough ok: score {res['score']}/{res['total']} in {res['seconds']}s")


def test_packing():
    g = ROOT / "games" / "veilspire"
    if not g.exists():
        print("packing skipped: no games/veilspire"); return
    texts, binaries = game_files(g)
    rels = [r for r, _ in texts]
    assert "index.html" in rels and any(r.endswith("main.js") for r in rels), rels[:10]
    assert not any(".git/" in r for r in rels + binaries)
    assert isinstance(binaries, list)
    b = Path(tempfile.mkdtemp())
    (b / "assets").mkdir()
    for n in ("story.json", "style.json", "selection.json"):
        (b / n).write_text("{}")
    srcs = workspace_sources(b, g, texts, binaries)
    targets = [s["target"] for s in srcs]
    assert "/workspace/CONTRACT.md" in targets and "/workspace/story.json" in targets
    assert all(t.startswith("/workspace/") for t in targets)
    size = sum(len(s["content"]) for s in srcs)
    print(f"packing ok: {len(texts)} text files, {len(binaries)} binaries, {size//1000}k chars in {len(srcs)} sources")


def test_apply_fixes():
    g = Path(tempfile.mkdtemp()) / "game"
    g.mkdir()
    (g / "a.js").write_text("let lives = 3;\nlet x = 1;\n")
    (g / "story.json").write_text("{}")
    changed = apply_fixes(g, {"fixes": [{"path": "/workspace/game/a.js", "search": "let lives = 3;", "replace": "let lives = Infinity;"}]})
    assert changed == ["a.js"] and "Infinity" in (g / "a.js").read_text()
    for bad in ({"path": "a.js", "search": "nope", "replace": ""},
                {"path": "story.json", "search": "{}", "replace": "{}"},
                {"path": "../a.js", "search": "x", "replace": "y"}):
        try:
            apply_fixes(g, {"fixes": [bad]}); raise AssertionError(f"should refuse {bad}")
        except ValueError:
            pass
    assert better_or_equal({"score": 3, "errors": []}, {"score": 3, "errors": []})
    assert not better_or_equal({"score": 3, "errors": []}, {"score": 2, "errors": []})
    assert not better_or_equal({"score": 3, "errors": []}, {"score": 4, "errors": ["TypeError"]})
    print("apply_fixes ok")


def test_ingest_parser():
    docs = ["<body><h2>CHAPTER I.<br/> One</h2><p>A.</p><p>B.</p></body>",
            "<body><h2>CHAPTER II.</h2><h2>Two</h2><p>C.</p><p>THE END</p></body>",
            "<body><footer class='pg-boilerplate'><p>license junk</p></footer></body>"]
    ch = chapters_from_docs(docs)
    assert [c["id"] for c in ch] == ["c01", "c02"], ch
    assert ch[1]["title"] == "CHAPTER II. Two" and [p["id"] for p in ch[1]["paragraphs"]] == ["c02.p0001"], ch[1]
    assert ch[0]["paragraphs"][1]["text"] == "B."
    print("ingest parser ok")


def test_grounding():
    g = ROOT / "games" / "browserquest"
    if not g.exists():
        print("grounding skipped: no games/browserquest"); return
    meta = json.loads((g / "client/sprites/rat.json").read_text())
    anims = [{"name": k, "row": v["row"], "frames": v["length"]} for k, v in meta["animations"].items()]
    good = {"id": "rat", "role": "enemy", "kind": "sheet", "required": True, "subject_hint": "rat", "count": 1,
            "where": {"files": ["client/img/1/rat.png", "client/img/2/rat.png"], "code": ["client/js/sprites.js:1"]},
            "format": {"frame_width": meta["width"], "frame_height": meta["height"], "animations": anims,
                       "facings": ["right", "up", "down"], "metadata_file": "client/sprites/rat.json", "notes": ""}}
    ok, why = ground(good, g)
    assert ok, why
    assert good["format"]["measured"]["client/img/1/rat.png"] and good["format"]["sheet_width"]
    bad = json.loads(json.dumps(good)); bad["format"]["frame_width"] = 50
    ok, why = ground(bad, g); assert not ok and "multiple" in why[0], why
    bad = json.loads(json.dumps(good)); bad["where"]["files"] = ["client/img/1/nope.png"]
    ok, why = ground(bad, g); assert not ok and "missing" in why[0], why
    print(f"grounding ok: rat sheet {good['format']['sheet_width']}x{good['format']['sheet_height']}, {len(anims)} animations")


def test_sheet_compose():
    pose = Image.new("RGBA", (300, 500), (0, 0, 0, 0))
    from PIL import ImageDraw
    ImageDraw.Draw(pose).rectangle([50, 50, 250, 480], fill=(200, 40, 40, 255))
    fmt = {"frame_width": 48, "frame_height": 48,
           "animations": [{"name": "walk_right", "row": 0, "frames": 3}, {"name": "idle_down", "row": 1, "frames": 2},
                          {"name": "walk_up", "row": 2, "frames": 4}]}
    sheet = compose_sheet({"right": pose, "down": pose, "up": pose}, fmt)
    assert sheet.size == (4 * 48, 3 * 48), sheet.size
    assert sheet.getpixel((24, 47))[3] > 0, "pose should touch the bottom of frame 0 (bottom anchor)"
    assert sheet.getpixel((3 * 48 + 24, 24))[3] == 0, "row 0 has 3 frames, column 4 must stay empty"
    assert sheet.getpixel((3 * 48 + 24, 2 * 48 + 24))[3] > 0, "row 2 has 4 frames"
    white = Image.new("RGB", (100, 100), (255, 255, 255)); ImageDraw.Draw(white).ellipse([20, 20, 80, 80], fill=(10, 10, 200))
    k = key_white(white)
    assert k.size[0] <= 62 and k.getpixel((0, 0))[3] == 0, "white keyed out and cropped to the ellipse"
    f = fit(k, 32, 32); assert f.size == (32, 32) and f.getpixel((16, 31))[3] > 0
    print("sheet compose ok")


if __name__ == "__main__":
    for t in (test_ingest_parser, test_apply_fixes, test_grounding, test_sheet_compose, test_packing, test_playthrough):
        t()
    print("ALL OK")
