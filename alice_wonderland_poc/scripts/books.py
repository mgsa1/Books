"""Book registry: one place that says how each book is read, cited, staged and drawn.
Generators pick the book with the BOOK env var (default: lesmis), e.g.

    BOOK=alice .venv/bin/python -I scripts/gen_game.py

A Book exposes the same API the Les Mis scripts already used: book_text(), check(d),
iter_quotes(d), ref_label(ref), BY_REF, plus paths, story scope, art style and UI strings.
Field names in the game JSON are historical: `text_fr` = the line in the book's ORIGINAL
language, `text_en` = its translation (English for Les Mis, French for Alice).
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("«", '"').replace("»", '"').replace("“", '"').replace("”", '"')
    s = s.replace("…", "...").replace("—", "--").replace("–", "-").replace("_", "")
    return re.sub(r"\s+", "", s)


def roman(n):
    out = ""
    for v, s in [(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while n >= v:
            out += s; n -= v
    return out


class Book:
    def __init__(self, id, chapters, label, header, game_dir, assets_dir, story, style, ui, characters_hint, seasons, narrator):
        self.id = id
        self.CHAPTERS = json.loads((ROOT / chapters).read_text())
        self.BY_REF = {c["ref"]: c for c in self.CHAPTERS}
        self.NORMED = {r: norm(c["text"]) for r, c in self.BY_REF.items()}
        self._label, self._header = label, header
        self.game_dir, self.assets_dir = ROOT / game_dir, ROOT / assets_dir
        self.story, self.style, self.ui = story, style, ui
        self.characters_hint, self.seasons, self.narrator = characters_hint, seasons, narrator

    def ref_label(self, ref):
        c = self.BY_REF.get(ref)
        return self._label(ref, c)

    def book_text(self):
        return "\n\n".join(f"【{c['ref']}】 {self._header(c)}\n{c['text']}" for c in self.CHAPTERS)

    @staticmethod
    def iter_quotes(d):
        if q := d.get("backdrop", {}).get("quote"):
            yield "backdrop", q
        for e in d.get("elements", []):
            yield e.get("id", "?"), e["quote"]

    def check(self, d):
        fails = []
        for where, q in self.iter_quotes(d):
            n = norm(q["text_fr"])
            if n in self.NORMED.get(q["ref"], ""):
                continue
            found = [r for r, t in self.NORMED.items() if n in t]
            fails.append({"where": where, "quote": q["text_fr"], "reason": f"found in {found[0]}, not {q['ref']}" if found else "not in the text",
                          "found": found[0] if found else None})
        return fails


TOMES = ["", "I", "II", "III", "IV", "V"]


def _lesmis_label(ref, c):
    t, l, ch = (int(x) for x in ref.split("."))
    label = f"Tome {TOMES[t]}, livre {roman(l)}, chapitre {roman(ch)}"
    return f"{label} — {c['title']}" if c else label


LESMIS = dict(
    id="lesmis", chapters="data/lesmis/chapters.json", label=_lesmis_label,
    header=lambda c: f"Tome {TOMES[c['tome']]} · Livre {c['livre']} « {c['livre_title']} » · Chapitre {c['chapitre']} « {c['title']} »",
    game_dir="game", assets_dir="assets_game", narrator="narrateur",
    story=None,  # gen_game.py keeps its original Les Mis prompt
    style=("Drawn in the manner of Victor Hugo's own ink-wash drawings (1850s-60s): sepia and brown-black ink, "
           "loose wash, splatters and blots, dramatic chiaroscuro; a touch of dark red only where the subject is red."),
    ui=None, characters_hint=None, seasons=None,
)

ALICE = dict(
    id="alice", chapters="data/alice/chapters.json",
    label=lambda ref, c: f"Chapter {roman(int(ref))} — {c['title']}" if c else f"Chapter {ref}",
    header=lambda c: f"CHAPTER {roman(c['n'])} « {c['title']} »",
    game_dir="game", assets_dir="game/assets", narrator="narrator",
    story="""You are the game writer for a small top-down RPG (Pokémon-style) adaptation of Lewis Carroll's *Alice's Adventures in Wonderland*. The complete original English text is above; each chapter starts with 【N】.

The player IS Alice. Cover the whole book in exactly four areas ("towns"), in story order:
  1. rabbit_hole — the riverbank, the White Rabbit with his watch, the fall, the hall of doors, the little golden key, "DRINK ME" and "EAT ME", the pool of tears (chapters 1-2).
  2. rabbit_house — the White Rabbit's house (Alice grows inside it, Bill the Lizard), the wood, the Caterpillar on the mushroom (chapters 4-5).
  3. duchess_wood — the Duchess's house (the Cook, the pepper, the baby that turns into a pig), the Cheshire Cat in the tree, the March Hare's house and the Mad Tea-Party (chapters 6-7).
  4. queens_garden — the rose-tree painted red by the gardeners, the croquet-ground with flamingos and hedgehogs, the Queen of Hearts, the Gryphon and Mock Turtle by the sea, the court and the trial, waking up on the bank (chapters 8-12).
Use effects.move_to to send Alice on when an area's story is done.""",
    characters_hint="valid examples: alice (blue dress, white pinafore, long fair hair), white_rabbit (white, waistcoat, small), caterpillar (blue), cheshire_cat, mad_hatter (huge hat), march_hare, dormouse, duchess, queen_of_hearts (red), king_of_hearts, knave_of_hearts, gryphon, mock_turtle",
    seasons="day | wonder-day | dusk-garden",
    style=("Drawn in the manner of John Tenniel's original wood-engraved illustrations for Alice's Adventures in Wonderland (1865): "
           "crisp black ink linework and fine cross-hatching, Victorian costume, lightly hand-tinted in soft watercolour as in The Nursery Alice."),
    ui={"title": "Alice’s Adventures in Wonderland", "subtitle": "Lewis Carroll · the game",
        "intro": ["You are Alice. A warm afternoon on the riverbank, a book with no pictures — and a White Rabbit with a pocket-watch.",
                  "Every line is quoted word for word from the book."],
        "start": "press space to begin", "end_title": "The End", "end_subtitle": "Alice wakes up on the bank",
        "end_go": "“Oh, I’ve had such a curious dream!”", "travel": "fall", "quote_open": "“", "quote_close": "”",
        "keys": "arrows: walk · space: talk / continue", "door_closed": "The door is locked.", "item_prefix": "You get: ",
        "items_label": "Items: ", "font_display": "\"Iowan Old Style\", Palatino, Georgia, serif"},
)

# This POC ships Alice only; the Les Mis entry is kept as a second example of a registry entry
# (its text is not included here). Add a book = add a dict + its data/<book>/chapters.json.
REGISTRY = {"alice": ALICE}
BOOK = Book(**REGISTRY[os.environ.get("BOOK", "alice")])
