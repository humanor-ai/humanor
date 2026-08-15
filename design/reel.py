#!/usr/bin/env python3
"""
Reel renderer v2 — the picture is alive, the words are not.

What changed and why:

  7 s -> 12 s   A non-native reader needs to read the line twice, and a drone
                needs room to become something. 12 s still loops well.

  living grain  The old grain was baked into the background, identical on every
                frame. That is what made it read as a photograph. Grain that is
                regenerated per frame is the single difference between a still
                and film. Nothing moves, and yet it breathes.

  travelling    A soft light crosses the frame once per loop, like a window in
  light         a room the camera is standing in.

  drift         Background layers pan slightly against the zoom, so the image
                has depth rather than a flat push-in.

The phrase never moves, never fades, and is on screen 100% of the duration.
Everything alive is behind it.
"""

import math
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from backgrounds import make as make_bg, FAMILIES
from studio import reel_frame, W, H

FPS = 24
SECONDS = 12


def text_layer(text, no):
    """Render the type once, as a transparent plate, then reuse it 288 times."""
    plate = reel_frame(Image.new("RGB", (W, H), (0, 0, 0)), text, no)
    a = np.asarray(plate, np.float32)
    alpha = a.max(axis=2) / 255.0
    return a, alpha[..., None]


def travelling_light(t01):
    """One soft pass across the frame per loop. Returns a (H,W,1) multiplier."""
    x = np.linspace(0, 1, W, dtype=np.float32)[None, :]
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    cx = -0.35 + 1.7 * t01                       # off-frame to off-frame
    beam = np.exp(-((x - cx) ** 2) / 0.105) * (0.65 + 0.35 * np.cos((y - 0.45) * 2.2))
    return (1.0 + 0.55 * beam)[..., None]


def render(text, no, family, seed, out_path, seconds=SECONDS, fps=FPS):
    n = seconds * fps
    bg = make_bg(family, seed)
    big = np.asarray(bg.resize((int(W * 1.14), int(H * 1.14)), Image.LANCZOS), np.float32)
    BH, BW = big.shape[:2]

    txt, alpha = text_layer(text, no)
    rng = np.random.default_rng(seed)

    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            p = i / n
            # cosine ease so frame 0 and frame n-1 meet exactly: a true loop
            ease = 0.5 - 0.5 * math.cos(2 * math.pi * p)

            z = 1.0 + 0.055 * ease
            cw, ch = int(W * z), int(H * z)
            # drift: the crop wanders as it zooms, so the image has depth
            dx = int(math.sin(2 * math.pi * p) * (BW - cw) * 0.22)
            dy = int(math.cos(2 * math.pi * p) * (BH - ch) * 0.16)
            x0 = np.clip((BW - cw) // 2 + dx, 0, BW - cw)
            y0 = np.clip((BH - ch) // 2 + dy, 0, BH - ch)

            crop = big[y0:y0 + ch, x0:x0 + cw]
            frame = np.asarray(
                Image.fromarray(crop.astype(np.uint8)).resize((W, H), Image.BILINEAR),
                np.float32)

            frame *= travelling_light(p)

            # living grain — new every frame, at two scales
            coarse = rng.normal(0, 4.0, (H // 4, W // 4)).astype(np.float32)
            coarse = np.asarray(Image.fromarray((coarse + 128).astype(np.uint8))
                                .resize((W, H), Image.BILINEAR), np.float32) - 128
            fine = rng.normal(0, 3.2, (H, W)).astype(np.float32)
            frame += (coarse + fine)[..., None]

            # the words sit on top, untouched by any of it
            frame = frame * (1 - alpha) + txt * alpha

            Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8)).save(f"{tmp}/{i:04d}.png")

        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
            "-i", f"{tmp}/%04d.png",
            "-c:v", "libx264", "-preset", "medium", "-tune", "grain", "-crf", "23",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_path)
        ], check=True)


if __name__ == "__main__":
    import csv, argparse
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", default="../data/rounds.csv")
    p.add_argument("--out", default="../out/reel")
    p.add_argument("--only", type=int, default=0, help="render only round N")
    p.add_argument("--count", type=int, default=1)
    a = p.parse_args()

    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(a.rounds)))
    if a.only:
        rows = [r for r in rows if int(r["day"]) == a.only]
    else:
        rows = rows[:a.count]

    for r in rows:
        no = int(r["day"])
        fam = FAMILIES[(no * 3) % len(FAMILIES)]
        render(r["text"], no, fam, 1855 + no * 37, out / f"{no:03d}-v2.mp4")
        print(f"N°{no:03d}  {fam}  {SECONDS}s  -> {no:03d}-v2.mp4")
