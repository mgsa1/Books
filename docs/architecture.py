#!/usr/bin/env python3
"""Storyworld architecture figure (detailed). Explicit geometry, no Graphviz or Mermaid.

    uv run docs/architecture.py            # writes docs/architecture.svg
    uv run docs/architecture.py --render   # also architecture.png (2x) and architecture.pdf via Playwright's Chromium

Every box and edge mirrors pipeline/*.py, prompts/ and schema/; update this file when the pipeline changes.
Panels: (a) authoring pipeline, (b) observation, (c) repair loop, (d) definitions. See docs/overview.py for the glance version.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import *  # noqa: E402,F401

W, H = 1980, 985
begin(W, H)

# ================================================================== (a) authoring pipeline (top band)
IN_Y, IN_H = 56, 48           # input documents
SY, SH = 146, 200             # stage boxes
GY_ = SY + SH + 18            # gate centre y
DY_, DH_ = SY + SH + 40, 66   # artifact documents
M = 30

header(M, 26, "(a) Authoring pipeline", "`pipeline/run.py` · one command · a step is skipped when its output exists")

# -- stage x layout
S1X, S1W = M, 150
S2X, S2W = S1X + S1W + 22, 190
C3X = S2X + S2W + 22
SUBW, SUBG = 185, 14
C3W = 4 * SUBW + 3 * SUBG + 16
SUB = [C3X + 8 + i * (SUBW + SUBG) for i in range(4)]
S4X, S4W = C3X + C3W + 22, 190
S5X, S5W = S4X + S4W + 22, 270
GX, GW = S5X + S5W + 76, 150
assert GX + GW <= W - M, GX + GW


def cx(x, w):
    return x + w / 2


# -- inputs
doc(S1X, IN_Y, S1W, IN_H, "book.epub", "public domain or rights-cleared")
doc(SUB[0], IN_Y, SUBW, IN_H, "games/<g>/", "libre starting game: open code and open art")
doc(SUB[1], IN_Y, SUBW, IN_H, "refs/*.png | brief", "1..n reference images and / or a text brief")
doc(SUB[2], IN_Y, SUBW, IN_H, "selection", "chapters to build, e.g. `c01 c02`")

# -- stages
node(S1X, SY, S1W, SH, "1  Ingest",
     "zip → XHTML spine → headings and paragraphs; stable ids `c01.p0042`; `sha256` of the input\n\nstandard library only")
node(S2X, SY, S2W, SH, "2  Story",
     "whole book in one context → ground truth S: characters, chapters with beats, items, lines; every element cites its source paragraphs (d1)",
     kind="model", model="gemini-4-argon", extra="thinking high · schema")

rect(C3X, SY - 26, C3W, SH + 34, fill=CONT_FILL, stroke=INK, sw=1.2)
tline(C3X + 8, SY - 10, "3  Look and assets", 11.5, weight="bold")
tline(SUB[2] + 150, SY - 15, "format fixed by the game code (3a), subject by the book (3c),", 8.8, fill=GREY, italic=True)
tline(SUB[2] + 150, SY - 4, "appearance by the look (3b); 3d fills inside those constraints", 8.8, fill=GREY, italic=True)
node(SUB[0], SY, SUBW, SH, "3a  Slots",
     "whole repository in context → every slot the loader reads: role, kind, required, count, where {files, code}, format (frame grid, animations, facings, tile size, colour value)\n\ncached beside the clone by repo hash",
     kind="model", model="gemini-4-argon", extra="thinking high · schema")
node(SUB[1], SY, SUBW, SH, "3b  Bible",
     "references + brief + slot kinds + engine notes → palette, prompt prefix, avoid list, one drawing rule per kind, UI colours\n\nkeyed by `sha1(brief, refs, kinds)`",
     kind="model", model="gemini-4-argon", extra="thinking medium · schema")
node(SUB[2], SY, SUBW, SH, "3c  Cast",
     "subjects of the selection × slots → one assignment per (slot, subject): protagonist → player, every character → portrait, every chapter → backdrop, items → pickups, colour slots → palette values",
     kind="model", model="gemini-4-argon", extra="thinking medium · schema")
node(SUB[3], SY, SUBW, SH, "3d  Fill",
     "per assignment: image fitted to w × h, white keyed to alpha; sheet = one pose per facing, composed static on the frame grid, plus scaled copies; tilesets kept upstream; 4 workers; cached by prompt",
     kind="model", model="gemini-nano-banana-2.1", extra="1K · jpeg → png")
node(S4X, SY, S4W, SH, "4  Voice",
     "one clip per utterance: summaries, goals, beats, item meanings (narrator); lines plain + original (one pool voice per character, delivery from its voice sentence)\n\ncached by `sha1(voice|text)`",
     kind="model", model="gemini-3.8-flash-tts", extra="speech_config · style")

# stage 5 with sandbox
rect(S5X, SY, S5W, SH, fill="#ffffff", stroke=INK, sw=1.3)
tline(S5X + 8, SY + 16, "5  Adapt", 11.5, weight="bold")
tline(S5X + 8, SY + 29, "antigravity-preview-09-2026", 9.3, fill=ACC, family=MONO)
tline(S5X + 8, SY + 41, "managed agent · model gemini-4-argon", 9.0, fill=ACC, family=MONO)
SBX, SBY, SBW, SBH = S5X + 8, SY + 50, S5W - 16, 104
rect(SBX, SBY, SBW, SBH, fill=ACC_FILL, stroke=ACC, sw=1.5, dash="6,4")
tline(SBX + 7, SBY + 14, "remote sandbox  /workspace", 10, weight="bold", fill=ACC)
para(SBX + 7, SBY + 27,
     "in: repository text files (< 400 kB, vendor dirs skipped), `story`, `slots`, `style`, `selection`, both manifests, list of upstream binaries, `CONTRACT.md` (20 points). No asset bytes.\nout: game rewired and rewritten in place, `CHECKS.md`; environment tarball downloaded",
     SBW - 14, 9.1)
para(S5X + 8, SBY + SBH + 15,
     "install: copy → `builds/`, overlay `assets/`, keep the previous build · fallback: one direct call, structured output `{files[], checks}`",
     S5W - 16, 9.1, fill=GREY)

# G
rect(GX, SY, GW, SH, fill=DOC_FILL, stroke=INK, sw=1.6)
tline(GX + 8, SY + 17, "G   builds/<book>/", 11.5, weight="bold")
para(GX + 8, SY + 34,
     "`game/`  static files, exposes `window.playtest`, records every session\n`assets/` + manifests\n`story.json` `slots.json` `style.json` `cast.json`\n`CHECKS.md` `adapt.log.json`\n`verification/round_n/` critique, patch, before / after, `report.json`\n\nno model call at play time",
     GW - 16, 9.1)

# -- spine
mid = SY + SH / 2
arrow([(S1X + S1W, mid), (S2X, mid)])
arrow([(S2X + S2W, mid), (SUB[0], mid)])
for i in range(3):
    arrow([(SUB[i] + SUBW, mid), (SUB[i + 1], mid)])
arrow([(SUB[3] + SUBW, mid), (S4X, mid)])
arrow([(S4X + S4W, mid), (S5X, mid)])
BGX = (S5X + S5W + GX) / 2
arrow([(S5X + S5W, mid), (BGX - 34, mid)])
diamond(BGX, mid, 34, 14, ["npm build"])
arrow([(BGX + 34, mid), (GX, mid)])
tline(BGX, mid + 28, "fails ⇒ reject", 8.6, fill=GREY, italic=True, anchor="middle")

# -- inputs → stages
arrow([(cx(S1X, S1W), IN_Y + IN_H), (cx(S1X, S1W), SY)])
OFF = 40
arrow([(cx(SUB[0], SUBW) + OFF, IN_Y + IN_H), (cx(SUB[0], SUBW) + OFF, SY)])
arrow([(cx(SUB[1], SUBW) + OFF, IN_Y + IN_H), (cx(SUB[1], SUBW) + OFF, SY)])
arrow([(cx(SUB[2], SUBW) + OFF, IN_Y + IN_H), (cx(SUB[2], SUBW) + OFF, SY)])
# games repo also goes to 5 (bus above the inputs row)
BUS1 = 44
gx0 = cx(SUB[0], SUBW) + OFF
arrow([(gx0, IN_Y), (gx0, BUS1), (S5X + 60, BUS1), (S5X + 60, SY)])
elabel(S5X + 66, BUS1 + 4, "repository", size=8.8, bg=False)
# selection also goes to 4 and 5 (bus below the inputs row)
BUS2 = IN_Y + IN_H + 10
sx0 = cx(SUB[2], SUBW) + OFF
dot(sx0, BUS2)
arrow([(sx0, BUS2), (S5X + 30, BUS2), (S5X + 30, SY)])
arrow([(cx(S4X, S4W), BUS2), (cx(S4X, S4W), SY)])
elabel(S5X + 36, BUS2 + 4, "selection", size=8.8, bg=False)

# -- artifacts and gates
def produce(x, w, name, sub, gate=None, note=None):
    c = cx(x, w)
    if gate:
        arrow([(c, SY + SH), (c, GY_ - 14)])
        diamond(c, GY_, 36, 14, [gate])
        arrow([(c, GY_ + 14), (c, DY_)])
        if note:
            tline(c + 40, GY_ + 3, note, 8.6, fill=GREY, italic=True)
    else:
        arrow([(c, SY + SH), (c, DY_)])
        if note:
            tline(c + 6, GY_ + 3, note, 8.6, fill=GREY, italic=True)
    doc(x, DY_, w, DH_, name, sub)


produce(S1X, S1W, "book.json", "+ `book.txt`, one `[id]` marker per paragraph")
produce(S2X, S2W, "story.json", "+ `story.log.json`: interaction id, usage, problems", gate="validate", note="fail ⇒ exit 1")
produce(SUB[0], SUBW, "slots.json", "grounded slots + `rejected[]`; two synthetic slots: dialogue portrait, chapter backdrop", gate="ground", note="claims vs real files (d2)")
produce(SUB[1], SUBW, "style.json", "palette · prefix · rules per kind · `ui` colours", gate="blocklist", note="franchise or artist ⇒ refuse")
produce(SUB[2], SUBW, "cast.json", "assignments ⟨slot, subject, value, why⟩; keyed by selection", note="unknown ids dropped")
produce(SUB[3], SUBW, "manifest.json", "fills[slot][subject] · replaces[upstream] · parameters · kept_upstream · unfilled · missing", gate="fit format", note="required failure ⇒ flat palette shape, listed missing")
produce(S4X, S4W, "audio_manifest.json", "`assets/audio/<hash>.wav` per utterance; failures recorded")
produce(S5X, S5W, "CHECKS.md", "one line per contract point, written by the agent; `adapt.log.json`: interaction and environment ids, status, seconds")

# ================================================================== (b) observation (right) and (c) repair loop (left)
OY = DY_ + DH_ + 70           # top of E / player / playthrough
CH_COMMIT = DY_ + DH_ + 20    # commit channel y
CH_SERVE = DY_ + DH_ + 36     # branch to player y

header(M, OY - 14, "(c) Repair loop  —  `verify.py: repair_loop`, shared by (6) and (7)")
PTW = 226
PTX = W - M - PTW
PLW = 240
PLX = PTX - 20 - PLW
header(PLX, OY - 14, "(b) Observation")

# scripted playthrough (6), under G
PTH = 236
node(PTX, OY, PTW, PTH, "6  Scripted playthrough",
     "`playtest.py`: serve G over local HTTP; headless Chromium via Playwright; wait for `window.playtest`; for each character of the selection: `goto`, `talk`, require `state()` to change; for each item: `goto`, `collect`, require it in `state()`; screenshot after every step; console and page errors; 90 s budget\n→ E with s(G)", body_size=9.4)
# human play (7)
node(PLX, OY, PLW, 92, "7  Human play",
     "the player opens `game/` from any static server; recorder on by default → `localStorage`: position every 1 s, every action, every line played, console errors, canvas shot every 5 s; “Download session” link", body_size=9.2)
doc(PLX + 40, OY + 110, PLW - 80, 40, "session.json", "uploaded by the player, offline")
rect(PLX, OY + 166, PLW, 70)
tline(PLX + 8, OY + 181, "watch.py · unpack_session", 10.5, weight="bold")
para(PLX + 8, OY + 195, "data-URL shots → `shots/`, events → `events.jsonl`, errors → `result.json`; review focus: where it broke, where the player got stuck (> 60 s), where the player was confused", PLW - 16, 9.0)
arrow([(cx(PLX, PLW), OY + 92), (cx(PLX, PLW), OY + 110)])
arrow([(cx(PLX, PLW), OY + 150), (cx(PLX, PLW), OY + 166)])

# G → playthrough and player
gcx = GX + GW / 2 + 20
arrow([(gcx, SY + SH), (gcx, OY)])
elabel(gcx - 6, SY + SH + 30, "G served as static files", anchor="end", size=8.8, bg=False)
dot(gcx, CH_SERVE)
arrow([(gcx, CH_SERVE), (cx(PLX, PLW) + 40, CH_SERVE), (cx(PLX, PLW) + 40, OY)])

# E bar
EX, EW, EH = M, PLX - 60 - M, 54
EY = OY
rect(EX, EY, EW, EH, fill=DOC_FILL, stroke=INK, sw=1.4)
tline(EX + 8, EY + 18, "E   evidence directory", 11.5, weight="bold")
tline(EX + 8, EY + 33, "`shots/NNN_label.png`   `events.jsonl`   `result.json` {score, errors, steps}", 9.4, fill=GREY)
tline(EX + 8, EY + 46, "round 0: `verification/round_0/before/` (6) or `verification/session_<ts>/` (7);  round n: `round_n/after/`", 9.4, fill=GREY)
# playthrough → E and unpack → E, merged in the channel between the player chain and E
CHX = PLX - 30
arrow([(cx(PTX, PTW), OY + PTH), (cx(PTX, PTW), OY + PTH + 20), (CHX, OY + PTH + 20), (CHX, EY + EH / 2), (EX + EW, EY + EH / 2)])
arrow([(PLX, OY + 201), (CHX, OY + 201)], head=False)
dot(CHX, OY + 201)
elabel(CHX - 6, EY + EH / 2 - 8, "evidence in", anchor="end", size=8.8, bg=False)

# strip
STY, STH = EY + EH + 44, 110
CRX, CRW = M, 300
node(CRX, STY, CRW, STH, "Critique",
     "in: E (≤ 24 screenshots, numbered event log, result), S, `slots`, `style`, manifest, `CONTRACT.md`, game source without protected files\nout: ≤ 8 defects by severity, each with evidence and search / replace fixes (d4)",
     kind="model", model="gemini-4-argon", extra="thinking medium · schema")
PAX, PAW = CRX + CRW + 66, 205
node(PAX, STY, PAW, STH, "Patch in staging",
     "copy of G without `node_modules` and sessions; `apply_fixes`: each search unique, protected files refused; `node_modules` symlinked")
BDX = PAX + PAW + 50
diamond(BDX, STY + STH / 2, 40, 22, ["builds?"], size=9.5)
RPX, RPW = BDX + 66, 196
node(RPX, STY, RPW, STH, "Replay",
     "same scripted playthrough on the staging copy → E′ with s(G′) and err(G′); saved under `round_n/after/`")
ACX = RPX + RPW + 70
diamond(ACX, STY + STH / 2, 60, 30, ["s(G′) ≥ s(G)", "∧ no new error"], size=9.2)

arrow([(EX + 120, EY + EH), (EX + 120, STY)])
elabel(EX + 128, EY + EH + 30, "round n ≤ N")
arrow([(CRX + CRW, STY + STH / 2), (PAX, STY + STH / 2)])
elabel(CRX + CRW + 33, STY + STH / 2 - 10, "first defect with", anchor="middle", size=8.6)
elabel(CRX + CRW + 33, STY + STH / 2 + 16, "evidence ∧ fixes", anchor="middle", size=8.6)
arrow([(PAX + PAW, STY + STH / 2), (BDX - 40, STY + STH / 2)])
arrow([(BDX + 40, STY + STH / 2), (RPX, STY + STH / 2)])
arrow([(RPX + RPW, STY + STH / 2), (ACX - 60, STY + STH / 2)])
arrow([(BDX, STY + STH / 2 + 22), (BDX, STY + STH + 10)])
tline(BDX, STY + STH + 24, "no: reject, stop", 9.0, fill=GREY, italic=True, anchor="middle")
arrow([(ACX, STY + STH / 2 + 30), (ACX, STY + STH + 10)])
tline(ACX, STY + STH + 24, "no: discard staging, stop", 9.0, fill=GREY, italic=True, anchor="middle")
# next round (dashed): accept → E
arrow([(ACX, STY + STH / 2 - 30), (ACX, STY - 24), (EX + EW - 80, STY - 24), (EX + EW - 80, EY + EH)], dashed=True)
elabel(ACX - 70, STY - 29, "yes: E ← E′, s(G) ← s(G′), next round", anchor="end")
# commit: accept → G (enters G from the left, below the build gate)
CMX = GX - 16
arrow([(ACX + 60, STY + STH / 2), (ACX + 100, STY + STH / 2), (ACX + 100, CH_COMMIT), (CMX, CH_COMMIT), (CMX, SY + SH - 30), (GX, SY + SH - 30)])
elabel(ACX + 108, CH_COMMIT - 4, "yes: copy the changed files into G; `report.json` records every round, score before / after, kept or reverted", size=8.8, bg=False)

# legend (between the strip and the player chain)
LGX, LGY = ACX + 120, STY - 8
LGW, LGH = PLX - 52 - LGX, STH + 40
rect(LGX, LGY, LGW, LGH, fill="#ffffff", stroke=GREY, sw=0.9)
tline(LGX + 8, LGY + 14, "Legend", 10.5, weight="bold")
col2 = LGX + LGW / 2 + 4
ly = LGY + 30
rect(LGX + 10, ly - 10, 30, 15, fill=ACC_FILL, stroke=ACC, sw=1.5)
tline(LGX + 48, ly + 1, "generative model call", 9.2)
rect(col2, ly - 10, 30, 15)
tline(col2 + 38, ly + 1, "deterministic code", 9.2)
ly += 26
out.append(f'<path d="M{LGX + 10},{ly - 10} h22 l8,8 v7 h-30 z" fill="{DOC_FILL}" stroke="{INK}" stroke-width="1.2"/>')
tline(LGX + 48, ly + 1, "artifact on disk", 9.2)
diamond(col2 + 15, ly - 2, 15, 8, [""])
tline(col2 + 38, ly + 1, "deterministic gate", 9.2)
ly += 26
rect(LGX + 10, ly - 10, 30, 15, fill=ACC_FILL, stroke=ACC, sw=1.5, dash="5,3")
tline(LGX + 48, ly + 1, "managed-agent sandbox", 9.2)
arrow([(col2, ly - 3), (col2 + 30, ly - 3)])
tline(col2 + 38, ly + 1, "data flow", 9.2)
ly += 26
arrow([(LGX + 10, ly - 3), (LGX + 40, ly - 3)], dashed=True)
tline(LGX + 48, ly + 1, "next round of the loop", 9.2)
ly += 22
para(LGX + 10, ly + 2, "Every model call is followed by a deterministic gate; every step is cached and resumable; no model runs while the player plays.", LGW - 20, 8.8, fill=GREY, italic=True)

# ================================================================== (d) definitions (bottom band)
DDY = STY + STH + 52
header(M, DDY - 14, "(d) Definitions")
NB, DG = 4, 20
DBW = (W - 2 * M - (NB - 1) * DG) / NB
DBH = H - DDY - 24
cols = [M + i * (DBW + DG) for i in range(NB)]
BS = 9.6

rect(cols[0], DDY, DBW, DBH)
tline(cols[0] + 8, DDY + 16, "d1  Ground truth S  (`story.json`, stage 2)", 11, weight="bold")
para(cols[0] + 8, DDY + 33,
     "characters: id, name, look, voice, [first, last] chapter\n"
     "chapters: summary, goal, beats {plain, original, source_ids}\n"
     "items: chapter, meaning, source_ids\n"
     "lines: character, chapter, plain, original, source_ids\n"
     "\n"
     "Invariants checked by `validate`, not by the model:\n"
     "∀ source_id: exists in the book ∧ lies in the element's chapter\n"
     "∀ chapter: |beats| ≥ 3;  ∀ line: chapter within its speaker's range\n"
     "∀ plain: |words| ≤ 14;  ids unique;  chapter order = book order\n"
     "The adapted game shows these texts and nothing else in a character's voice.",
     DBW - 16, BS)

rect(cols[1], DDY, DBW, DBH)
tline(cols[1] + 8, DDY + 16, "d2  Slot model  (`slots.json`, stage 3a)", 11, weight="bold")
para(cols[1] + 8, DDY + 33,
     "slot = ⟨id, role, kind, required, count, where {files, code}, format⟩\n"
     "role ∈ {player, npc, enemy, pickup, terrain, decoration, backdrop, portrait, ui, sound, music, font, parameter}; kind ∈ {sheet, tileset, image, model, material, colour, audio, font, text}\n"
     "\n"
     "grounded iff every named file exists ∧ claimed size ∈ measured sizes ∧ sheet divisible by its frame ∧ animation rows and frames fit ∧ metadata file and code refs exist ∧ a colour value is found in code; else rejected\n"
     "\n"
     "A fill is ⟨slot, subject⟩ → path, size, prompt; `replaces[upstream] = path`. The adapter rewires slots to fills, never draws, resizes or recolours (contract §12).",
     DBW - 16, BS)

rect(cols[2], DDY, DBW, DBH)
tline(cols[2] + 8, DDY + 16, "d3  Test interface  (`window.playtest`, contract §17)", 11, weight="bold")
para(cols[2] + 8, DDY + 33,
     "`characters()`  `items()`  →  ids and positions\n"
     "`goto(id)`  teleport next to a character or item\n"
     "`talk()`  `collect()`  interact with what is in front\n"
     "`state()`  chapter, beats seen, items collected, lines heard\n"
     "`screenshot()`  canvas as data URL\n"
     "\n"
     "Playthrough score  s(G) = number of passed steps: API present · each character of the selection present · each item present · talk changes `state()` · collect records the item · no console error\n"
     "Evidence  E = ⟨`shots/*.png`, `events.jsonl`, `result.json`⟩;  err(G) = console and page errors",
     DBW - 16, BS)

rect(cols[3], DDY, DBW, DBH)
tline(cols[3] + 8, DDY + 16, "d4  Patch acceptance  (`verify.py`)", 11, weight="bold")
para(cols[3] + 8, DDY + 33,
     "defect d = ⟨kind, severity, evidence, observed, expected, fixes⟩,  kind ∈ {crash, unreachable, stuck, story, accessibility, visual, rights}\n"
     "evidence = ∅  ⇒  d is discarded: no screenshot, log line or story id, no defect\n"
     "\n"
     "patch p = [⟨path, search, replace⟩] is applicable iff every `search` occurs exactly once in `path` and `path` ∉ {story, selection, manifests, LICENSE, NOTICE}\n"
     "\n"
     "Keep p iff G′ = G ⊕ p builds ∧ s(G′) ≥ s(G) ∧ err(G′) ⊆ err(G)\n"
     "One defect per round; at most 3 rounds (6) or 2 rounds (7); every before / after pair is kept.",
     DBW - 16, BS)

finish(Path(__file__).resolve().parent / "architecture", W, H, render="--render" in sys.argv)
