"""Generate neutral, brand-safe placeholder images for a site that has no GBP photos yet.

usage: python3 scripts/make_placeholder_images.py <domain>
writes assets/<domain>/img/{og.jpg, gallery/g0.jpg, products/<slug>.jpg} in the site's own palette.
No logo.png is written, so build.py falls back to the inline SVG shield mark.
Replace with real photos via make_images.py once the GBP gallery is available.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build import PALETTES, PRODUCTS  # noqa: E402

domain = sys.argv[1]
loc = next(l for l in json.loads((ROOT / "data" / "locations.json").read_text()) if l["domain"] == domain)
ink, signal, signal_ink, paper = PALETTES[loc.get("palette", 0) % len(PALETTES)]
out = ROOT / "assets" / domain / "img"
(out / "gallery").mkdir(parents=True, exist_ok=True)
(out / "products").mkdir(parents=True, exist_ok=True)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def key_mark(d, cx, cy, s, color):
    """Simple key glyph: ring + shaft + two teeth."""
    w = max(2, s // 9)
    d.ellipse((cx - s * .5, cy - s * .5, cx, cy), outline=color, width=w)
    d.line((cx, cy - s * .25, cx + s * .9, cy - s * .25), fill=color, width=w)
    d.line((cx + s * .55, cy - s * .25, cx + s * .55, cy + s * .05), fill=color, width=w)
    d.line((cx + s * .8, cy - s * .25, cx + s * .8, cy + s * .12), fill=color, width=w)


def stripes(im, color, alpha=18):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    W, H = im.size
    for x in range(-H, W, 56):
        d.line((x, H, x + H, 0), fill=color + (alpha,), width=18)
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def card(size, title, sub, big=True):
    W, H = size
    im = Image.new("RGB", size, hexrgb(ink))
    im = stripes(im, hexrgb(signal))
    d = ImageDraw.Draw(im)
    pad = int(min(W, H) * .08)
    d.rectangle((pad, pad, pad + int(W * .06), pad + int(W * .06)), fill=hexrgb(signal))
    key_mark(d, W - pad - int(W * .22), H - pad - int(W * .1), int(W * .2), hexrgb(signal))
    tf = ImageFont.truetype(BOLD, int(min(W, H) * (.11 if big else .085)))
    sf = ImageFont.truetype(REG, int(min(W, H) * .055))
    # wrap title to ~2 lines
    words, lines, cur = title.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=tf) > W - 2 * pad and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    y = int(H * .34)
    for ln in lines[:3]:
        d.text((pad, y), ln, font=tf, fill=(255, 255, 255)); y += tf.size + 6
    d.text((pad, y + 10), sub, font=sf, fill=hexrgb(signal))
    return im


biz, city = loc["business"], f'{loc["city"]}, {loc["st"]}'
card((1200, 630), biz, f"24-hour locksmith · {city} · {loc['phone']}").save(out / "og.jpg", quality=85, optimize=True)
card((1400, 1050), biz, f"Mobile locksmith · {city}").save(out / "gallery" / "g0.jpg", quality=82, optimize=True)
for p in PRODUCTS:
    card((500, 500), p["name"], city, big=False).save(out / "products" / p["image"], quality=82, optimize=True)
print("wrote placeholders to", out)

# favicon / schema logo: signal square with the key glyph (used by base.html as /img/logo.png)
lg = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
d = ImageDraw.Draw(lg)
d.rounded_rectangle((0, 0, 511, 511), radius=96, fill=hexrgb(ink))
key_mark(d, 120, 290, 300, hexrgb(signal))
lg.save(out / "logo.png")
