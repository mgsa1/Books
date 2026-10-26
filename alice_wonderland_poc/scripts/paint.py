"""Paint a diorama with Nano Banana: backdrop first, then every cut-out in parallel
(the backdrop is passed as a style reference so the set reads as one hand), then key
out the white paper so each element becomes a transparent PNG.

    .venv/bin/python -I scripts/paint.py barricade              # paint what is missing
    .venv/bin/python -I scripts/paint.py barricade --only gavroche,flag --force
"""
import argparse
import base64
import io
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from argon import ask, client  # noqa: E402
from PIL import ImageStat  # noqa: E402

PAINTER = "gemini-nano-banana-2.1"

STYLE = ("Drawn in the manner of Victor Hugo's own ink-wash drawings (1850s-60s): sepia and brown-black ink, "
         "loose wash, splatters and blots, dramatic chiaroscuro; a touch of dark red only where the subject is red.")
CUTOUT = (" A single isolated subject, entirely in frame, on a plain uniform pure white background (#FFFFFF) — not cream, not paper-textured. "
          "Nothing else: no ground plane, no cast shadow on the ground, no border, no frame, no text, no signature.")
BACKDROP = (" Full-bleed scene that fills the entire frame edge to edge on aged cream paper; no white margins, "
            "no foreground objects, no people, no text. It will sit behind cut-out figures, so keep the lower third quiet.")


def generate(prompt, aspect, ref_image=None):
    content = [{"type": "text", "text": prompt}]
    if ref_image:
        content = [{"type": "image", "data": base64.b64encode(ref_image).decode(), "mime_type": "image/jpeg"},
                   {"type": "text", "text": "Match the ink, paper tone and hand of this reference drawing. " + prompt}]
    it = client.interactions.create(model=PAINTER, input=content, response_modalities=["image"],
                                    generation_config={"image_config": {"aspect_ratio": aspect, "image_size": "1K"}})
    if not it.output_image:
        raise RuntimeError(f"no image returned: {(it.output_text or '')[:200]}")
    data = it.output_image.data
    return base64.b64decode(data) if isinstance(data, str) else data


def paper_colour(im):
    """Median of the border pixels: the painter sometimes uses cream paper instead of pure white."""
    w, h = im.size
    px = im.load()
    border = [px[x, y] for x in range(0, w, 4) for y in (0, 1, h - 2, h - 1)] + [px[x, y] for y in range(0, h, 4) for x in (0, 1, w - 2, w - 1)]
    return tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))


def cut_out(jpeg_bytes, thresh=46):
    """Flood-fill the paper from the border; small enclosed paper (between wheel spokes) stays, like real paper theatre."""
    im = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
    paper = paper_colour(im)
    pad = 6
    canvas = Image.new("RGB", (im.width + 2 * pad, im.height + 2 * pad), paper)
    canvas.paste(im, (pad, pad))
    ImageDraw.floodfill(canvas, (0, 0), (255, 0, 255), thresh=thresh)
    px = canvas.load()
    # second pass: large enclosed white pockets (sky under a flag) are background too;
    # small ones (between wheel spokes) stay as paper
    area, k, tagged = canvas.width * canvas.height, 0, {}
    for y in range(pad, canvas.height - pad, 12):
        for x in range(pad, canvas.width - pad, 12):
            r, g, b = px[x, y]
            if abs(r - paper[0]) + abs(g - paper[1]) + abs(b - paper[2]) < 24 and k < 250:
                k += 1
                tag = (1, 2, k)
                ImageDraw.floodfill(canvas, (x, y), tag, thresh=thresh // 2)
                tagged[tag] = True
    if tagged:
        counts = {c: n for n, c in canvas.getcolors(area) if c in tagged}
        big = {c for c, n in counts.items() if n > area * 0.004}
        for y in range(canvas.height):
            for x in range(canvas.width):
                if px[x, y] in tagged:
                    px[x, y] = (255, 0, 255) if px[x, y] in big else paper
    mask = Image.new("L", canvas.size, 255)
    mp = mask.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if px[x, y] == (255, 0, 255):
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))  # eat the JPEG halo, soften
    rgba = Image.new("RGBA", canvas.size)
    rgba.paste(Image.new("RGB", canvas.size, paper), (0, 0))
    rgba.paste(Image.open(io.BytesIO(jpeg_bytes)).convert("RGB"), (pad, pad))
    rgba.putalpha(mask)
    box = mask.point(lambda v: 255 if v > 8 else 0).getbbox()
    return rgba.crop(box) if box else rgba


def paper_ok(jpeg_bytes):
    """A cut-out is only keyable on plain white: bright, uniform border (no aged-paper texture or vignette)."""
    im = Image.open(io.BytesIO(jpeg_bytes)).convert("L")
    w, h = im.size
    strips = [im.crop((0, 0, w, 6)), im.crop((0, h - 6, w, h)), im.crop((0, 0, 6, h)), im.crop((w - 6, 0, w, h))]
    stats = [ImageStat.Stat(s) for s in strips]
    # a subject may touch one edge (a wall, a street); the other three must be plain, light paper
    plain = sum(st.mean[0] > 228 and st.stddev[0] < 9 for st in stats)
    return plain >= 3, f"{plain}/4 plain border strips, means {[round(st.mean[0]) for st in stats]}"


def soften(prompt, error):
    """Nano Banana refused: Argon rewrites the prompt, keeping the text-grounded detail."""
    it = ask(f"An image model refused this prompt ({error[:160]}). Rewrite it so it is acceptable — no corpses, gore or "
             f"visible wounds; suggest death or danger indirectly (a dropped cap, a lantern, a covered form) — while keeping "
             f"every concrete visual detail. Return only the new prompt.\n\n{prompt}", level="low")
    return it.output_text.strip()


def paint_cutout(e, ref, log):
    """Paint -> check the paper -> retry; last try drops the reference (it pulls toward aged paper)."""
    prompt = e["image_prompt"]
    for attempt in range(3):
        use_ref = ref if attempt < 2 else None
        try:
            raw = generate(prompt + " " + STYLE + CUTOUT, e["aspect"], ref_image=use_ref)
        except Exception as ex:
            if "safety" in str(ex).lower() or "prohibited" in str(ex).lower():
                prompt = soften(prompt, str(ex))
                log(f"  ↻ {e['id']}: blocked by safety filter, Argon rewrote the prompt")
                continue
            raise
        ok, why = paper_ok(raw)
        if ok:
            return raw, prompt
        log(f"  ↻ {e['id']}: paper not keyable ({why}), repainting{' without reference' if attempt == 1 else ''}")
    return raw, prompt  # best effort


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--recut", action="store_true", help="re-run the cut-out on saved raw images, no painting")
    a = ap.parse_args()

    d = json.loads((ROOT / "world_lm" / f"{a.id}.json").read_text())
    out = ROOT / "assets_lm" / a.id
    (out / "raw").mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    only = set(filter(None, a.only.split(",")))

    if a.recut:
        for raw in sorted((out / "raw").glob("*.jpg")):
            png = cut_out(raw.read_bytes())
            png.save(out / f"{raw.stem}.png", optimize=True)
            manifest[raw.stem] = {"w": png.width, "h": png.height}
            print(f"  recut {raw.stem:<22} paper={paper_colour(Image.open(raw).convert('RGB'))} {png.size}")
        manifest_path.write_text(json.dumps(manifest, indent=1))
        return

    t0 = time.time()
    bd = out / "backdrop.jpg"
    if (not bd.exists() or (a.force and (not only or "backdrop" in only))):
        img = generate(d["backdrop"]["image_prompt"] + " " + STYLE + BACKDROP, "21:9")
        bd.write_bytes(img)
        print(f"  backdrop  {time.time() - t0:.0f}s", flush=True)
    ref = bd.read_bytes()

    todo = [e for e in d["elements"] if (not only or e["id"] in only) and (a.force or not (out / f"{e['id']}.png").exists())]

    def paint(e):
        raw, used = paint_cutout(e, ref, lambda m: print(m, flush=True))
        if used != e["image_prompt"]:
            e["image_prompt_used"] = used
        (out / "raw" / f"{e['id']}.jpg").write_bytes(raw)
        png = cut_out(raw)
        png.save(out / f"{e['id']}.png", optimize=True)
        return e["id"], png.size

    with ThreadPoolExecutor(a.workers) as pool:
        futs = {pool.submit(paint, e): e["id"] for e in todo}
        for f in as_completed(futs):
            try:
                eid, (w, h) = f.result()
                manifest[eid] = {"w": w, "h": h}
                print(f"  {eid:<22} {w}x{h}  {time.time() - t0:.0f}s", flush=True)
            except Exception as ex:
                print(f"  ✗ {futs[f]}: {ex}", flush=True)
    for e in d["elements"]:  # fill sizes for elements painted on earlier runs
        p = out / f"{e['id']}.png"
        if p.exists() and e["id"] not in manifest:
            manifest[e["id"]] = dict(zip(("w", "h"), Image.open(p).size))
    manifest_path.write_text(json.dumps(manifest, indent=1))
    (ROOT / "world_lm" / f"{a.id}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")  # keep rewritten prompts
    print(f"done in {time.time() - t0:.0f}s → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()


GREEN = (" A single isolated subject, entirely in frame, on a perfectly flat, uniform chroma-key green background (#00B140), "
         "like a studio green screen. No ground plane, no shadow, no border, no text. Do not use green anywhere on the subject.")


def chroma_key(img_bytes):
    """Key out a green-screen background (keeps white aprons and white fur, unlike the paper flood-fill)."""
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    px = im.load()
    alpha = Image.new("L", im.size, 255)
    ap = alpha.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b = px[x, y]
            dom = g - max(r, b)  # how much greener than the other channels
            if dom > 60:
                ap[x, y] = 0
            elif dom > 20:  # soft edge + despill
                ap[x, y] = int(255 * (60 - dom) / 40)
                px[x, y] = (r, max(r, b), b)
            elif dom > 0:
                px[x, y] = (r, max(r, b), b)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA")
    out.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    return out.crop(box) if box else out


def green_ok(img_bytes):
    """Border must be mostly the green screen."""
    im = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((64, 64))
    edge = [im.getpixel((x, y)) for x in range(64) for y in (0, 63)] + [im.getpixel((x, y)) for y in range(64) for x in (0, 63)]
    green = sum(g - max(r, b) > 60 for r, g, b in edge) / len(edge)
    return green > 0.85, f"{green:.0%} of the border is green"
