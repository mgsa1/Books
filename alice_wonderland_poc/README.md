# Alice in Wonderland — book → playable game (proof of concept)

A self-contained side exploration from the Argon hackathon (25 Oct 2026), separate from the main ExpLit pipeline in
this repo. **Gemini 4 Argon reads the whole book and designs a small Pokémon-style isometric game; every line of
dialogue is quoted word for word from Lewis Carroll, checked by a program, spoken by Gemini TTS, with a French
translation underneath.** Design rationale: [`PRINCIPLES.md`](PRINCIPLES.md) · models and what each did: [`MODELS.md`](MODELS.md).

## Play it
```bash
cd alice_wonderland_poc
python3 -m http.server 8780
open http://127.0.0.1:8780/                    # arrows: walk · space: talk / continue · M: sound on/off
```
Hands-free (autopilot walks, talks and advances when each voice line ends): `viewer/game.html?autopilot=1`;
closer camera for video: `&zoom=10`. Character-style comparison (chibi / paper / pixel / Argon voxels): `viewer/char_lab.html`.

## What's in the box
| Path | What |
|---|---|
| `game/script.json` | Argon's game script: 12 characters, 4 areas, 24 story beats, 79 verbatim lines (+ French translations) |
| `game/map_*.json` | Argon's tile maps, one per area, validated for reachability |
| `game/assets/` | Nano Banana portraits, story cards and pixel sprites (front/back/side) · Flash-TTS voice clips · Lyria music loops |
| `viewer/game.html` | The engine: Three.js isometric renderer, beats, dialogue, autopilot, event log (`window.__game.events`) |
| `scripts/` | The pipeline that produced everything above (see below) |
| `data/` | Project Gutenberg #11 (public domain) and its chapter split |

## Regenerate (needs `GEMINI_API_KEY`; the repo-root `.env` is found automatically)
```bash
pip install "google-genai>=2.30" python-dotenv pillow playwright   # or uv add …
python3 -I scripts/prepare_alice.py        # Gutenberg text → data/alice/chapters.json
python3 -I scripts/gen_game.py             # Argon: whole book → game/script.json (quotes verified, repaired)
python3 -I scripts/gen_map.py              # Argon: one map per area (BFS-validated, repaired)
python3 -I scripts/paint_game.py           # Nano Banana: portraits + story cards
python3 -I scripts/pixel_game.py           # Nano Banana: pixel sprites, 3 views per character (green-screen keyed)
python3 -I scripts/voice_game.py           # Argon casts voices → Flash TTS voices every line
python3 -I scripts/verify_audio.py         # local Whisper (mlx-whisper) checks every clip against its text
python3 -I scripts/music_game.py           # Argon writes briefs → Lyria loops; scripts/listen_music.py = Argon listens
python3 -I scripts/playtest.py rabbit_hole,rabbit_house,duchess_wood,queens_garden   # headless play-through
python3 -I scripts/record.py alice --from 0 --until 5 --zoom 10 --title 6             # 1080p autopilot recording
python3 -I scripts/mix_audio.py recordings/alice_0-5   # rebuild the soundtrack from the event log
python3 -I scripts/review_video.py recordings/alice_0-5  # Argon watches the video + log and reports bugs
```

## Honest notes
- **Illustrations are generated in the style of John Tenniel (1865), not his original engravings.** The originals are
  public domain and could replace the story cards.
- The book is 36K tokens, so Alice doesn't need Argon's 1M window; the same pipeline read all of *Les Misérables*
  (921K tokens) in one call, which is where the long context matters (that build is not included here).
- Known gaps: the underground hall shares the riverbank map; Alice doesn't shrink after "DRINK ME"; one Les Mis-only
  code path (map of France travel screen) remains in the engine.
