"""Build per-site image assets from GBP gallery photos.

usage: python3 scripts/make_images.py <domain> <incoming_dir>
  incoming_dir holds logo.png and g0.jpg..gN.jpg
  reads data/image_map/<domain>.json: {"hero": "g6.jpg", "gallery": ["g6.jpg", ...], "products": {"slug": "g7.jpg", ...}}
  writes assets/<domain>/img/{logo.png, og.jpg, gallery/*.jpg, products/<slug>.jpg}
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
domain, inc = sys.argv[1], Path(sys.argv[2])
m = json.loads((ROOT / "data" / "image_map" / f"{domain}.json").read_text())
out = ROOT / "assets" / domain / "img"
(out / "gallery").mkdir(parents=True, exist_ok=True)
(out / "products").mkdir(parents=True, exist_ok=True)

logo = Image.open(inc / "logo.png").convert("RGBA")
# trim transparent/white margins of the logo
bbox = Image.eval(logo.split()[3], lambda a: 255 if a > 10 else 0).getbbox() or logo.getbbox()
logo = logo.crop(bbox)
if logo.split()[3].getextrema()[0] > 200:  # no transparency (e.g. GBP avatar JPEG): trim the white margins too
    from PIL import ImageChops
    rgb = logo.convert("RGB")
    diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 25 else 0)
    bb = diff.getbbox()
    if bb:
        pad = max(8, logo.width // 60)
        logo = logo.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(logo.width, bb[2] + pad), min(logo.height, bb[3] + pad)))
logo.save(out / "logo.png")


def square(im, size):
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    return im.resize((size, size), Image.LANCZOS)


def badge(im):
    """White rounded card with the logo in the bottom-right corner."""
    im = im.convert("RGBA")
    W = im.width
    bw = int(W * 0.34)
    lg = logo.copy()
    lg.thumbnail((bw - 24, int(bw * 0.5)))
    pad = 12
    cw, ch = lg.width + pad * 2, lg.height + pad * 2
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=14, fill=(255, 255, 255, 235))
    card.alpha_composite(lg, (pad, pad))
    im.alpha_composite(card, (W - cw - 16, im.height - ch - 16))
    return im.convert("RGB")


for slug, fn in m["products"].items():
    im = square(Image.open(inc / fn), 500)
    badge(im).save(out / "products" / f"{slug}.jpg", quality=82, optimize=True)

for fn in m["gallery"]:
    im = Image.open(inc / fn).convert("RGB")
    im.thumbnail((1200, 1200))
    im.save(out / "gallery" / fn, quality=80, optimize=True)

hero = Image.open(inc / m["hero"]).convert("RGB")
hero.thumbnail((1400, 1400))
hero.save(out / "gallery" / "g0.jpg", quality=80, optimize=True)
# OG image 1200x630 from the hero with badge
og = hero.copy()
w, h = og.size
tw, th = 1200, 630
scale = max(tw / w, th / h)
og = og.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
og = og.crop(((og.width - tw) // 2, (og.height - th) // 2, (og.width - tw) // 2 + tw, (og.height - th) // 2 + th))
badge(og).save(out / "og.jpg", quality=82, optimize=True)
print("wrote", out, "products", len(m["products"]), "gallery", len(m["gallery"]) + 1)
