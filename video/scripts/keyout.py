"""Key the white paper out of scanned illustrations and crop to the drawing."""
import sys, os
from PIL import Image, ImageChops

src_dir, out_dir = sys.argv[1], sys.argv[2]
HI, LO = 242, 190  # above HI fully transparent, below LO fully opaque (min channel)
for name in sys.argv[3:]:
    im = Image.open(os.path.join(src_dir, name)).convert("RGB")
    r, g, b = im.split()
    minc = ImageChops.darker(ImageChops.darker(r, g), b)
    alpha = minc.point(lambda v: 255 if v <= LO else (0 if v >= HI else int(255 * (HI - v) / (HI - LO))))
    out = im.copy(); out.putalpha(alpha)
    bbox = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        pad = 10
        bbox = (max(0, bbox[0]-pad), max(0, bbox[1]-pad), min(im.width, bbox[2]+pad), min(im.height, bbox[3]+pad))
        out = out.crop(bbox)
    stem = os.path.splitext(name)[0]
    out.save(os.path.join(out_dir, stem + ".png"))
    print(stem, out.size)
