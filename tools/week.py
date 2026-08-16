#!/usr/bin/env python3
"""
The Sunday batch. One command turns a week of rounds into files ready to post.

    python3 tools/week.py --from 1 --to 7

For each round it:
  1. seals the answer          (sha256 committed, salt kept private)
  2. renders the Reel          (12 s, the seal burned into the pixels)
  3. renders the reveal card   (for the 17:55 story, next day)
  4. renders the OG image      (what a shared link looks like)
  5. writes the caption        (ready to paste)
  6. pushes the round to the API, unpublished

Then it re-encodes one Reel at Instagram-like bitrate and reports whether the
seal is still legible after their compression. Ours is not the last one.

Nothing is published. Publishing stays a deliberate act.
"""

import argparse
import csv
import json
import pathlib
import subprocess
import sys
import datetime

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "design"))
sys.path.insert(0, str(HERE))


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, **kw)


CAPTION = """N°{no:03d}. One of these minds wrote this line — a human, or a machine.

Vote in the comments: HUMAN or AI.
Reveal tomorrow, 17:55.

The answer was sealed before you saw the line. The proof is in the video:
{short}
Check it yourself at humanor.co/proof

Humain ou IA ? Vote en commentaire.

#humanorai #words #ai #poetry #writing"""

REVEAL_TEXT = """N°{no:03d} was {label}.
{source}
{fool}
salt {salt}
Verify: humanor.co/proof"""


def main(a):
    from studio import reel_frame, reveal_card, og_card, load_rounds
    from backgrounds import make as make_bg, FAMILIES
    import reel as reelmod

    out = ROOT / "out" / "week"
    out.mkdir(parents=True, exist_ok=True)

    rows = [r for r in csv.DictReader(open(ROOT / "data" / "rounds.csv"))
            if a.start <= int(r["day"]) <= a.end]
    if not rows:
        sys.exit("no rounds in that range")

    start_date = datetime.date.fromisoformat(a.date)
    manifest = []

    for i, r in enumerate(rows):
        no, label, text = int(r["day"]), r["label"], r["text"]
        day = start_date + datetime.timedelta(days=i)

        # 1. seal — refuses to overwrite an existing seal, by design
        res = sh(f'cd "{ROOT}" && python3 proof/seal.py seal --round {no:03d} --label {label}')
        if "already sealed" in res.stdout + res.stderr:
            seals = json.load(open(ROOT / "proof" / "private" / "seals.json"))
            sha = seals[f"{no:03d}"]["sha256"]
            print(f"N°{no:03d}  already sealed, reusing")
        else:
            sha = [l.split(":")[1].strip() for l in res.stdout.splitlines()
                   if l.startswith("sha256")][0]

        fam = FAMILIES[(no * 3) % len(FAMILIES)]
        bg = make_bg(fam, 1855 + no * 37)
        rd = {"no": no, "text": text, "label": label, "sha256": sha,
              "source": ", ".join(x for x in [r.get("author"), r.get("work"), r.get("year")] if x) or None}

        # 2-4. the plates
        if not a.no_video:
            reelmod.render(text, no, fam, 1855 + no * 37, out / f"{no:03d}-reel.mp4", sha256=sha)
        reveal_card(bg, rd).save(out / f"{no:03d}-reveal.png")
        og_card(bg, text, no).save(out / f"{no:03d}-og.png")

        # 5. the caption
        short = sha[:12] + "…" + sha[-6:]
        (out / f"{no:03d}-caption.txt").write_text(CAPTION.format(no=no, short=short))

        # 6. register with the API, unpublished
        if a.api:
            body = json.dumps({"no": no, "date": day.isoformat(), "text": text, "sha256": sha})
            sh(f"""curl -s -X POST {a.api}/api/admin/round -H "x-humanor-key: $HUMANOR_KEY" """
               f"""-H 'content-type: application/json' -d '{body}'""")

        manifest.append({"no": no, "date": day.isoformat(), "family": fam,
                         "label": label, "sha256": sha})
        print(f"N°{no:03d}  {day}  {fam:9s}  {label:5s}  {short}")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # the check that matters: does the seal survive Instagram's re-encode?
    if not a.no_video:
        first = out / f"{rows[0]['day'].zfill(3)}-reel.mp4"
        if first.exists():
            proof_check(first, out)

    print(f"\n{len(rows)} rounds -> {out}")
    print("Nothing is published. Schedule the Reels in Business Suite by hand.")


def proof_check(path, out):
    """Instagram re-encodes on upload. Ours is not the last compression, so
    verify the seal is still there after a second, harsher pass."""
    sim = out / "_ig-simulation.mp4"
    sh(f'ffmpeg -y -loglevel error -i "{path}" -c:v libx264 -b:v 3500k '
       f'-maxrate 3500k -bufsize 7000k -vf scale=720:1280 -c:a aac -b:a 128k "{sim}"')
    crop = out / "_seal-after-ig.png"
    sh(f'ffmpeg -y -loglevel error -i "{sim}" -vf "crop=720:150:0:1000,scale=1440:300" '
       f'-frames:v 1 "{crop}"')
    print(f"\nInstagram-like re-encode written to {sim.name}")
    print(f"Open {crop.name} — if the hash is not readable there, it will not be readable on a phone.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="start", type=int, required=True)
    p.add_argument("--to", dest="end", type=int, required=True)
    p.add_argument("--date", default=str(datetime.date.today()), help="date of the first drop")
    p.add_argument("--api", default="", help="e.g. https://humanor-api.humanor-ai.workers.dev")
    p.add_argument("--no-video", action="store_true", help="stills only, fast")
    main(p.parse_args())
