#!/usr/bin/env python3
"""
Drones — the sound of the account.

Three constraints decided the design:

  1. It loops every 7 seconds. Any melodic phrase becomes unbearable by the
     third pass, so there is no melody, no rhythm, no arpeggio. A held tone
     doesn't loop, it lasts.
  2. No pulse means no reading tempo imposed on the viewer. They read at
     their own speed and re-read on the loop.
  3. Every partial completes a whole number of cycles in exactly 7 s, so the
     end of the file meets its start with no click. A true loop, like the
     picture.

Synthesised from scratch: original work, no licence to clear, and it becomes
a sound you own. Others reusing it on Reels is free distribution.
"""

import argparse
import pathlib
import subprocess

import numpy as np

SR = 48000
DUR = 12.0   # 12 s: room for the drone to become something


def _partial(t, freq, amp, drift_hz=0.0, drift_depth=0.0, phase=0.0):
    """One voice. Frequency snapped so it closes its cycle exactly at DUR."""
    f = round(freq * DUR) / DUR                 # integer cycles in the loop
    sig = np.sin(2 * np.pi * f * t + phase)
    if drift_hz:                                # slow beating, also loop-locked
        d = round(drift_hz * DUR) / DUR
        sig *= 1 + drift_depth * np.sin(2 * np.pi * d * t)
    return amp * sig


def deep(t):
    """Low, close, almost furniture. The safest of the three."""
    f0 = 55.0                                   # A1
    s = _partial(t, f0, 0.50, 0.143, 0.18)
    s += _partial(t, f0 * 1.5, 0.22, 0.286, 0.22, phase=1.1)   # fifth
    s += _partial(t, f0 * 2, 0.12, 0.143, 0.15, phase=2.3)
    s += _partial(t, f0 * 3.01, 0.05, 0.429, 0.30, phase=0.7)  # slight detune
    return s


def _chord(t, root, ratios, amps, phases=None):
    phases = phases or [i * 0.7 for i in range(len(ratios))]
    out = np.zeros_like(t)
    for r, a, p in zip(ratios, amps, phases):
        out += _partial(t, root * r, a, 0.143, 0.14, phase=p)
    return out


def cosmic(t):
    """Two chords, one crossing into the other. Movement is what separates
    music from texture — a single held chord is the reason a drone reads as
    noise. Here the sound leaves A minor and arrives on F, then returns."""
    p = t / DUR
    # Am (A C E) -> F (F A C): one voice moves, the others are held. The oldest
    # trick in harmony, and the only one that fits in twelve seconds.
    a = _chord(t, 110.0, [1.0, 1.2, 1.5, 2.0, 3.0, 0.5],
                        [.26, .17, .20, .13, .06, .16])
    b = _chord(t, 87.31, [1.0, 1.26, 1.5, 2.0, 3.0, 0.5],
                        [.26, .17, .20, .13, .06, .16],
                        phases=[.4, 1.1, 1.9, 2.5, .8, 3.1])
    x = (0.5 - 0.5 * np.cos(2 * np.pi * p)) ** 1.3     # there and back
    return a * (1 - x) + b * x


def bowed(t):
    """Closest to a held cello. Warmest, most human of the three —
    which is its own small joke on an account about telling them apart."""
    f0 = 73.42                                  # D2
    s = np.zeros_like(t)
    for n, amp in ((1, .42), (2, .24), (3, .15), (4, .08), (5, .05), (6, .03), (7, .02)):
        s += _partial(t, f0 * n, amp, 0.143 * (1 + n * .1), .12, phase=n * 0.7)
    # bow noise: filtered, and looped by construction
    rng = np.random.default_rng(1855)
    n = rng.normal(0, 1, len(t))
    k = np.hanning(1200); k /= k.sum()
    s += 0.02 * np.convolve(np.concatenate([n, n[:1200]]), k, mode="same")[:len(t)]
    return s


VOICES = {"deep": deep, "cosmic": cosmic, "bowed": bowed}


def render(name, out):
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    s = VOICES[name](t)

    # An arc, not a pulse: enter quiet, swell, hold, settle exactly back to the
    # starting value so the loop closes without a seam.
    p = t / DUR
    swell = (0.5 - 0.5 * np.cos(2 * np.pi * p)) ** 0.75        # main arc
    hold = 0.16 * (0.5 - 0.5 * np.cos(4 * np.pi * p))          # a second, smaller lift
    s *= 0.55 + 0.38 * swell + hold

    # the high partials open later than the low ones — the sound widens as it rises
    if name != "deep":
        bright = 0.35 + 0.65 * swell
        s = s * (0.65 + 0.35 * bright)

    s /= np.max(np.abs(s)) + 1e-9
    s *= 0.72                                    # headroom; IG normalises anyway

    raw = out.with_suffix(".raw")
    (s.astype(np.float32)).tofile(raw)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
        "-c:a", "aac", "-b:a", "192k", str(out)
    ], check=True)
    raw.unlink()

    # prove the loop: first and last sample must nearly meet
    print(f"{name:7s}  seam {abs(s[0] - s[-1]):.5f}  peak {np.max(np.abs(s)):.2f}  -> {out.name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../out/audio")
    a = p.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for name in VOICES:
        render(name, out / f"{name}.m4a")
