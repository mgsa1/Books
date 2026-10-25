"""Step [1] of the pipeline: EPUB -> builds/<slug>/book.json + book.txt

Usage: uv run pipeline/ingest.py ressources/alice_in_wonderland.epub

book.json: title, author, source, rights, sha256, chapters[{id, title, paragraphs[{id, text}]}]
book.txt:  the same text with one "[c01.p0042]" marker per paragraph, for the Argon prompt.
Paragraph ids are stable for a given input hash. Standard library only.
"""
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config as C  # noqa: E402

NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
HEADINGS = {"h1", "h2", "h3"}
BLOCKS = HEADINGS | {"p"}
BOILERPLATE_RE = re.compile(r"pg-boilerplate|pgheader|pg-footer|pg-header")
CHAPTER_RE = re.compile(r"^\s*(chapter|book|part|volume)\b", re.I)


class Blocks(HTMLParser):
    """Collect (tag, text) for headings and paragraphs, skipping boilerplate containers."""

    def __init__(self):
        super().__init__()
        self.blocks, self._tag, self._buf, self._skip = [], None, [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if BOILERPLATE_RE.search(f"{a.get('class', '')} {a.get('id', '')}"):
            self._skip += 1
        if self._skip:
            return
        if tag in BLOCKS and self._tag is None:
            self._tag, self._buf = tag, []
        elif tag == "br" and self._tag:
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if self._skip and tag in ("header", "footer", "div", "section"):
            self._skip -= 1
            return
        if tag == self._tag:
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.blocks.append((tag, text))
            self._tag = None

    def handle_data(self, data):
        if self._tag and not self._skip:
            self._buf.append(data)


def read_epub(path: Path):
    z = zipfile.ZipFile(path)
    container = ET.fromstring(z.read("META-INF/container.xml"))
    opf_path = container.find(".//c:rootfile", NS).get("full-path")
    opf = ET.fromstring(z.read(opf_path))
    base = posixpath.dirname(opf_path)
    meta = {k: (opf.findtext(f".//dc:{k}", default="", namespaces=NS) or "").strip()
            for k in ("title", "creator", "source", "rights")}
    hrefs = {i.get("id"): i.get("href") for i in opf.findall(".//opf:manifest/opf:item", NS)}
    docs = []
    for ref in opf.findall(".//opf:spine/opf:itemref", NS):
        href = hrefs.get(ref.get("idref"))
        if href and href.endswith((".xhtml", ".html", ".htm")):
            docs.append(z.read(posixpath.join(base, href) if base else href).decode("utf-8", "ignore"))
    return meta, docs


def chapters_from_docs(docs):
    chapters = []
    for doc in docs:
        p = Blocks()
        p.feed(doc)
        for tag, text in p.blocks:
            if tag in HEADINGS:
                if CHAPTER_RE.match(text) or (chapters and not chapters[-1]["paragraphs"]):
                    if chapters and not chapters[-1]["paragraphs"]:
                        chapters[-1]["title"] += " " + text  # heading split over two tags
                    else:
                        chapters.append({"title": text, "paragraphs": []})
                continue
            if chapters and not re.fullmatch(r"(THE END\.?|\*+)", text, re.I):
                chapters[-1]["paragraphs"].append(text)
    out = []
    for n, ch in enumerate(c for c in chapters if c["paragraphs"]):
        cid = f"c{n + 1:02d}"
        out.append({
            "id": cid,
            "title": re.sub(r"\s+", " ", ch["title"]).strip(),
            "paragraphs": [{"id": f"{cid}.p{i + 1:04d}", "text": t} for i, t in enumerate(ch["paragraphs"])],
        })
    return out


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def ingest(path: Path, out_dir: Path | None = None):
    meta, docs = read_epub(path)
    chapters = chapters_from_docs(docs)
    slug = slugify(meta["title"] or path.stem)
    out_dir = out_dir or C.BUILDS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    book = {
        "slug": slug,
        "title": meta["title"],
        "author": meta["creator"],
        "source": meta["source"],
        "rights": meta["rights"],
        "input_file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "chapters": chapters,
    }
    (out_dir / "book.json").write_text(json.dumps(book, ensure_ascii=False, indent=1))
    lines = [f"# {book['title']} — {book['author']}", ""]
    for ch in chapters:
        lines += [f"## {ch['id']} {ch['title']}", ""]
        lines += [f"[{p['id']}] {p['text']}" for p in ch["paragraphs"]] + [""]
    (out_dir / "book.txt").write_text("\n".join(lines))
    return book, out_dir


if __name__ == "__main__":
    book, out = ingest(Path(sys.argv[1]))
    n_par = sum(len(c["paragraphs"]) for c in book["chapters"])
    n_words = sum(len(p["text"].split()) for c in book["chapters"] for p in c["paragraphs"])
    print(f"{book['title']} by {book['author']} -> {out}")
    print(f"{len(book['chapters'])} chapters, {n_par} paragraphs, {n_words} words, sha256 {book['sha256'][:12]}")
    for c in book["chapters"]:
        print(f"  {c['id']} {len(c['paragraphs']):3d}p  {c['title']}")
