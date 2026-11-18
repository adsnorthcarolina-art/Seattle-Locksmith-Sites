"""Social-profile graphics for fastlocksmithsseattle.com (FB cover, avatar, YouTube banner, X header).
Palette 4: charcoal #202124 + safety orange #FF7A1A (the van-decal colors). The logo PNG is the decal crop
(opaque charcoal background), so it sits on charcoal cards, not white ones.
Run from repo root: python3 scratchpad/fast_social_assets.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pathlib

A = pathlib.Path("assets/fastlocksmithsseattle.com/img")
OUT = A / "social"; OUT.mkdir(exist_ok=True)
CHAR = (32, 33, 36); CHAR2 = (46, 48, 53); ORANGE = (255, 122, 26); WHITE = (255, 255, 255); SOFT = (222, 224, 228); MUTED = (170, 174, 182)
F = "/usr/share/fonts/opentype/inter/"
def font(w, size): return ImageFont.truetype(F + f"Inter-{w}.otf", size)

PHONE = "(206) 317-4890"; SITE = "fastlocksmithsseattle.com"
TAG = "24/7 LOCKSMITH IN SEATTLE, WA"
SERV = "Car lockouts · Car keys & fobs · Home & business · Rekeying"
TRUST = "Since 2011 · Licensed & insured · Upfront pricing · Free estimate"

logo = Image.open(A / "logo.png").convert("RGB")  # 600×260, charcoal bg

def logo_card(w, pad=22, radius=26):
    lw = w - 2 * pad; lh = int(lw * logo.height / logo.width)
    card = Image.new("RGBA", (w, lh + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(card); d.rounded_rectangle([0, 0, w - 1, lh + 2 * pad - 1], radius, fill=CHAR, outline=ORANGE, width=4)
    card.paste(logo.resize((lw, lh), Image.LANCZOS), (pad, pad))
    return card

def photo_fit(path, w, h, focus=(0.5, 0.5)):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1])
    return im.crop((x, y, x + w, y + h))

def pill(d, xy, text, f, fill, fg=WHITE, padx=34, pady=14):
    x, y = xy; tw = d.textlength(text, font=f); th = f.size
    d.rounded_rectangle([x, y, x + tw + 2 * padx, y + th + 2 * pady], (th + 2 * pady) // 2, fill=fill)
    d.text((x + padx, y + pady - 2), text, font=f, fill=fg)
    return x + tw + 2 * padx, y + th + 2 * pady

def cover(w, h, photo_frac=0.56, text_scale=1.0, out="fb-cover.jpg", photo="gallery/g0.jpg", focus=(0.2, 0.5)):
    im = Image.new("RGB", (w, h), CHAR)
    pw = int(w * photo_frac)
    ph = photo_fit(A / photo, pw, h, focus)
    mask = Image.linear_gradient("L").rotate(-90, expand=True).resize((pw, h))
    mask = mask.point(lambda v: 255 if v < 150 else max(0, 255 - int((v - 150) * 255 / 105)))
    im.paste(ph, (0, 0), mask)
    d = ImageDraw.Draw(im)
    s = text_scale; x0 = max(pw - int(60 * s), int(w * 0.52))
    card = logo_card(int(440 * s)); im.paste(card, (x0, int(h * 0.09)), card)
    y = int(h * 0.09) + card.height + int(24 * s)
    d.text((x0, y), TAG, font=font("Bold", int(42 * s)), fill=WHITE); y += int(54 * s)
    d.text((x0, y), SERV, font=font("Regular", int(23 * s)), fill=SOFT); y += int(46 * s)
    _, y = pill(d, (x0, y), PHONE, font("Bold", int(40 * s)), ORANGE, fg=CHAR, padx=int(30 * s), pady=int(12 * s)); y += int(20 * s)
    d.text((x0, y), SITE, font=font("SemiBold", int(28 * s)), fill=ORANGE); y += int(40 * s)
    d.text((x0, y), TRUST, font=font("Regular", int(19 * s)), fill=MUTED)
    im.save(OUT / out, quality=92); print(out, im.size)

def avatar(size=1080, out="avatar.jpg"):
    im = Image.new("RGB", (size, size), CHAR)
    lw = int(size * 0.80); lh = int(lw * logo.height / logo.width)
    im.paste(logo.resize((lw, lh), Image.LANCZOS), ((size - lw) // 2, (size - lh) // 2 - int(size * 0.05)))
    d = ImageDraw.Draw(im)
    f = font("Bold", int(size * 0.068)); t = "24/7 · " + PHONE
    tw = d.textlength(t, font=f); d.text(((size - tw) / 2, size * 0.66), t, font=f, fill=ORANGE)
    d.ellipse([8, 8, size - 9, size - 9], outline=ORANGE, width=22)
    im.save(OUT / out, quality=94); print(out, im.size)

def yt_banner(out="yt-banner.jpg"):
    W, H = 2560, 1440; im = Image.new("RGB", (W, H), CHAR)
    ph = photo_fit(A / "gallery/g0.jpg", W, H, (0.5, 0.4)).filter(ImageFilter.GaussianBlur(6))
    im.paste(Image.blend(ph, Image.new("RGB", (W, H), CHAR), 0.74))
    sx, sy = (W - 1546) // 2, (H - 423) // 2
    band = Image.new("RGBA", (W, 423 + 120), CHAR + (235,)); im.paste(band, (0, sy - 60), band)
    card = logo_card(540, pad=20); im.paste(card, (sx + 10, sy + (423 - card.height) // 2), card)
    d = ImageDraw.Draw(im); x = sx + 10 + card.width + 50; y = sy + 60
    d.text((x, y), TAG, font=font("Bold", 54), fill=WHITE); y += 72
    d.text((x, y), SERV, font=font("Regular", 28), fill=SOFT); y += 56
    _, y2 = pill(d, (x, y), PHONE, font("Bold", 44), ORANGE, fg=CHAR, padx=30, pady=12)
    d.text((x, y2 + 18), SITE + "  ·  Since 2011 · Licensed & insured", font=font("SemiBold", 28), fill=ORANGE)
    im.save(OUT / out, quality=90); print(out, im.size)

cover(1640, 624, out="fb-cover.jpg")
cover(1500, 500, photo_frac=0.52, text_scale=0.82, out="x-header.jpg")
avatar()
yt_banner()
