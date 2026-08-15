#!/usr/bin/env python3
"""
The weekly read. Answers four questions and nothing else:

  1. Which lines fooled people?          -> what to write more of
  2. Which lines travelled?              -> what the algorithm rewards
  3. Is the sequence still unpredictable? -> the audit, on live data
  4. What did the classifier not resolve? -> the comments to read by hand

Feed it the API's /api/rounds output plus an optional insights CSV.
"""

import argparse, csv, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "tools"))
from comments import classify
from sequence import strategy_scores, autocorr


def load(path):
    return json.load(open(path))


def main(rounds_path, insights_path=None, comments_path=None):
    rounds = [r for r in load(rounds_path) if r.get("revealed")]
    if not rounds:
        print("no revealed rounds yet"); return

    print("=" * 66)
    print("FOOL RATE — the number that becomes tomorrow's caption")
    print("=" * 66)
    for r in sorted(rounds, key=lambda x: -(x.get("foolRate") or 0)):
        v = r.get("votes", {})
        n = v.get("human", 0) + v.get("ai", 0)
        fr = r.get("foolRate")
        src = (r.get("source") or "generated")[:38]
        print(f"  N°{r['no']:03d}  {r['label']:5s}  {str(fr)+'%' if fr is not None else '  —':>4}  "
              f"n={n:<5}  {src}")

    by_label = {}
    for r in rounds:
        if r.get("foolRate") is not None:
            by_label.setdefault(r["label"], []).append(r["foolRate"])
    print("\n  average fool rate:")
    for k, v in by_label.items():
        print(f"    {k:5s}  {sum(v)/len(v):.0f}%   ({len(v)} rounds)")
    if len(by_label) == 2:
        h = sum(by_label.get("HUMAN", [0])) / max(len(by_label.get("HUMAN", [1])), 1)
        a = sum(by_label.get("AI", [0])) / max(len(by_label.get("AI", [1])), 1)
        print(f"\n  -> {'AI lines fool more' if a > h else 'human lines fool more'} "
              f"by {abs(a-h):.0f} points. Write more of what fools.")

    labels = [r["label"] for r in sorted(rounds, key=lambda x: x["no"])]
    if len(labels) >= 8:
        print("\n" + "=" * 66)
        print("SEQUENCE — is it still unpredictable on live data?")
        print("=" * 66)
        for k, v in sorted(strategy_scores(labels).items(), key=lambda x: -x[1]):
            flag = "  <-- exploitable" if v > 0.62 else ""
            print(f"  {k:<14} {v:.0%}{flag}")
        print(f"  autocorr lag1 {autocorr(labels,1):+.2f}")

    if insights_path:
        print("\n" + "=" * 66)
        print("DISTRIBUTION — what travelled")
        print("=" * 66)
        rows = list(csv.DictReader(open(insights_path)))
        def num(r, *keys):
            for k in keys:
                for kk in r:
                    if k.lower() in kk.lower():
                        try: return int(float(r[kk] or 0))
                        except ValueError: pass
            return 0
        for r in rows:
            print(f"  {r.get('Post ID', r.get('ID',''))[:12]:14s} "
                  f"reach {num(r,'reach'):>7}  saves {num(r,'save'):>5}  "
                  f"shares {num(r,'share'):>5}  likes {num(r,'like'):>6}")

    if comments_path:
        print("\n" + "=" * 66)
        print("COMMENTS — classifier output")
        print("=" * 66)
        tally = {"HUMAN": 0, "AI": 0, "UNSURE": 0}
        unsure = []
        for line in open(comments_path):
            line = line.strip()
            if not line: continue
            v, c, w = classify(line)
            tally[v] += 1
            if v == "UNSURE": unsure.append(line)
        total = sum(tally.values())
        for k, v in tally.items():
            print(f"  {k:7s} {v:5d}  ({v/max(total,1):.0%})")
        print(f"\n  resolved: {(total-tally['UNSURE'])/max(total,1):.0%}")
        if unsure:
            print("\n  to read by hand:")
            for u in unsure[:15]:
                print(f"    {u[:70]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("rounds", help="JSON from /api/rounds")
    p.add_argument("--insights", help="Business Suite CSV export")
    p.add_argument("--comments", help="one comment per line")
    a = p.parse_args()
    main(a.rounds, a.insights, a.comments)
