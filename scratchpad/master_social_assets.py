"""Social-profile graphics for masterlocksmithofseattle.com (FB cover, avatar, YouTube banner, X header).
Run from repo root: python3 scratchpad/master_social_assets.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pathlib

A = pathlib.Path("assets/masterlocksmithofseattle.com/img")
OUT = A / "social"; OUT.mkdir(exist_ok=True)
NAVY = (11, 37, 69); SKY = (27, 163, 224); WHITE = (255, 255, 255); RED = (220, 38, 38)
F = "/usr/share/fonts/opentype/inter/"
def font(w, size):
    return ImageFont.truetype(F + f"Inter-{w}.otf", size)

PHONE = "(206) 582-6887"; SITE = "masterlocksmithofseattle.com"
TAG = "24/7 LOCKSMITH IN SEATTLE, WA"
SERV = "Car lockouts · Car keys & fobs · Home & business · Rekeying"
TRUST = "Women-owned · Since 2007 · Licensed & insured · Free estimate"

logo = Image.open(A / "logo.png").convert("RGBA")

def logo_card(w, pad=28, radius=26):
    """White rounded card with the logo inside, width w."""
    lw = w - 2 * pad; lh = int(lw * logo.height / logo.width)
    card = Image.new("RGBA", (w, lh + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(card); d.rounded_rectangle([0, 0, w - 1, lh + 2 * pad - 1], radius, fill=WHITE)
    card.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), (pad, pad))
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

def cover(w, h, photo_frac=0.56, text_scale=1.0, out="fb-cover.jpg", photo="gallery/g54.jpg", focus=(0.35, 0.5)):
    im = Image.new("RGB", (w, h), NAVY)
    pw = int(w * photo_frac)
    ph = photo_fit(A / photo, pw, h, focus)
    # fade the photo's right edge into navy
    mask = Image.linear_gradient("L").rotate(-90, expand=True).resize((pw, h))
    mask = mask.point(lambda v: 255 if v < 150 else max(0, 255 - int((v - 150) * 255 / 105)))
    im.paste(ph, (0, 0), mask)
    d = ImageDraw.Draw(im)
    s = text_scale; x0 = pw - int(60 * s); x0 = max(x0, int(w * 0.52))
    card = logo_card(int(470 * s)); im.paste(card, (x0, int(h * 0.09)), card)
    y = int(h * 0.09) + card.height + int(26 * s)
    d.text((x0, y), TAG, font=font("Bold", int(44 * s)), fill=WHITE); y += int(56 * s)
    d.text((x0, y), SERV, font=font("Regular", int(24 * s)), fill=(226, 236, 246)); y += int(48 * s)
    _, y = pill(d, (x0, y), PHONE, font("Bold", int(40 * s)), RED, padx=int(30 * s), pady=int(12 * s)); y += int(22 * s)
    d.text((x0, y), SITE, font=font("SemiBold", int(28 * s)), fill=WHITE); y += int(40 * s)
    d.text((x0, y), TRUST, font=font("Regular", int(20 * s)), fill=(200, 215, 232))
    im.save(OUT / out, quality=92); print(out, im.size)

def avatar(size=1080, out="avatar.jpg"):
    im = Image.new("RGB", (size, size), WHITE)
    # logo centered with margin; a thin sky ring so it reads inside a circle crop
    lw = int(size * 0.78); lh = int(lw * logo.height / logo.width)
    im.paste(logo.resize((lw, lh), Image.LANCZOS), ((size - lw) // 2, (size - lh) // 2 - int(size * 0.04)), logo.resize((lw, lh), Image.LANCZOS))
    d = ImageDraw.Draw(im)
    f = font("Bold", int(size * 0.07)); t = "24/7 · " + PHONE
    tw = d.textlength(t, font=f); d.text(((size - tw) / 2, size * 0.66), t, font=f, fill=NAVY)
    d.ellipse([8, 8, size - 9, size - 9], outline=SKY, width=22)
    im.save(OUT / out, quality=94); print(out, im.size)

def yt_banner(out="yt-banner.jpg"):
    W, H = 2560, 1440; im = Image.new("RGB", (W, H), NAVY)
    ph = photo_fit(A / "gallery/g0.jpg", W, H, (0.5, 0.4)).filter(ImageFilter.GaussianBlur(6))
    im.paste(Image.blend(ph, Image.new("RGB", (W, H), NAVY), 0.72))
    # safe area 1546×423 centred — solid navy band behind it
    sx, sy = (W - 1546) // 2, (H - 423) // 2
    band = Image.new("RGBA", (W, 423 + 120), NAVY + (235,)); im.paste(band, (0, sy - 60), band)
    card = logo_card(560, pad=24); im.paste(card, (sx + 10, sy + (423 - card.height) // 2), card)
    d = ImageDraw.Draw(im); x = sx + 10 + card.width + 50; y = sy + 60
    d.text((x, y), TAG, font=font("Bold", 54), fill=WHITE); y += 72
    d.text((x, y), SERV, font=font("Regular", 28), fill=(226, 236, 246)); y += 56
    _, y2 = pill(d, (x, y), PHONE, font("Bold", 44), RED, padx=30, pady=12)
    d.text((x, y2 + 18), SITE + "  ·  " + "Women-owned · Since 2007", font=font("SemiBold", 28), fill=WHITE)
    im.save(OUT / out, quality=90); print(out, im.size)

cover(1640, 624, out="fb-cover.jpg")
cover(1500, 500, photo_frac=0.52, text_scale=0.82, out="x-header.jpg")
avatar()
yt_banner()
