# ExpLit explainer video

A Remotion project that accompanies the pitch. About 95 seconds, 1920x1080, 30 fps.

Scenes, in order: the friend (a wall of text, then Alice's own line about books
without pictures or conversations), the ExpLit title, the pipeline (book + look +
game → Argon → new game), the accessibility rules, the self-watching loop, why
Gemini 4 Argon (the context window filling up), outro.

## Two cuts, one script

Remotion Studio lists two compositions:

- **ExpLit**: the lean cut. Paper, ink, one clay accent, a serif for headlines.
- **ExpLitPlayful**: the same scenes, words and timing in a playful scrapbook
  style: chunky rounded type, pastel stickers, and public-domain book
  illustrations (Tenniel, Rackham, Potter, Denslow, Shepard) as cut-outs.

Both read [src/script.ts](src/script.ts), so a wording or timing change lands
in both. The playful scenes live in `src/playful/`.

The illustrations are in `public/pd/` with sources and rights in
[public/pd/CREDITS.md](public/pd/CREDITS.md). `public/pd/cut/` holds the same
drawings with the scanned paper keyed out to transparency, made by
`scripts/keyout.py`:

```bash
uv run --no-project --with pillow python -I scripts/keyout.py public/pd public/pd/cut white-rabbit.png alice.png
```

Note on Pooh: Shepard's 1926 drawings are public domain in the US only.
Remove `pooh` from `src/playful/art.ts` and its uses if publishing elsewhere.

## Edit the words

Everything spoken or shown lives in [src/script.ts](src/script.ts): narration per
scene, on-screen labels, scene durations in seconds, the brand strings and the
GitHub link. The scenes in `src/scenes/` only lay things out.

The narration is drawn as subtitles at the bottom of the frame in the same style
the game uses (large, high contrast, 12 words max). Keep each narration line at
or under 12 words so it stays on one line.

## Run

```bash
cd video
npm install
npm run dev        # Remotion Studio, live preview with a scrubber
npm run render     # out/explit.mp4 at full resolution
npm run still      # out/cover.png, one frame for the thumbnail
npm run narration  # prints the narration as plain text for a TTS pass
```

## Add a voiceover

1. `npm run narration > narration.txt`, then record it or run it through
   `gemini-3.8-flash-tts` (the pipeline's `voice.py` already knows how).
2. Save the result as `video/public/voiceover.mp3`.
3. In `src/script.ts` set `VOICEOVER_FILE = 'voiceover.mp3'`.
4. Adjust each scene's `seconds` so the subtitles land with the voice.
   Subtitles split a scene's time between lines by word count, so they roughly
   follow a natural reading pace already.
