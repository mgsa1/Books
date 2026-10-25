You are reading the complete source of a browser game to list every asset slot it has. A slot is anything the code loads or defines that gives the game its look or sound: an image, a sprite sheet with animations, a tile set, a 3D model or procedural shape, a material, a colour constant or palette, an audio file, a font, or a visible text value such as a title or a character name. Later, other people will fill each slot with new art made from a book. They can only do that if your description of the slot's exact format is right, so read the loader code, not just the file names.

For every slot give:

- `id`: short lowercase snake_case, unique.
- `role`: what the engine uses it for: player, npc, enemy, pickup, terrain, decoration, backdrop, portrait, ui, sound, music, font, parameter.
- `kind`: sheet (frames in a grid), tileset, image, model, material, colour, audio, font, text.
- `required`: true if the game fails to run or looks broken without it.
- `subject_hint`: what the upstream asset depicts, in a few words.
- `count`: how many distinct instances of this slot the game can place at once (one player, N NPC types, M item types).
- `where.files`: every upstream file path for this slot, relative to the repo root, including scaled copies. Empty for procedural slots.
- `where.code`: the code locations that load, define, or place it, as `path:line`.
- `format`: exactly what the loader reads. For a sheet: frame_width, frame_height, animations with row index and frame count, facings, anchor, metadata_file if frame data lives in a JSON or JS file. For a tileset: tile_size, width, height. For an image: width, height, transparent, aspect_ratio. For a model or material: notes describing the procedural construction and which parameters shape its look. For a colour: value_type and current_value as written in code. Put anything else that matters in notes.

Also write `engine_notes`: five to ten sentences on how this engine loads assets, how NPC dialogue and quests are defined, where the player and NPCs are placed, and where UI colours and fonts come from. Group near-duplicate files (the same sprite at several scales) into one slot. Do not list build tooling, tests, or documentation images. Be complete: a slot you miss will stay upstream art.
