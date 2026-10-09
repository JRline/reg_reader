#!/usr/bin/env python3
"""Generates the home-screen icons (app/pwa/icon-*.png): a dark-blue rounded square with 規.
Needs Pillow and a CJK font (IPAGothic here). Run once; the PNGs are committed."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
OUT = Path(__file__).parent.parent / "app" / "pwa"
FONT = next(p for p in ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf") if Path(p).exists())
BG, FG = (29, 78, 160), (255, 255, 255)
for size, name, radius in ((180, "icon-180.png", 0), (192, "icon-192.png", 0), (512, "icon-512.png", 0), (512, "icon-maskable-512.png", 0)):
    # iOS rounds the corners itself and adds no transparency, so the icons are full-bleed squares.
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    scale = 0.52 if "maskable" in name else 0.64  # maskable icons keep the glyph inside the central safe zone
    f = ImageFont.truetype(FONT, int(size * scale))
    d.text((size / 2, size / 2), "規", font=f, fill=FG, anchor="mm")
    img.save(OUT / name)
print("icons written to", OUT)
