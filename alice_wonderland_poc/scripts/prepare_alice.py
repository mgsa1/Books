"""Gutenberg #11 (Alice's Adventures in Wonderland) -> data/alice/chapters.json [{ref, n, title, text}]."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
raw = (ROOT / "data/alice_raw/pg11.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
body = raw[raw.index("\n", raw.index("*** START OF")) + 1: raw.index("*** END OF")]
heads = list(re.finditer(r"^CHAPTER ([IVXL]+)\.\n(.+)$", body, re.M))  # body headings: number line, then title line
if len(heads) != 12:
    sys.exit(f"expected 12 chapters, found {len(heads)}")
chapters = []
for i, h in enumerate(heads):
    stop = heads[i + 1].start() if i + 1 < len(heads) else len(body)
    text = body[h.end():stop].strip()
    text = re.sub(r"\[Illustration\]", "", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # join hard-wrapped lines, keep paragraphs
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    chapters.append({"ref": str(i + 1), "n": i + 1, "title": h.group(2).strip(), "text": text})
out = ROOT / "data/alice"
out.mkdir(exist_ok=True)
(out / "chapters.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=1))
print(f"12 chapters, {sum(len(c['text']) for c in chapters):,} chars")
for c in chapters:
    print(f"  {c['ref']:>2} {c['title']:<32} {len(c['text']):>6}  «{c['text'][:50]}»")
