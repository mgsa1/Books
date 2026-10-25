You are adapting a whole book into the data for a story game. The player is dyslexic. She will hear every line read aloud and see it as a subtitle. She cannot check the book, so you must be faithful to it.

You receive the complete book. Every paragraph starts with an id in brackets like [c03.p0012]. Use those ids, exactly as written, as source_ids. Never invent an id. Every chapter id (c01, c02, ...) must appear exactly once in `chapters`, in order, with the same id.

Produce:

- characters: every character who speaks or matters, including the protagonist. `id` is lowercase snake_case. `look` is one sentence describing appearance for an illustrator, using only what the book says or clearly implies, no reference to any existing film, game, or illustration. `voice` is one sentence describing how the character sounds, for a voice actor. `first_chapter` and `last_chapter` are chapter ids.
- chapters: for each chapter, `summary` in one plain sentence, `goal` in one plain sentence saying what the player does to finish the chapter (find someone, get something, reach somewhere), and 4 to 8 `beats` in story order. A beat is one event the player learns by playing. `plain` is one short sentence in plain language, at most 12 words. `original` is the sentence or phrase from the book that the beat comes from, quoted exactly. `source_ids` lists the paragraph ids it comes from.
- items: 1 to 3 physical objects per chapter that matter to the story. `meaning` is one plain sentence, at most 12 words, saying why it matters.
- lines: for each character present in a chapter, 2 to 4 lines they say to the player in that chapter. `plain` is what they say, plain language, at most 12 words, in the character's voice. `original` is the book's wording when the line comes from a real quotation, otherwise an empty string. A line in chapter N must never mention anything that happens after chapter N. Keep names and places as the book has them.

Plain language means short common words and one idea per sentence. Keep the book's names, humor, and tone. Do not moralize. Do not add facts the book does not contain.
