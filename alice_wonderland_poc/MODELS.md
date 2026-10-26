# Models used — and what for

*Argon hackathon, 25 Oct 2026. Counts are approximate (from logs and asset folders), across all iterations
(西游记 3D → Les Mis dioramas → Les Mis game → Alice game).*

## Generative models (Google, via the Interactions API)

| Model | Role | What it did in this project | Approx. volume |
|---|---|---|---|
| **`gemini-4-argon`** | Lead model: writer, designer, reviewer, critic | • **Read the whole novel in one call** (Les Mis 921K tokens, Alice 36K) and wrote the game script: characters, areas, story beats, verbatim lines + translations<br>• Designed every **town map** (tile grid, buildings, spots, props) from the chapters describing it<br>• Designed the 2.5D **diorama** layouts (depth, position, image prompts)<br>• **Repaired** its own output from program feedback: non-verbatim quotes, broken references, unreachable map tiles, malformed JSON<br>• **Cast the voices** (voice + delivery tag per character)<br>• Wrote the **music briefs** per area<br>• **Listened** to every music loop (audio in): vocals? matches brief? loops?<br>• **Watched** a 6.7-min play-through video + event log and reported bugs with timestamps; picked the 20-s highlight window<br>• **Looked** at full-body paintings and designed **voxel** 3D characters<br>• **Rewrote prompts** blocked by the image/speech safety filters | ~40 calls; 4 whole-novel reads of Les Mis (~0.9M tokens each) |
| **`gemini-nano-banana-2.1`** (Nano Banana 2.1) | Illustrator | • Hugo ink-wash **diorama** backdrop + cut-outs (Les Mis)<br>• **Portraits** for every character (Hugo style for Les Mis, Tenniel style for Alice)<br>• Full-screen **story cards** for the key moments<br>• Full-body **paper cut-out** figures (HD-2D test)<br>• **Pixel-art sprites**: front / back / side per character, back and side drawn from the front as a reference | ~120 images |
| **`gemini-3.8-flash-tts`** | Voice actor | • Every dialogue line voiced in the book's original language (79 English lines for Alice, 79 French for Les Mis), one voice per character, with inline delivery tags | ~180 clips (incl. re-voices) |
| **`lyria-3-clip-preview`** (Lyria) | Composer | • 30-s instrumental loop per area + a title theme for each game | 9 loops |

Defined in `argon.py` but **not used**: `gemini-3.8-flash`, `gemini-3.5-flash-lite` (everything stayed on Argon;
Flash would be the natural choice for cheap parallel sub-tasks like voice casting or prompt rewrites).

## Local / open models (on the Mac, no API)

| Model | Role | What it did |
|---|---|---|
| **Whisper large-v3-turbo** (`mlx-community/whisper-large-v3-turbo`, via mlx-whisper) | Ear for QA | • Transcribed every voice clip and compared it to the script → caught clips that **read their stage direction aloud** ("Furious, booming, tyrannical! Off with her head!"), garbled or swapped lines<br>• Checked the audio/video sync of the recorded play-through<br>• *Not* used for music: it hallucinates words on instrumentals ("Music Music Music") — Argon listens instead |

## The coding agent

| Model | Role | What it did |
|---|---|---|
| **Claude Opus 5.5** (Claude Code) | Engineer | Built the pipeline and every checker (quote verifier, map validator with BFS, paper/green-screen keying, voice verifier), the Three.js engines (3D scene, diorama, isometric game, autopilot, event log), the recording + audio-remix pipeline, and the deployment. Wrote no story content: all lines are Hugo's/Carroll's, all design decisions above are Argon's. |

## Non-AI tools worth crediting
Three.js (rendering, served locally), Playwright + Chromium (headless play-tests and 1080p recording), ffmpeg (audio
remix, ducking, clips), Pillow (keying, pixel snapping), OpenCC + pypinyin + CC-CEDICT + HSK 3.0 list (西游记 prototype),
Project Gutenberg (all source texts), Caddy on the VPS (hosting).

## Division of labour in one line
**Argon decides and checks, Nano Banana draws, Flash TTS speaks, Lyria plays, Whisper listens, code referees.**
