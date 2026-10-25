# Adaptation contract

You are rewriting the open-source game in /workspace/game into a new game that tells the story in /workspace/story.json, for a dyslexic player who hears every line and sees it as a subtitle. Keep the engine, the controls, and the feel of the game. Replace everything about what it depicts.

Deliver a working game in /workspace/game. It must satisfy every point below. Check each one yourself before you finish, and write the result of each check to /workspace/CHECKS.md.

## Story
1. The game's levels, areas, or regions follow the chapters in story.json, in order. One chapter is one unit. Build the chapters listed in /workspace/selection.json; later chapters may be stubs that say "to be continued".
2. Every character in story.json whose chapter range covers a built chapter appears in that chapter, in a place that makes sense, and can be talked to.
3. When the player talks to a character, the character says its `lines` for that chapter from story.json, one line per interaction, in order, then repeats from the first. The game says nothing else in a character's voice.
4. Every beat of a built chapter is reachable by playing. Reaching the place or doing the action that corresponds to a beat shows the beat's `plain` text as narration. Beats appear in story order.
5. Every item of a built chapter can be found and collected. Collecting it shows its `meaning` as narration.
6. Each chapter ends when its `goal` is met. Show the chapter `summary` as narration when a chapter starts and the `goal` when it ends. Then move to the next chapter.

## Accessibility
7. Every line, beat, meaning, summary, and goal shown to the player is played as audio from /workspace/assets/audio/ using the path in /workspace/assets/audio_manifest.json, and shown at the same time as a subtitle, word for word.
8. Subtitles use the font Atkinson Hyperlegible (fall back to Verdana), at least 28px on a 1280px-wide canvas, high contrast on a solid box, letter-spacing 0.05em, line-height 1.6, at most two lines. The subtitle stays until the player presses the action key or moves on.
9. The original sentence (`original` field) is available: holding the action key or pressing a second key shows it and plays its audio when present.
10. No timers, no lives, no death, no game over. Falling or being hit returns the player to the last safe spot with no penalty. Enemies, if kept, do no damage. Progress is only by exploring, talking, and collecting.
11. Keyboard controls only, with an on-screen hint showing which key does what.

## Assets and rights
12. /workspace/slots.json lists every asset slot of the original game, and /workspace/assets/manifest.json says, per slot, which file now fills it (`fills[slot_id][subject_id].path`) or that it was kept from upstream (`kept_upstream`), must be removed with the code that places it (`remove`), or is `missing`. Your art job is rewiring, not art: point every slot at its filled replacement, or remove the slot together with the code that placed it. Do not resize, crop, recolour, or draw. Loader code and metadata formats stay as they were so the filled files drop in. A missing required asset is reported in CHECKS.md under "missing assets", not improvised.
13. Slots marked `synthetic` in slots.json do not exist upstream; add them: show `dialogue_portrait` for the speaking character beside the subtitle box, and `chapter_backdrop` full screen while the narrator reads the chapter summary.
14. UI colours, the subtitle box, menus, and every `parameter` slot take their values from /workspace/style.json `palette` and the manifest's `parameters`, so the game's chrome matches the art.
15. Remove every upstream image, sound, name, and text that is not kept by the manifest. Nothing from the original game's subject may remain, in file or in code.
16. Keep the upstream LICENSE file and add a NOTICE file naming the original project, its license, which upstream assets were kept and under what license, and what was changed.

## Testing hooks
17. Expose `window.playtest` with: `characters()` and `items()` returning ids and positions, `goto(id)` teleporting the player next to one, `talk()` and `collect()` triggering the interaction in front of the player, `state()` returning the current chapter, beats seen, items collected, lines heard, and `screenshot()` returning the canvas as a data URL.
18. Record every session: write to `localStorage['storyworld.session']` a JSON log with the player position every second, every action, every line played, every console error, and a low-resolution canvas screenshot every 5 seconds. Add a "Download session" link on the page.

## Build
19. The game runs from a static folder with `python -m http.server` from /workspace/game. If the original needs a build step, run it and commit the output, and document it in /workspace/game/README.md in five lines or fewer.
20. Do not add dependencies beyond what the original game already has.
