#!/usr/bin/env python3
"""
Studio — turns a round into the files that get posted.

Three outputs per round:
  1. the Reel   (1080x1920, ~7s loop)     the question
  2. the reveal (1080x1920 still)         the truth, next day 17:55, in story
  3. the OG     (1200x630 still)          what a shared link looks like

Invariants, from the design language:
  - the phrase never moves and is on screen 100% of the duration
  - the background breathes (3% zoom); nothing else animates
  - the answer never appears in the Reel, ever
"""

import argparse
import csv
import json
import math
import pathlib
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backgrounds import make as make_bg, FAMILIES

W, H = 1080, 1920
INK = (244, 241, 234)
DIM = (150, 147, 141)
FAINT = (95, 93, 89)
FONTS = pathlib.Path("/mnt/skills/examples/canvas-design/canvas-fonts")
SERIF = FONTS / "InstrumentSerif-Regular.ttf"
MONO = FONTS / "IBMPlexMono-Regular.ttf"
FPS, SECONDS = 24, 7


# ------------------------------------------------------------------ type set

def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit_phrase(draw, text, max_w, max_h, start=104):
    """Shrink until the phrase breathes inside the safe box. Never clipped."""
    size = start
    while size > 40:
        f = ImageFont.truetype(str(SERIF), size)
        lines = wrap(draw, text, f, max_w)
        lh = size * 1.30
        if len(lines) <= 5 and lh * len(lines) <= max_h:
            return f, lines, lh
        size -= 3
    f = ImageFont.truetype(str(SERIF), 40)
    return f, wrap(draw, text, f, max_w), 52


def centred_block(draw, lines, font, lh, cy, fill=INK):
    top = cy - (lh * len(lines)) / 2
    for i, ln in enumerate(lines):
        w_ = draw.textlength(ln, font=font)
        draw.text((W / 2 - w_ / 2, top + i * lh), ln, font=font, fill=fill)


def mono_centred(draw, text, size, y, fill, tracking=0.0):
    f = ImageFont.truetype(str(MONO), size)
    if tracking:
        total = sum(draw.textlength(c, font=f) + tracking for c in text) - tracking
        x = W / 2 - total / 2
        for c in text:
            draw.text((x, y), c, font=f, fill=fill)
            x += draw.textlength(c, font=f) + tracking
    else:
        draw.text((W / 2 - draw.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


# --------------------------------------------------------------------- plates

def reel_frame(bg, text, no):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    mono_centred(d, f"N°{no:03d}", 26, 250, FAINT, tracking=11)
    f, lines, lh = fit_phrase(d, text, W - 200, 820, start=112)
    centred_block(d, lines, f, lh, H * 0.46)
    # The ask, in the project's two voices — legible at arm's length on a phone.
    # safe zone: IG chrome covers the bottom ~430px
    ask_y = H - 590
    fs = ImageFont.truetype(str(SERIF), 62)
    fm = ImageFont.truetype(str(MONO), 50)
    w_h = d.textlength("HUMAN", font=fs)
    w_a = sum(d.textlength(c, font=fm) + 14 for c in "AI") - 14
    gap = 66
    total = w_h + gap * 2 + 2 + w_a
    x = W / 2 - total / 2
    d.text((x, ask_y), "HUMAN", font=fs, fill=INK)
    rx = x + w_h + gap
    d.line([(rx, ask_y + 12), (rx, ask_y + 74)], fill=(120, 117, 112), width=2)
    x = rx + gap
    for c in "AI":
        d.text((x, ask_y + 8), c, font=fm, fill=INK)
        x += d.textlength(c, font=fm) + 14
    mono_centred(d, "vote in the comments", 24, ask_y + 108, DIM, tracking=5)
    return img


def reveal_card(bg, round_):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    mono_centred(d, f"N°{round_['no']:03d}", 26, 250, FAINT, tracking=11)

    f, lines, lh = fit_phrase(d, round_["text"], W - 220, 620, start=76)
    centred_block(d, lines, f, lh, H * 0.34, fill=DIM)

    label = round_["label"]
    if label == "HUMAN":
        lf = ImageFont.truetype(str(SERIF), 150)
        d.text((W / 2 - d.textlength("HUMAN", font=lf) / 2, H * 0.53), "HUMAN", font=lf, fill=INK)
    else:
        mono_centred(d, "AI", 132, int(H * 0.53), INK, tracking=22)

    y = int(H * 0.68)
    if round_.get("source"):
        for ln in wrap(d, round_["source"], ImageFont.truetype(str(MONO), 26), W - 260):
            mono_centred(d, ln, 26, y, DIM); y += 44
    else:
        mono_centred(d, "No human ever wrote this line.", 26, y, DIM); y += 44

    if round_.get("foolRate") is not None:
        y += 30
        mono_centred(d, f"{round_['foolRate']}% were fooled", 30, y, INK)

    mono_centred(d, "sealed before the vote · humanor.co/proof", 20, H - 520, (78, 76, 73), tracking=2)
    return img


def og_card(bg, text, no):
    img = bg.resize((1200, 1200), Image.LANCZOS).crop((0, 285, 1200, 915))
    d = ImageDraw.Draw(img)
    gw, gh = 1200, 630
    size = 76
    while size > 28:
        f = ImageFont.truetype(str(SERIF), size)
        lines = wrap(d, text, f, gw - 200)
        if len(lines) <= 3 and size * 1.3 * len(lines) <= 330:
            break
        size -= 3
    lh = size * 1.3
    top = gh / 2 - (lh * len(lines)) / 2 - 14
    for i, ln in enumerate(lines):
        d.text((gw / 2 - d.textlength(ln, font=f) / 2, top + i * lh), ln, font=f, fill=INK)
    fm = ImageFont.truetype(str(MONO), 22)
    lab = "HUMAN  or  AI ?"
    d.text((gw / 2 - d.textlength(lab, font=fm) / 2, gh - 96), lab, font=fm, fill=DIM)
    return img


# ---------------------------------------------------------------------- video

def render_reel(bg, text, no, out_path, fps=FPS, seconds=SECONDS):
    """The background breathes 3%; the words do not move. Loops seamlessly."""
    n = fps * seconds
    with tempfile.TemporaryDirectory() as tmp:
        big = bg.resize((int(W * 1.06), int(H * 1.06)), Image.LANCZOS)
        for i in range(n):
            # cosine in/out so frame 0 and frame n-1 match: a true loop
            t = 0.5 - 0.5 * math.cos(2 * math.pi * i / n)
            z = 1.0 + 0.03 * t
            cw, ch = int(W * z), int(H * z)
            fr = big.resize((cw, ch), Image.LANCZOS)
            fr = fr.crop(((cw - W) // 2, (ch - H) // 2, (cw - W) // 2 + W, (ch - H) // 2 + H))
            reel_frame(fr, text, no).save(f"{tmp}/{i:04d}.png")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
            "-i", f"{tmp}/%04d.png",
            "-c:v", "libx264", "-preset", "slow", "-crf", "17",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(out_path)
        ], check=True)


# ----------------------------------------------------------------------- main

def load_rounds(path):
    if str(path).endswith(".json"):
        return json.load(open(path))
    rows = list(csv.DictReader(open(path)))
    out = []
    for r in rows:
        out.append({
            "no": int(r["day"]), "text": r["text"], "label": r["label"],
            "source": ", ".join(x for x in [r.get("author"), r.get("work"), r.get("year")] if x) or None,
        })
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", default="../data/rounds.csv")
    p.add_argument("--out", default="../out")
    p.add_argument("--video", type=int, default=0, help="how many reels to encode (slow)")
    a = p.parse_args()

    out = pathlib.Path(a.out)
    for sub in ("reel", "reveal", "og", "poster"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    rounds = load_rounds(a.rounds)
    for r in rounds:
        no = r["no"]
        fam = FAMILIES[(no * 3) % len(FAMILIES)]      # rotate, never repeat twice
        bg = make_bg(fam, 1855 + no * 37)

        reel_frame(bg, r["text"], no).save(out / "poster" / f"{no:03d}.png")
        og_card(bg, r["text"], no).save(out / "og" / f"{no:03d}.png")
        if r.get("label"):
            reveal_card(bg, r).save(out / "reveal" / f"{no:03d}.png")
        print(f"N°{no:03d}  {fam:9s}  {r['text'][:44]}")

    for r in rounds[:a.video]:
        no = r["no"]
        fam = FAMILIES[(no * 3) % len(FAMILIES)]
        render_reel(make_bg(fam, 1855 + no * 37), r["text"], no, out / "reel" / f"{no:03d}.mp4")
        print(f"reel N°{no:03d} encoded")
