#!/usr/bin/env python3
"""
Backgrounds — five families, generated, never photographed.

Rules that are not negotiable, because the phrase is the hero:
  - luminance stays inside a narrow dark band (the text must always win)
  - no accent colour, ever: the palette is the project's black and paper white
  - no faces, no objects, nothing that tells its own story
  - the centre of the frame is quieter than the edges

Each family is a mood, not a picture. Deterministic from a seed, so any
background can be regenerated exactly.
"""

import argparse
import math
import pathlib

import numpy as np
from PIL import Image, ImageFilter

W, H = 1080, 1920
FAMILIES = ["dusk", "paper", "concrete", "silver", "fog"]


# ------------------------------------------------------------------ helpers

def _grid():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    return x / W, y / H


def _grain(a, rng, amount=0.012, soft=0.0):
    n = rng.normal(0, amount, a.shape).astype(np.float32)
    if soft:
        n = np.asarray(Image.fromarray((n * 255 + 128).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(soft)), np.float32) / 255 - 0.5
    return a + n


def _fbm(rng, octaves=5, base=6, gain=0.5):
    """Fractal noise: irregular at every scale, so it never lattices."""
    out = np.zeros((H, W), np.float32)
    amp, size = 1.0, base
    for _ in range(octaves):
        small = rng.random((max(2, int(size * H / W)), max(2, size))).astype(np.float32)
        layer = np.asarray(Image.fromarray((small * 255).astype(np.uint8))
                           .resize((W, H), Image.BICUBIC), np.float32) / 255
        out += amp * layer
        amp *= gain
        size *= 2
    return out / out.max()


def _centre_hush(a, strength=0.5):
    """Quiet the middle of the frame so the words sit on calm ground."""
    x, y = _grid()
    d = np.sqrt(((x - .5) / .62) ** 2 + ((y - .44) / .46) ** 2)
    mask = np.clip(d, 0, 1) ** 1.6
    mean = float(a.mean())
    return a * (1 - strength * (1 - mask)) + mean * strength * (1 - mask) * 0.55


def _finish(a, lo=0.018, hi=0.165):
    """Compress into the dark band and return an image."""
    a = (a - a.min()) / max(float(a.max() - a.min()), 1e-6)
    a = lo + a * (hi - lo)
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGB")


# ----------------------------------------------------------------- families

def dusk(rng):
    """Granular twilight gradient — the default, the quietest."""
    x, y = _grid()
    a = (1 - y) * 0.55 + 0.2 + 0.22 * _fbm(rng, octaves=4, base=3)
    cx, cy = rng.uniform(.35, .65), rng.uniform(.25, .45)
    a += 0.45 * np.exp(-(((x - cx) ** 2) / 0.10 + ((y - cy) ** 2) / 0.07))
    a = _grain(a, rng, 0.035, soft=1.2)
    a = _grain(a, rng, 0.010)
    return a


def paper(rng):
    """Paper and ink — fibre, bleed, the residue of a hand."""
    x, y = _grid()
    a = 0.34 + 0.42 * _fbm(rng, octaves=6, base=4)
    # laid lines, the faint ribbing of handmade paper — irregular amplitude
    ribs = np.sin(2 * np.pi * x * rng.uniform(9, 14) + rng.uniform(0, 6))
    a += 0.010 * ribs * (0.4 + 0.6 * _fbm(rng, octaves=3, base=3))
    # ink bleed: a few soft washes, never a shape you could name
    for _ in range(rng.integers(2, 4)):
        bx, by = rng.uniform(.1, .9), rng.uniform(.1, .9)
        r = rng.uniform(.10, .26)
        a -= 0.30 * np.exp(-(((x - bx) ** 2 + (y - by) ** 2) / (r ** 2)))
    a = _grain(a, rng, 0.045, soft=2.0)
    return a


def concrete(rng):
    """Blurred architecture — light falling across a wall, out of focus."""
    x, y = _grid()
    ang = rng.uniform(-0.35, 0.35)
    u = x * math.cos(ang) + y * math.sin(ang)
    a = np.full((H, W), 0.45, np.float32)
    for _ in range(rng.integers(3, 6)):          # slabs of light
        c, w_ = rng.uniform(0, 1), rng.uniform(.05, .18)
        a += rng.uniform(.12, .32) * np.exp(-((u - c) ** 2) / (w_ ** 2))
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(34)), np.float32) / 255
    a = _grain(a, rng, 0.020, soft=1.0)
    return a


def silver(rng):
    """Film landscape — a horizon, and nothing else identifiable."""
    x, y = _grid()
    hz = rng.uniform(.55, .74)
    sky = np.clip((hz - y) / hz, 0, 1) ** 1.4
    land = np.clip((y - hz) / (1 - hz), 0, 1)
    a = 0.30 + 0.55 * sky - 0.22 * land + 0.10 * _fbm(rng, octaves=4, base=5)
    # a low ridge, softened past recognition
    ridge = 0.012 * np.sin(2 * np.pi * (x * rng.uniform(1.2, 2.6) + rng.uniform(0, 1)))
    a -= 0.5 * np.clip((y - (hz + ridge)) * 40, 0, 1) * 0.06
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    a = _grain(a, rng, 0.042, soft=0.7)          # silver halide
    return a


def fog(rng):
    """Minimal dark mist — the emptiest of the five."""
    x, y = _grid()
    a = np.full((H, W), 0.42, np.float32)
    for _ in range(rng.integers(3, 6)):
        cy_ = rng.uniform(.1, .9)
        band = np.exp(-((y - cy_) ** 2) / (rng.uniform(.02, .09) ** 2))
        drift = 1 + 0.25 * np.sin(2 * np.pi * (x * rng.uniform(.6, 1.8) + rng.uniform(0, 1)))
        a += rng.uniform(.10, .24) * band * drift
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(48)), np.float32) / 255
    a = _grain(a, rng, 0.016, soft=1.4)
    return a


BUILD = {"dusk": dusk, "paper": paper, "concrete": concrete, "silver": silver, "fog": fog}


def make(family, seed):
    rng = np.random.default_rng(seed)
    a = BUILD[family](rng)
    a = _centre_hush(a)
    return _finish(a)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="backgrounds")
    p.add_argument("--seeds", type=int, default=1, help="variants per family")
    a = p.parse_args()

    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for fam in FAMILIES:
        for s in range(a.seeds):
            img = make(fam, 1855 + s * 101)
            img.save(out / f"{fam}-{s}.png")
            arr = np.asarray(img.convert("L"), np.float32)
            print(f"{fam}-{s}  luminance {arr.min():5.1f}–{arr.max():5.1f}  mean {arr.mean():5.1f}")
