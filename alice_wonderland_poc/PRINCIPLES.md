# Les Misérables — le jeu · principles & design choices

*Models used: see `MODELS.md`. Argon hackathon, 25 Oct 2026. Built for Les Misérables (FR) and Alice in Wonderland (EN); this folder ships the Alice game.*

## The one-line pitch
Argon reads the **entire** French text of *Les Misérables* (921K tokens, in one call) and turns it into a
playable Pokémon-style RPG where you walk as Jean Valjean, and **every line of dialogue is Hugo's own words**,
verified by a program, with the chapter reference.

## How we got here (three iterations, same core)
1. **西游记 in 3D** — explorable scenes for a Mandarin learner. Proved the pipeline: text → world description → scene.
2. **Les Mis 2.5D dioramas** — paper-theatre parallax scenes in Hugo's ink style. Proved Nano Banana art + verified quotes.
3. **Les Mis RPG (current)** — follows the character through the story. Most engaging, best demo.
Each pivot kept the same backbone, so nothing was thrown away conceptually.

---

## Principle 1 — Grounded in the text, never invented
- Every quote must be **verbatim** (a contiguous run from the cited chapter). A checker normalises whitespace,
  apostrophes and guillemets, then does an exact substring match against that chapter.
- If the quote exists but in another chapter → we fix the reference locally (no model call).
- If it doesn't exist → it goes back to Argon to fix; anything still wrong after 3 rounds is **dropped**, not shown.
- Result so far: 79/79 game lines verified (78 first pass, 1 repaired).
- *Why:* the credibility of the whole thing rests on "these are Hugo's words". A hallucinated quote would kill it.

## Principle 2 — Use Argon for what only it can do: the whole book at once
- The full novel fits Argon's 1M-token window, so the script is written with **all 365 chapters in view** —
  continuity (who is where, when, alive or dead) comes from the whole story, not from chunks.
- Smaller jobs get smaller inputs: each town map gets only the chapters that describe that town (cheaper, faster).
- Prompt order: book first, instructions after (stable prefix, meant to benefit from implicit caching).

## Principle 3 — Generate → verify → repair, everywhere
Every generated artefact has a **programmatic check**, and failures go back to the model as concrete feedback:

| Artefact | Generator | Check | On failure |
|---|---|---|---|
| Dialogue lines | Argon (whole novel) | verbatim substring in cited chapter | Argon repairs; else drop |
| Script structure | Argon | every trigger target / speaker / spot exists | Argon repairs |
| Town map | Argon (town chapters) | in bounds, no overlaps, **BFS: every door/spot reachable** | Argon repairs (up to 5 rounds) |
| Cut-out images | Nano Banana | border must be plain paper (keyable) | repaint; last try without style reference |
| Blocked images | Nano Banana | safety filter refusal | **Argon rewrites the prompt** (suggest, don't show) |
| Whole game | — | **headless play-through of every beat** (Playwright) | we fix engine or data |
| Voiced lines | Gemini TTS (Argon casts voices + delivery tags) | **local Whisper transcript must match the text** | re-voice; drop the tag if it got read aloud |
| Music loops | Lyria (Argon writes the briefs) | **Argon listens**: vocals? matches brief? loops? (Whisper hallucinates on music) | regenerate, or crossfade away the ending cue |

This is the guide's "give Argon a verification loop" pattern, applied to content, not just code.
The play-test caught real issues (the sleeping bishop standing on the spot you must reach).

## Principle 4 — Clear division of labour
- **Argon = writer and level designer.** Script, characters, beats, maps, prompt rewrites.
- **Nano Banana = illustrator.** Portraits and key-moment cards, in one consistent style.
- **Deterministic code = engine and referee.** Rendering, movement, collisions, triggers, all the checks.
- Models produce **data (JSON) against a contract**; code never trusts it without checking.

## Principle 5 — Data contracts decouple the pieces
- `game/script.json` — characters, towns (buildings + named spots), ordered beats (trigger, NPCs, lines, effects).
- `game/map_<town>.json` — ASCII tile grid + buildings (with door tile) + spots + props + exits.
- Spots are **named** in the script and **positioned** by the map designer → script and maps can be generated
  independently and in parallel, and re-generated one at a time.
- One generic engine plays any script + maps: adding a town = data, not code.

## Principle 6b — Any book, same machine
A second book (*Alice's Adventures in Wonderland*, English, Tenniel style) went from text to a deployed,
fully play-tested game with **no new engine code** beyond palettes/props: one registry entry in
`scripts/books.py` (text, chapter labels, story scope, art style, UI strings). Same checks, same results:
79/79 lines verbatim, 4/4 maps valid on the first pass, 24/24 beats played headlessly.

## Principle 7 — The game watches itself (observability)
Generated content will produce situations nobody designed. So the game records what happens and checks
itself while it runs, instead of us discovering problems by watching the character "go banana".
- **Structured event log:** every beat start/end, trigger, dialogue line, move, blocked move, travel and
  error is an event with time, beat, town and position — readable by a person, a script or Argon.
- **Runtime invariants (soft-lock detectors):**
  - the current objective is **reachable** from where the player stands (BFS on the live grid, NPCs included);
  - no character stands on a door or on the only approach to the target;
  - the player isn't **stuck** (many blocked moves in a row, no progress on the beat for N seconds);
  - no **dialogue loop** (the same idle line reopened over and over);
  - the beat order only moves forward, and every `move_to` lands on a walkable tile.
- **When an invariant breaks:** log it with a snapshot of the state, show a discreet hint or auto-nudge
  (move an NPC aside, highlight the target), and never leave the player trapped.
- **Triage loop:** the headless play-through and real sessions both produce the same log; failures get
  grouped by cause and fed back — to the engine (rule fix) or to Argon (content fix, e.g. "spot X is in a
  doorway"). Today's bugs (bishop on the target, crowd blocking the inn door, wrong person answering,
  stuck arrow keys) were all found this way, by hand; this principle makes it automatic.
- *Why:* with model-generated levels you can't test every case in advance; you can make every failure
  visible, explainable and recoverable.

## Principle 8 — The player stays in control; nothing external is touched
- No actions on external systems, money or private data. Static site, no API key on the server.
- Everything generated is reviewable (JSON + images on disk) before it ships.

---

## Design choices (and why)
- **Low-poly isometric 3D, not generated sprites.** Image models can't keep a walking character consistent
  frame to frame; Three.js primitives under an orthographic iso camera are consistent, cheap and editable.
- **Hugo's own ink-wash drawings as the art direction** (sepia ink, wash, blots) for portraits and story cards.
  Hugo was a serious draughtsman — the style is *from* the source, not decoration.
- **Story cards for the 4–6 big moments** (bishop's welcome, the candlesticks…): full-screen illustration
  behind the dialogue, where a low-poly scene can't carry the emotion.
- **French first, English underneath, chapter reference always visible.** Reading the real text is the point.
- **Beats as the unit of story.** Each beat = objective + trigger (start / talk / enter / reach) + lines + effects
  (new name, item, move to next town). Simple enough for Argon to write reliably, rich enough to tell the story.
- **Forgiving engine rules** instead of brittle content: several characters on one spot are spread onto nearby
  tiles; bumping into an occupied target spot counts as reaching it.
- **Scope: Tome I arc in three towns** — Digne (the bishop, the candlesticks), Montreuil-sur-Mer (M. Madeleine,
  Fauchelevent, Javert, Fantine), Montfermeil (Cosette, the Thénardiers, the doll).
- **UI typography:** Didot / Baskerville, paper `#EFE6D2`, ink `#2B2118`, one red `#8E1F1A` for names and "!".
  (Non-Mac machines fall back to Georgia.)

## Numbers worth knowing
- Whole novel: 3.1M characters, 365 chapters, **921K tokens** → ~2.5–3.5 min per Argon call, ~$1.75 input.
  Leaves ~75K tokens for thinking + output, so outputs are capped (~60K).
- Repair rounds via `previous_interaction_id` re-billed the full input (no cache hit observed).
- Town map (chapters only): ~2.5 min, valid on first pass for Digne.
- Nano Banana: ~20 s per image at 1K, run 8 in parallel → a town's art in ~30 s.

## Known limitations / open questions
- Argon sometimes breaks its own "one moment in time" rule (seen in the dioramas) → a timeline-consistency
  review pass would help.
- Interiors are abstracted: "inside" scenes trigger at the door and play over a story card.
- Voice is the browser's built-in French TTS; Gemini TTS would be a big upgrade for the demo.
- Outside the town walls is flat colour; no overworld walking (travel is an animated ink map of France).

## Demo plan (< 3 min)
1. Title screen → "every line is verbatim Hugo". 2. Walk into Digne, get turned away at the inn (real lines).
3. Bishop's house → story card. 4. Candlesticks scene → Myriel's actual words. 5. Travel map to Montreuil.
6. Close on the pipeline: one slide/diagram of generate → verify → repair, with the counts above.

## Where things are (`hackathons/argon/`)
`scripts/gen_game.py` (script) · `scripts/gen_map.py` (maps) · `scripts/paint_game.py` (art) ·
`viewer/game.html` (engine) · `scripts/playtest.py` (headless play-through) · `scripts/lesmis.py` (text + quote
checker) · `CLAUDE.md` (gotchas, deployment) · earlier iterations: `viewer/diorama.html`, `viewer/index.html`.

---

## Backlog (next)
1. **Argon refactors an existing open-source game, then the story is applied to it.** Take a well-known
   open-source top-down RPG/adventure engine (e.g. a JS/TS or Godot project with its own map, NPC and dialogue
   systems), have Argon read the *whole codebase* in its 1M window, refactor it to load our data contracts
   (`script.json` beats, `map_*.json` tiles/spots, portraits, voice clips), and verify with its existing test
   suite plus our headless play-through. Demonstrates Argon's long-horizon multi-file refactoring on a real
   codebase — the other half of the hackathon brief — with the book pipeline as the content source.
   Pick a project with a permissive licence (MIT/Apache) and a test suite; keep the original licence and credits.
2. **Principle 7 in code:** event log, soft-lock detectors (objective unreachable, stuck, dialogue loop),
   auto-nudge, and logs fed back to the engine/Argon.
3. **Cache headers on the VPS** (`Cache-Control: no-cache` for HTML/JSON) so judges never see a stale build.
4. **Timeline-consistency review pass** by Argon over the script (the "one moment in time" rule).
