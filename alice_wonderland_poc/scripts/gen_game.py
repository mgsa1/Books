"""Argon reads the whole novel and writes the game script: characters, towns, story beats
with verbatim lines. Repairs non-verbatim quotes.

    .venv/bin/python -I scripts/gen_game.py            -> game/script.json
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from argon import ARGON, client  # noqa: E402
from books import BOOK as lesmis  # noqa: E402  (BOOK env var picks the book; name kept for the Les Mis code paths)

GAME = lesmis.game_dir
GAME.mkdir(parents=True, exist_ok=True)

FORMAT = r"""
{
  "title_fr": "...",
  "player": {"character": "valjean"},
  "characters": [
    {"id": "valjean", "name_fr": "Jean Valjean", "name_en": "...",
     "colors": {"coat": "#hex", "trousers": "#hex", "hat": "#hex or null", "hair": "#hex", "skin": "#hex"},
     "build": "tall|average|small|child",
     "portrait_prompt": "head-and-shoulders portrait at this point in the story, concrete details from Hugo's description"}
  ],
  "towns": [
    {"id": "digne", "name_fr": "Digne", "name_en": "...", "refs": ["1.2.1", ...],
     "layout_en": "What the town map must contain and how it is arranged, from Hugo's text (streets, square, cathedral, inns, the bishop's house, the prison, the city gate, gardens...). 4-8 sentences.",
     "buildings": [{"id": "croix_de_colbas", "name_fr": "L'auberge de la Croix-de-Colbas", "kind": "inn|house|church|hall|prison|shop|factory|convent|ruin|other", "enterable": true}],
     "spots": [{"id": "bishop_door", "description_en": "the door of the bishop's house"}],
     "entry_spot": "spot id where the player appears when arriving"}
  ],
  "beats": [
    {"id": "b01_arrival", "town": "digne",
     "objective_fr": "short imperative, e.g. Trouver un gîte pour la nuit", "objective_en": "...",
     "trigger": {"type": "start|talk|enter|reach", "target": "character id (talk) | building id (enter) | spot id (reach) | null (start)"},
     "npcs": [{"character": "id", "spot": "spot id"}],
     "lines": [{"speaker": "character id or narrateur", "ref": "1.2.1", "text_fr": "VERBATIM", "text_en": "..."}],
     "card_prompt": "optional: a full-screen illustration of this key moment (only for 4-6 big moments)",
     "effects": {"player_name_fr": "optional new name (e.g. Monsieur Madeleine)", "item_fr": "optional item gained", "move_to": {"town": "id", "spot": "id"}}}
  ]
}"""

INSTRUCTIONS = """You are the game writer for a small top-down RPG (Pokémon-style) adaptation of Les Misérables. The complete French text is above; each chapter starts with 【tome.livre.chapitre】.

The player IS Jean Valjean. Cover his story from his arrival in Digne (October 1815) to the night he takes Cosette away from Montfermeil, in exactly three towns:
  1. digne — arrival, rejection from the inns, the bishop Myriel, the silver, the gendarmes, the candlesticks, Petit-Gervais.
  2. montreuil — years later as Monsieur Madeleine: the factory, the mayor, Fauchelevent under the cart, Javert, Fantine.
  3. montfermeil — Christmas night 1823: the Thénardier inn, Cosette fetching water in the woods, the doll, leaving with Cosette.
Between towns the player walks an overworld road; use effects.move_to to send them on when a town's story is done.

Output ONE JSON object in this format:
""" + FORMAT + """

Rules:
1. Every `text_fr` is copied VERBATIM from the cited chapter: a contiguous run of 6-45 words, original punctuation and spelling. Prefer spoken dialogue (the words inside the quotation marks/dashes) when the speaker is a character; use "narrateur" for narration. Never paraphrase or merge. A program checks every line.
2. 16-24 beats in story order; 2-5 lines each. The first beat of each town has trigger "start" or "reach". Every trigger target must exist (character present in that beat's npcs, building in that town, or spot in that town).
3. Each town: 4-8 buildings, 6-12 spots. Spots are named places the map designer will position (doors, a bench, the fountain, the woods' spring, the cart).
4. 8-12 characters, including valjean. Colours must make characters distinguishable from a high camera (Javert dark with a hat, Fantine pale, Cosette tiny and ragged...).
5. objective_fr/en tells the player what to do next, in game voice, short.
Return only the JSON object."""


ALICE_FORMAT_NOTE = """
Field meanings for this book (the field names are historical — follow these meanings exactly):
  - text_fr  = the line copied VERBATIM in the book's ORIGINAL ENGLISH;   text_en = a faithful FRENCH translation of it.
  - name_fr  = the character/place/building name in ENGLISH as in the book; name_en = its usual FRENCH name.
  - objective_fr = the objective in ENGLISH; objective_en = the same in FRENCH.
  - item_fr / player_name_fr = in ENGLISH.
  - narration speaker id is "narrator" (not "narrateur"); refs are chapter numbers as strings, e.g. "7".
  - season of each town will be one of: """


def instructions():
    if not lesmis.story:  # Les Mis: the original prompt, unchanged
        return INSTRUCTIONS
    fmt = (FORMAT.replace('"valjean"', '"alice"').replace("Jean Valjean", "Alice").replace("Hugo's description", "the text and Tenniel's illustrations")
           .replace('"digne"', '"rabbit_hole"').replace('"Digne"', '"The Rabbit-Hole"').replace('["1.2.1", ...]', '["1", "2"]').replace("Hugo's text", "the text")
           .replace("(streets, square, cathedral, inns, the bishop's house, the prison, the city gate, gardens...)", "(paths, trees, the riverbank, the hall of doors, gardens, houses...)")
           .replace('"croix_de_colbas"', '"rabbit_house"').replace("L'auberge de la Croix-de-Colbas", "The White Rabbit's house")
           .replace('"bishop_door"', '"tiny_door"').replace("the door of the bishop's house", "the little door behind the curtain")
           .replace("Trouver un gîte pour la nuit", "Follow the White Rabbit").replace("narrateur", "narrator").replace('"1.2.1"', '"1"')
           .replace("(e.g. Monsieur Madeleine)", "(rarely needed)"))
    rules = (INSTRUCTIONS[INSTRUCTIONS.index("\n\nRules:"):]
             .replace('"narrateur"', '"narrator"').replace("quotation marks/dashes", "quotation marks")
             .replace("including valjean", "including alice").replace("(Javert dark with a hat, Fantine pale, Cosette tiny and ragged...)", "(" + lesmis.characters_hint + ")")
             .replace("the woods' spring, the cart", "the mushroom, the tea table, the rose-tree"))
    return lesmis.story + "\n\nOutput ONE JSON object in this format:\n" + fmt + ALICE_FORMAT_NOTE + lesmis.seasons + rules


def iter_lines(g):
    for b in g["beats"]:
        for i, l in enumerate(b["lines"]):
            yield f"{b['id']}#{i}", l


def check(g):
    fails = []
    for where, l in iter_lines(g):
        d = {"elements": [{"id": where, "quote": {"ref": l["ref"], "text_fr": l["text_fr"]}}]}
        for f in lesmis.check(d):
            if f["found"]:
                l["ref"] = f["found"]  # quote is real, chapter was off: fix locally
            else:
                fails.append(f)
    return fails


def structure_errors(g):
    errs = []
    chars = {c["id"] for c in g["characters"]}
    towns = {t["id"]: t for t in g["towns"]}
    for b in g["beats"]:
        t = towns.get(b["town"])
        if not t:
            errs.append(f"{b['id']}: unknown town {b['town']}"); continue
        spots = {s["id"] for s in t["spots"]}
        builds = {x["id"] for x in t["buildings"]}
        present = {n["character"] for n in b.get("npcs", [])}
        for n in b.get("npcs", []):
            if n["character"] not in chars: errs.append(f"{b['id']}: unknown character {n['character']}")
            if n["spot"] not in spots: errs.append(f"{b['id']}: unknown spot {n['spot']} in {t['id']}")
        tr = b["trigger"]
        if tr["type"] == "talk" and tr["target"] not in present: errs.append(f"{b['id']}: talk target {tr['target']} not in npcs")
        if tr["type"] == "enter" and tr["target"] not in builds: errs.append(f"{b['id']}: enter target {tr['target']} not a building of {t['id']}")
        if tr["type"] == "reach" and tr["target"] not in spots: errs.append(f"{b['id']}: reach target {tr['target']} not a spot of {t['id']}")
        if tr["type"] == "reach" and any(n["spot"] == tr["target"] for n in b.get("npcs", [])):
            errs.append(f"{b['id']}: a character stands on the reach target {tr['target']}; put them on a neighbouring spot")
        for l in b["lines"]:
            if l["speaker"] not in chars and l["speaker"] != lesmis.narrator: errs.append(f"{b['id']}: unknown speaker {l['speaker']}")
        mv = (b.get("effects") or {}).get("move_to")
        if mv and (mv["town"] not in towns or mv["spot"] not in {s["id"] for s in towns[mv["town"]]["spots"]}):
            errs.append(f"{b['id']}: move_to {mv} invalid")
    return errs


def parse_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def main():
    prompt = lesmis.book_text() + "\n\n" + instructions()
    t0 = time.time()
    it = client.interactions.create(model=ARGON, input=prompt, generation_config={"thinking_level": "medium", "max_output_tokens": 60000})
    u = it.usage
    print(f"round 0: {time.time() - t0:.0f}s · in {u.total_input_tokens:,} · out {u.total_output_tokens:,}", flush=True)
    (GAME / "script_raw_0.json").write_text(it.output_text)
    g = parse_json(it.output_text)
    for rnd in range(1, 4):
        fails, errs = check(g), structure_errors(g)
        n = sum(1 for _ in iter_lines(g))
        print(f"  verify: {n - len(fails)}/{n} lines verbatim · {len(errs)} structure errors", flush=True)
        if not fails and not errs:
            break
        fb = "A program checked your script. Fix ONLY these problems, keep everything else identical, return the full JSON.\n"
        fb += "\n".join(f"- line {f['where']}: not verbatim in the novel: «{f['quote']}» — find the real words and copy them exactly, or replace the line." for f in fails)
        fb += "".join(f"\n- {e}" for e in errs)
        t0 = time.time()
        it = client.interactions.create(model=ARGON, input=fb, previous_interaction_id=it.id,
                                        generation_config={"thinking_level": "medium", "max_output_tokens": 60000})
        print(f"round {rnd}: {time.time() - t0:.0f}s", flush=True)
        (GAME / f"script_raw_{rnd}.json").write_text(it.output_text)
        g = parse_json(it.output_text)
    bad = {f["where"] for f in check(g)}
    for b in g["beats"]:  # last resort: drop lines that are still not verbatim
        b["lines"] = [l for i, l in enumerate(b["lines"]) if f"{b['id']}#{i}" not in bad]
    for _, l in iter_lines(g):
        l["label"] = lesmis.ref_label(l["ref"])
    if lesmis.ui:
        g["ui"] = lesmis.ui  # title screen, end screen, quote marks, travel style for the engine
    g["narrator"] = lesmis.narrator
    (GAME / "script.json").write_text(json.dumps(g, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {(GAME / 'script.json').relative_to(ROOT)}: {len(g['characters'])} characters, {len(g['towns'])} towns, {len(g['beats'])} beats, "
          f"{sum(1 for _ in iter_lines(g))} lines ({len(bad)} dropped)")


if __name__ == "__main__":
    main()
