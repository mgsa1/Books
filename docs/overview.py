#!/usr/bin/env python3
"""Storyworld overview figure: the architecture at a glance (intro figure).

    uv run docs/overview.py            # writes docs/overview.svg
    uv run docs/overview.py --render   # also overview.png (2x) and overview.pdf

Same visual language as docs/architecture.py, a tenth of the text. Keep both in step with pipeline/*.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import *  # noqa: E402,F401

W, H = 1520, 660
begin(W, H)

TS, BS = 14.5, 11.2          # title and body sizes for this figure


def box(x, y, w, h, title, body, kind="proc", model=None):
    fill = ACC_FILL if kind == "model" else (DOC_FILL if kind == "out" else "#ffffff")
    stroke = ACC if kind == "model" else INK
    rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.8 if kind in ("model", "out") else 1.4)
    ty = y + 22
    tline(x + 12, ty, title, TS, weight="bold")
    if model:
        tline(x + 12, ty + 16, model, 10.5, fill=ACC, family=MONO)
        ty += 16
    para(x + 12, ty + 20, body, w - 24, BS, lh=BS * 1.38)


def col_label(x, y, s):
    tline(x, y, s, 11.5, weight="bold", fill=GREY)


def gate(cx_, cy_, label, size=9.6):
    diamond(cx_, cy_, 38, 16, [label], size=size)


# ---------------------------------------------------------------- columns
IX, IW = 30, 150            # inputs
UX, UW = 230, 230           # understand
GX_, GW_ = 540, 250         # generate
AX, AW = 870, 250           # adapt
PX, PW = 1200, 270          # play (the game)
RY = [70, 165, 260]         # three rows
RH = 72
TOP, BOT = 70, 332          # tall boxes

col_label(IX, 52, "INPUTS")
col_label(UX, 52, "UNDERSTAND  ·  gemini-4-argon")

col_label(GX_, 52, "GENERATE")
col_label(AX, 52, "ADAPT  ·  managed agent")
col_label(PX, 52, "PLAY")

# inputs
doc(IX, RY[0] + 6, IW, RH - 12, "Book", "EPUB, public domain", size=12)
doc(IX, RY[1] + 6, IW, RH - 12, "Look", "reference images or a brief", size=12)
doc(IX, RY[2] + 6, IW, RH - 12, "Game", "libre open-source repository", size=12)

# understand: three authorities
box(UX, RY[0], UW, RH, "Story  S", "what happens: characters, beats, lines, each citing its paragraph", kind="model")
box(UX, RY[1], UW, RH, "Style bible", "how it looks: palette, prompt prefix, one rule per asset kind", kind="model")
box(UX, RY[2], UW, RH, "Slots", "what must exist, in which format: every asset the code loads", kind="model")
for i in range(3):
    arrow([(IX + IW, RY[i] + RH / 2), (UX, RY[i] + RH / 2)])

# gates after story and slots (checked against the book / the files)
GAPX = (UX + UW + GX_) / 2
arrow([(UX + UW, RY[0] + RH / 2), (GAPX - 38, RY[0] + RH / 2)])
gate(GAPX, RY[0] + RH / 2, "validate")
arrow([(GAPX + 38, RY[0] + RH / 2), (GX_, RY[0] + RH / 2)])
arrow([(UX + UW, RY[1] + RH / 2), (GX_, RY[1] + RH / 2)])
arrow([(UX + UW, RY[2] + RH / 2), (GAPX - 38, RY[2] + RH / 2)])
gate(GAPX, RY[2] + RH / 2, "ground")
arrow([(GAPX + 38, RY[2] + RH / 2), (GX_, RY[2] + RH / 2)])
tline(GAPX, RY[0] + RH / 2 + 30, "against the book", 9, fill=GREY, italic=True, anchor="middle")
tline(GAPX, RY[2] + RH / 2 + 30, "against the files", 9, fill=GREY, italic=True, anchor="middle")

# generate
box(GX_, TOP, GW_, BOT - TOP, "Cast and fill",
    "The book decides what each slot depicts, the look decides how it looks, the game decides the format.\n\n"
    "One image per slot and subject, fitted to the slot's exact size and sheet grid.\n`gemini-nano-banana-2.1`\n\n"
    "One audio clip per line, beat and narration.\n`gemini-3.8-flash-tts`\n\n"
    "→ assets + manifests, cached", kind="model")

# adapt
arrow([(GX_ + GW_, (TOP + BOT) / 2), (AX, (TOP + BOT) / 2)])
box(AX, TOP, AW, BOT - TOP, "Rewrite the game",
    "The agent gets the whole repository, the story, the slots, the style and a 20-point contract in a remote sandbox. "
    "It keeps the engine and the controls, rewires every asset slot to its generated replacement, and rewrites the story logic: "
    "one chapter per level, every character says its lines and nothing else, no timers, no fail states.\n\n"
    "Never draws, resizes or invents art.",
    kind="model", model="antigravity-preview-09-2026 · gemini-4-argon")
# game repo also feeds adapt (bus under the rows)
BUSY = BOT + 16
arrow([(IX + IW / 2, RY[2] + RH - 6), (IX + IW / 2, BUSY), (AX + 40, BUSY), (AX + 40, BOT)])
elabel(IX + IW / 2 + 8, BUSY - 5, "repository", size=9, bg=False)

# build gate, then the game
BG = (AX + AW + PX) / 2
arrow([(AX + AW, (TOP + BOT) / 2), (BG - 38, (TOP + BOT) / 2)])
gate(BG, (TOP + BOT) / 2, "builds?")
arrow([(BG + 38, (TOP + BOT) / 2), (PX, (TOP + BOT) / 2)])
box(PX, TOP, PW, BOT - TOP, "The game  G",
    "Static files, playable from any web server.\n\n"
    "Every line is spoken and shown as a subtitle. Progress by exploring, talking and collecting; nothing to read, nothing to lose.\n\n"
    "Exposes `window.playtest` for testing and records every session.\n\n"
    "No model call while the player plays.",
    kind="out")

# ---------------------------------------------------------------- repair loop
LY = 420
LH = 106
col_label(GX_ + 44, LY - 22, "REPAIR LOOP  ·  the game watches itself: scripted playthroughs before release, real sessions after; same loop, at most three rounds")
OX, OW = GX_, 200
CX_, CW = OX + OW + 30, 210
PTX, PTW = CX_ + CW + 30, 140
RX_, RW = PTX + PTW + 30, 140
ACX = RX_ + RW + 30 + 62
assert ACX + 62 < W - 20

box(OX, LY, OW, LH, "Observe", "Playwright drives the test API, or the player uploads a session → screenshots, event log, score s(G)")
box(CX_, LY, CW, LH, "Critique", "defects with evidence, each with a small search / replace fix; no evidence, no defect", kind="model", model="gemini-4-argon")
box(PTX, LY, PTW, LH, "Patch", "in a staging copy; must still build")
box(RX_, LY, RW, LH, "Replay", "same playthrough → s(G′)")
diamond(ACX, LY + LH / 2, 62, 30, ["s(G′) ≥ s(G)", "∧ no new error"], size=9.8)

arrow([(OX + OW, LY + LH / 2), (CX_, LY + LH / 2)])
arrow([(CX_ + CW, LY + LH / 2), (PTX, LY + LH / 2)])
arrow([(PTX + PTW, LY + LH / 2), (RX_, LY + LH / 2)])
arrow([(RX_ + RW, LY + LH / 2), (ACX - 62, LY + LH / 2)])

# G → observe (play), accept → G (commit)
SERVE_Y = LY - 44
arrow([(PX + 50, BOT), (PX + 50, SERVE_Y), (OX + 22, SERVE_Y), (OX + 22, LY)])
elabel(OX + 30, SERVE_Y - 5, "play the current build", size=9, bg=False)
arrow([(ACX, LY + LH / 2 - 30), (ACX, BOT)])
elabel(ACX - 8, BOT + 40, "yes: keep the patch", anchor="end", size=9, bg=False)
tline(ACX + 66, LY + LH / 2 + 4, "no:", 9.6, fill=GREY, italic=True)
tline(ACX + 66, LY + LH / 2 + 16, "revert", 9.6, fill=GREY, italic=True)
# next round
arrow([(ACX, LY + LH / 2 + 30), (ACX, LY + LH + 32), (OX + OW / 2, LY + LH + 32), (OX + OW / 2, LY + LH)], dashed=True)
elabel((OX + ACX) / 2, LY + LH + 28, "next round", anchor="middle", size=9)

# ---------------------------------------------------------------- legend and footer
LGX, LGY = 30, LY
rect(LGX, LGY - 6, 460, 112, fill="#ffffff", stroke=GREY, sw=0.9)
tline(LGX + 10, LGY + 12, "Legend", 10.5, weight="bold")
ly = LGY + 32
rect(LGX + 12, ly - 10, 30, 15, fill=ACC_FILL, stroke=ACC, sw=1.5)
tline(LGX + 50, ly + 1, "generative model call", 10)
rect(LGX + 250, ly - 10, 30, 15)
tline(LGX + 288, ly + 1, "deterministic code", 10)
ly += 26
out.append(f'<path d="M{LGX + 12},{ly - 10} h22 l8,8 v7 h-30 z" fill="{DOC_FILL}" stroke="{INK}" stroke-width="1.2"/>')
tline(LGX + 50, ly + 1, "input or output on disk", 10)
diamond(LGX + 265, ly - 2, 15, 8, [""])
tline(LGX + 288, ly + 1, "deterministic gate", 10)
ly += 26
arrow([(LGX + 12, ly - 3), (LGX + 42, ly - 3)])
tline(LGX + 50, ly + 1, "data flow", 10)
arrow([(LGX + 250, ly - 3), (LGX + 280, ly - 3)], dashed=True)
tline(LGX + 288, ly + 1, "next round of the loop", 10)

para(30, H - 60,
     "Every model output passes a deterministic check before the next step uses it. "
     "Argon reads the whole book and the whole game repository in one context, so one pass rewrites the game faithfully; "
     "the loop fixes what the pass got wrong, with evidence. All of this runs offline: the player's game never calls a model.",
     W - 60, 10.8, fill=GREY, italic=True)

finish(Path(__file__).resolve().parent / "overview", W, H, render="--render" in sys.argv)
