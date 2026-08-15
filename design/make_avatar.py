#!/usr/bin/env python3
"""humanor — profile mark generator.

Constraints that drove every decision:
  - Instagram crops to a CIRCLE and renders it at ~40px in a feed.
  - The mark must survive that size and still feel like an object,
    not a clipart glyph.
  - Palette is the project's, forever: #050505 ground, #F4F1EA ink.
"""

import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 1080                       # master size
BG = (5, 5, 5)
INK = (244, 241, 234)
FONTS = "/mnt/skills/examples/canvas-design/canvas-fonts"

random.seed(1855)              # Leaves of Grass


def ground(size=S):
    """Deep black with a breath of light behind the glyph — depth, not decoration."""
    img = Image.new("RGB", (size, size), BG)
    px = img.load()
    c = size / 2
    for y in range(size):
        for x in range(0, size, 2):
            d = math.hypot(x - c, y - c) / c
            lift = int(13 * max(0.0, 1.0 - d * 1.25) ** 2)
            v = 5 + lift
            px[x, y] = (v, v, v)
            if x + 1 < size:
                px[x + 1, y] = (v, v, v)
    return img.filter(ImageFilter.GaussianBlur(size / 90))


def grain(img, amount=5):
    """Film grain: the mark should feel printed, not exported."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            n = random.randint(-amount, amount)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + n)),
                        max(0, min(255, g + n)),
                        max(0, min(255, b + n)))
    return img


def draw_glyph(img, text, font_path, size_ratio, dy_ratio=0.0, ink=INK):
    """Optically centred — bounding-box centred, not baseline centred."""
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font_path, int(S * size_ratio))
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    d.text((S / 2 - (x1 + x0) / 2, S / 2 - (y1 + y0) / 2 + S * dy_ratio),
           text, font=f, fill=ink)
    return img


def variant_question():
    """A. The question mark. The whole project in one sign."""
    img = ground()
    draw_glyph(img, "?", f"{FONTS}/InstrumentSerif-Regular.ttf", 0.62)
    return grain(img)


def variant_question_ring():
    """B. The same, held by a hairline — a seal, a coin, a proof."""
    img = ground()
    d = ImageDraw.Draw(img)
    m = S * 0.085
    d.ellipse([m, m, S - m, S - m], outline=(70, 68, 65), width=max(2, int(S * 0.0035)))
    draw_glyph(img, "?", f"{FONTS}/InstrumentSerif-Regular.ttf", 0.50)
    return grain(img)


def variant_monogram():
    """C. H | AI — the two authors, the rule between them."""
    img = ground()
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(f"{FONTS}/InstrumentSerif-Regular.ttf", int(S * 0.30))

    hb = d.textbbox((0, 0), "H", font=f)
    ab = d.textbbox((0, 0), "AI", font=f)
    hw, aw = hb[2] - hb[0], ab[2] - ab[0]
    gap = S * 0.085
    total = hw + gap + aw
    left = S / 2 - total / 2
    mid = S / 2 - (hb[3] + hb[1]) / 2

    d.text((left - hb[0], mid), "H", font=f, fill=INK)
    d.text((left + hw + gap - ab[0], mid), "AI", font=f, fill=INK)

    rx = left + hw + gap / 2
    d.line([rx, S * 0.36, rx, S * 0.64], fill=(120, 117, 112), width=max(2, int(S * 0.004)))
    return grain(img)


def circle_preview(img, px):
    """What Instagram actually shows: cropped to a circle, tiny."""
    small = img.resize((px, px), Image.LANCZOS)
    mask = Image.new("L", (px * 8, px * 8), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, px * 8, px * 8], fill=255)
    mask = mask.resize((px, px), Image.LANCZOS)
    out = Image.new("RGB", (px, px), (24, 24, 24))
    out.paste(small, (0, 0), mask)
    return out


if __name__ == "__main__":
    out = "/home/claude/humanor/design"
    builds = {
        "avatar-A-question": variant_question(),
        "avatar-B-seal": variant_question_ring(),
        "avatar-C-monogram": variant_monogram(),
    }
    sheet = Image.new("RGB", (3 * 260, 260 + 120), (18, 18, 18))
    for i, (name, img) in enumerate(builds.items()):
        img.save(f"{out}/{name}.png")
        sheet.paste(circle_preview(img, 220), (i * 260 + 20, 20))
        sheet.paste(circle_preview(img, 40), (i * 260 + 110, 260))
        print("wrote", name)
    sheet.save(f"{out}/_preview-sheet.png")
    print("wrote _preview-sheet (220px and real-feed 40px)")
