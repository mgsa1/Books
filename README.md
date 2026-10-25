# ExpLit

A book, a look, and an open-source game go in. A new game that tells the book's story comes out, for a reader who cannot engage with the page. Every line is spoken and subtitled. The game records how it is played, and Gemini 4 Argon reviews the recording and fixes what broke.

Built at the Gemini 4 Argon SF Hackathon, 25 Oct 2026. See [PLAN.md](PLAN.md).

## Setup

1. `cp .env.example .env` and paste your key from https://aistudio.google.com/api-keys
2. `uv sync && uv run playwright install chromium-headless-shell`
3. `uv run pipeline/smoke.py` runs four API checks: Argon JSON, image, speech, Managed Agent.
4. `uv run tests/test_backend.py` runs the no-model tests: parser, patcher, packing, Playwright driver.

## Run

Browser UI: `uv run server.py` then open http://127.0.0.1:8765. Pick book, chapters, style, game; build; play; upload a session for review.

Command line:

```bash
git clone --depth 1 https://github.com/Lunaneco/veilspire games/veilspire
uv run pipeline/run.py ressources/alice_in_wonderland.epub --game veilspire \
    --chapters c01 c02 --brief "soft watercolour storybook, gentle ink lines, pastel greens and gold"
```

Steps run in order and are skipped when their output exists: ingest, story, style, voice, adapt, verify. Use `--only` or `--force` to pick steps, `--fallback` to adapt with a direct Argon call instead of the Managed Agent, and `--refs ressources/style` to style from reference images.

Play: `cd builds/<book>/game && python -m http.server 8000`. The page offers a "Download session" link. Feed that file back: `uv run pipeline/watch.py builds/<book> session.json`.

## What each model does

| Job | Model |
|---|---|
| Whole-book story extraction, style bible, critique | gemini-4-argon |
| Rewriting the game | antigravity-preview-09-2026 running gemini-4-argon |
| Images | gemini-nano-banana-2.1 |
| Voice | gemini-3.8-flash-tts |

## Rights

Books are public domain or rights-cleared. Every image and sound is generated from the book's text and the user's style; prompts are refused if they name a franchise or artist. Starting games are fully open source (libre code and libre art) and keep their licenses; their art is replaced with generated art.

## Provenance

`poc/` and `games/` are pre-existing. Everything in `pipeline/`, `prompts/`, `schema/`, `tests/`, and `builds/` was written during the event.

## Pitch video
`video/` is a Remotion project for the explainer that accompanies the pitch. See [video/README.md](video/README.md).
