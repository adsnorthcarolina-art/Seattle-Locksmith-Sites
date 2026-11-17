"""Builds a 9:16 reel (1080x1920, ~17 s) for Master Locksmith Seattle from GBP photos.
Run from repo root: python3 scratchpad/master_reel.py
Output: assets/masterlocksmithofseattle.com/img/social/reel1.mp4
"""
import subprocess, pathlib, shlex
from PIL import Image, ImageDraw, ImageFont

SRC = pathlib.Path("/home/claude/incoming/master")
A = pathlib.Path("assets/masterlocksmithofseattle.com/img")
OUT = A / "social"; OUT.mkdir(exist_ok=True)
TMP = pathlib.Path("/tmp/reel"); TMP.mkdir(exist_ok=True)
W, H = 1080, 1920
NAVY = (11, 37, 69); SKY = (27, 163, 224); WHITE = (255, 255, 255); RED = (220, 38, 38)
F = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(F + f"Inter-{w}.otf", s)
logo = Image.open(SRC / "logo.png").convert("RGBA")

SCENES = [  # (photo, headline, sub)
    ("g54.jpg", "24/7 LOCKSMITH", "Seattle, WA · Women-owned · Since 2007"),
    ("g2.jpg",  "CAR KEYS MADE ON SITE", "All makes & models · Fobs programmed"),
    ("g7.jpg",  "LOCKED OUT?", "Car · Home · Business · No damage"),
    ("g16.jpg", "SMART LOCKS", "Installed & paired to your phone"),
    ("g14.jpg", "REKEY & DEADBOLTS", "One new key for every door"),
    ("g29.jpg", "SAFE OPENING", "Home & office safes, combos reset"),
    ("g10.jpg", "CUT & PROGRAMMED", "Right from the van, while you wait"),
]
DUR = 2.2; XF = 0.4

def fit(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = (im.width - w) // 2; y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def overlay_card(headline, sub):
    """Transparent 1080x1920 overlay: dark gradient at bottom, headline, sub, logo chip at top."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for i in range(700):  # bottom gradient
        a = int(210 * (i / 700) ** 1.4); d.line([(0, H - 700 + i), (W, H - 700 + i)], fill=(5, 20, 40, a))
    # logo chip top-left
    lw = 420; lh = int(lw * logo.height / logo.width)
    chip = Image.new("RGBA", (lw + 40, lh + 32), (255, 255, 255, 235)); chip.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), (20, 16))
    ov.alpha_composite(chip, (50, 90))
    # headline
    f1 = font("ExtraBold", 92); f2 = font("Medium", 44)
    y = H - 470
    d.text((60, y), headline, font=f1, fill=WHITE)
    d.text((60, y + 120), sub, font=f2, fill=(226, 236, 246))
    # phone pill
    f3 = font("Bold", 50); t = "(206) 582-6887"; tw = d.textlength(t, font=f3)
    d.rounded_rectangle([60, y + 210, 60 + tw + 70, y + 210 + 90], 45, fill=RED)
    d.text((95, y + 226), t, font=f3, fill=WHITE)
    return ov

def outro():
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    lw = 860; lh = int(lw * logo.height / logo.width)
    card = Image.new("RGBA", (lw + 80, lh + 60), WHITE + (255,)); card.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), (40, 30))
    im.paste(card, ((W - card.width) // 2, 520), card)
    y = 520 + card.height + 90
    f1 = font("ExtraBold", 72); t = "24/7 · Seattle, WA"; d.text(((W - d.textlength(t, font=f1)) / 2, y), t, font=f1, fill=WHITE); y += 120
    f3 = font("Bold", 84); t = "(206) 582-6887"; tw = d.textlength(t, font=f3)
    d.rounded_rectangle([(W - tw) / 2 - 50, y, (W + tw) / 2 + 50, y + 130], 65, fill=RED); d.text(((W - tw) / 2, y + 22), t, font=f3, fill=WHITE); y += 190
    f2 = font("SemiBold", 48); t = "masterlocksmithofseattle.com/book"; d.text(((W - d.textlength(t, font=f2)) / 2, y), t, font=f2, fill=SKY); y += 80
    f4 = font("Regular", 38); t = "Women-owned · Since 2007 · Licensed & insured · Free estimate"; d.text(((W - d.textlength(t, font=f4)) / 2, y), t, font=f4, fill=(200, 215, 232))
    return im

clips = []
for i, (ph, hl, sub) in enumerate(SCENES):
    base = fit(Image.open(SRC / ph).convert("RGB"), W, H)
    base.save(TMP / f"p{i}.jpg", quality=92)
    overlay_card(hl, sub).save(TMP / f"o{i}.png")
    out = TMP / f"c{i}.mp4"
    frames = int(DUR * 30)
    zoom = "zoom+0.0015" if i % 2 == 0 else "if(eq(on,1),1.12,zoom-0.0015)"
    cmd = (f"ffmpeg -y -loop 1 -i {TMP}/p{i}.jpg -loop 1 -i {TMP}/o{i}.png -filter_complex "
           f"\"[0:v]scale=1300:-1,zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps=30[bg];"
           f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v]\" -map [v] -t {DUR} -r 30 -c:v libx264 -preset medium -crf 20 {out}")
    subprocess.run(cmd, shell=True, check=True, capture_output=True)
    clips.append(out)
outro().save(TMP / "outro.jpg", quality=92)
out = TMP / "outro.mp4"
subprocess.run(f"ffmpeg -y -loop 1 -i {TMP}/outro.jpg -t 3.2 -r 30 -vf format=yuv420p -c:v libx264 -crf 20 {out}", shell=True, check=True, capture_output=True)
clips.append(out)

# concat with xfade
inputs = " ".join(f"-i {c}" for c in clips)
n = len(clips); fc = ""; prev = "[0:v]"; offset = 0.0
durs = [DUR] * (n - 1) + [3.2]
for i in range(1, n):
    offset += durs[i - 1] - XF
    outl = f"[v{i}]" if i < n - 1 else "[v]"
    fc += f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.2f}{outl};"
    prev = outl
final = OUT / "reel1.mp4"
subprocess.run(f"ffmpeg -y {inputs} -filter_complex \"{fc[:-1]}\" -map [v] -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart {final}", shell=True, check=True, capture_output=True)
print(final, subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {final}", shell=True, capture_output=True, text=True).stdout.strip(), "s")
