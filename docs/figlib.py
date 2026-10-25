"""Shared drawing helpers for the Storyworld figures (docs/architecture.py, docs/overview.py).

Plain SVG from explicit geometry; `finish(..., render=True)` rasterises with Playwright's Chromium.
"""
from pathlib import Path

SANS = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "Menlo, Consolas, 'DejaVu Sans Mono', monospace"
INK = "#111111"
GREY = "#5b5b5b"
LINE = "#222222"
ACC = "#1f4e79"          # generative model calls
ACC_FILL = "#e8eef6"
DOC_FILL = "#f2f2f2"
CONT_FILL = "#fafafa"

out = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(s, width_px, size):
    maxc = max(8, int(width_px / (size * 0.50)))
    words, lines, cur = s.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxc:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines


def tline(x, y, s, size=10.5, weight="normal", fill=INK, anchor="start", italic=False, family=SANS):
    parts, tsp = s.split("`"), []
    for i, p in enumerate(parts):
        if not p:
            continue
        if i % 2 == 1:
            tsp.append(f'<tspan font-family="{MONO}" font-size="{size * 0.93:.1f}">{esc(p)}</tspan>')
        else:
            tsp.append(esc(p))
    st = f'font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
    if italic:
        st += ' font-style="italic"'
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" {st}>{"".join(tsp)}</text>')


def para(x, y, text, width, size=10.0, lh=None, **kw):
    lh = lh or size * 1.33
    n = 0
    for raw in text.split("\n"):
        if raw == "":
            n += 0.45
            continue
        for ln in wrap(raw, width, size):
            tline(x, y + n * lh, ln, size, **kw)
            n += 1
    return y + n * lh


def rect(x, y, w, h, fill="#ffffff", stroke=INK, sw=1.3, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def doc(x, y, w, h, name, sub=None, size=10.3):
    f = 9
    out.append(f'<path d="M{x},{y} h{w - f} l{f},{f} v{h - f} h{-w} z" fill="{DOC_FILL}" stroke="{INK}" stroke-width="1.2"/>')
    out.append(f'<path d="M{x + w - f},{y} v{f} h{f}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    tline(x + 7, y + 15, name, size, family=MONO, weight="bold")
    if sub:
        para(x + 7, y + 28, sub, w - 12, size - 1.2, fill=GREY)


def diamond(cx, cy, rx, ry, lines, size=8.8, fill="#ffffff"):
    out.append(f'<path d="M{cx},{cy - ry} L{cx + rx},{cy} L{cx},{cy + ry} L{cx - rx},{cy} z" fill="{fill}" stroke="{INK}" stroke-width="1.3"/>')
    lh = size * 1.2
    y0 = cy - lh * (len(lines) - 1) / 2 + size * 0.35
    for i, ln in enumerate(lines):
        tline(cx, y0 + i * lh, ln, size, anchor="middle")


def arrow(pts, dashed=False, sw=1.3, color=LINE, head=True):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    da = ' stroke-dasharray="5,4"' if dashed else ""
    m = ' marker-end="url(#arr)"' if head else ""
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"{da}{m}/>')


def dot(x, y, r=2.8):
    out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{LINE}"/>')


def elabel(x, y, s, anchor="start", size=9.2, bg=True):
    if bg:
        wpx = len(s) * size * 0.5 + 6
        xx = x - 3 if anchor == "start" else (x - wpx / 2 if anchor == "middle" else x - wpx + 3)
        out.append(f'<rect x="{xx:.1f}" y="{y - size + 1:.1f}" width="{wpx:.1f}" height="{size + 3}" fill="#ffffff"/>')
    tline(x, y, s, size, fill=GREY, anchor=anchor, italic=True)


def node(x, y, w, h, title, body, kind="proc", model=None, extra=None, body_size=9.8):
    fill = ACC_FILL if kind == "model" else "#ffffff"
    stroke = ACC if kind == "model" else INK
    rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.5 if kind == "model" else 1.3)
    ty = y + 16
    tline(x + 8, ty, title, 11.5, weight="bold")
    if model:
        tline(x + 8, ty + 13, model, 9.3, fill=ACC, family=MONO)
        ty += 13
    if extra:
        tline(x + 8, ty + 12, extra, 9.0, fill=ACC, family=MONO)
        ty += 12
    if body:
        para(x + 8, ty + 15, body, w - 16, body_size)


def header(x, y, s, sub=None):
    tline(x, y, s, 14, weight="bold")
    if sub:
        tline(x, y + 15, sub, 9.8, fill=GREY)




def begin(w, h):
    out.clear()
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    out.append("""<defs>
<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#222222"/></marker>
</defs>""")
    out.append(f'<rect width="{w}" height="{h}" fill="#ffffff"/>')


def finish(stem: Path, w, h, render=False, scale=2):
    out.append("</svg>")
    svg_path = stem.with_suffix(".svg")
    svg_path.write_text("\n".join(out))
    print("wrote", svg_path)
    if not render:
        return
    from playwright.sync_api import sync_playwright

    html = f"<html><head><style>html,body{{margin:0;padding:0;background:#fff}}</style></head><body>{svg_path.read_text()}</body></html>"
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        p = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        p.set_content(html)
        p.wait_for_timeout(300)
        p.screenshot(path=str(stem.with_suffix(".png")))
        p.pdf(path=str(stem.with_suffix(".pdf")), width=f"{w}px", height=f"{h}px", print_background=True)
        b.close()
    print("wrote", stem.with_suffix(".png"), stem.with_suffix(".pdf"))
