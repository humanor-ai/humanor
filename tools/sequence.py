#!/usr/bin/env python3
"""
Label sequencing — the hardest small problem in this project.

The naive fixes are both wrong:

  - Strict alternation (H A H A) is 100% predictable after two rounds.
  - "Never more than 2 in a row" LEAKS: once a player sees two AI, they know
    round three is HUMAN. A hard cap hands out free information.

So the sequence is drawn as independent fair coin flips — the only process with
zero exploitable structure — and then *audited*. A candidate sequence is
accepted only if it passes tests for balance, run length, autocorrelation, and
conditional bias, AND if no simple player strategy beats chance on it.

This is the same principle as the rest of the project: we don't claim the
sequence is fair, we prove it.
"""

import argparse
import json
import random
from collections import Counter

H, A = "HUMAN", "AI"


# ----------------------------------------------------------------- the audits

def runs(seq):
    out, cur = [], 1
    for i in range(1, len(seq)):
        if seq[i] == seq[i - 1]:
            cur += 1
        else:
            out.append(cur); cur = 1
    out.append(cur)
    return out


def autocorr(seq, lag):
    """+1 = perfectly repeating, -1 = perfectly alternating, 0 = no structure."""
    v = [1 if s == H else -1 for s in seq]
    n = len(v) - lag
    if n <= 0:
        return 0.0
    return sum(v[i] * v[i + lag] for i in range(n)) / n


def conditional_bias(seq, k):
    """Worst-case edge available to a player who memorises the last k labels."""
    tally = {}
    for i in range(k, len(seq)):
        key = tuple(seq[i - k:i])
        t = tally.setdefault(key, Counter())
        t[seq[i]] += 1
    worst = 0.0
    for key, t in tally.items():
        n = sum(t.values())
        if n < 4:            # too few samples to be exploitable
            continue
        worst = max(worst, abs(max(t.values()) / n - 0.5))
    return worst


def strategy_scores(seq):
    """Can any simple player heuristic beat a coin flip on this sequence?"""
    n = len(seq)
    s = {
        "always HUMAN":  sum(1 for x in seq if x == H) / n,
        "always AI":     sum(1 for x in seq if x == A) / n,
        "alternate":     sum(1 for i, x in enumerate(seq) if x == (H if i % 2 == 0 else A)) / n,
        "repeat last":   sum(1 for i in range(1, n) if seq[i] == seq[i - 1]) / (n - 1),
        "oppose last":   sum(1 for i in range(1, n) if seq[i] != seq[i - 1]) / (n - 1),
    }
    return s


def audit(seq, tol_balance=0.10, max_run=4, tol_corr=0.14, tol_cond=0.26, tol_strategy=0.58):
    n = len(seq)
    bal = sum(1 for x in seq if x == H) / n
    r = runs(seq)
    checks = {
        "balance":        abs(bal - 0.5) <= tol_balance,
        "max run":        max(r) <= max_run,
        "has some runs":  max(r) >= 2,          # pure alternation would be a red flag
        "autocorr lag1":  abs(autocorr(seq, 1)) <= tol_corr,
        "autocorr lag2":  abs(autocorr(seq, 2)) <= tol_corr,
        "autocorr lag3":  abs(autocorr(seq, 3)) <= tol_corr,
        "cond bias k=1":  conditional_bias(seq, 1) <= tol_cond,
        "cond bias k=2":  conditional_bias(seq, 2) <= tol_cond,
        "no winning strategy": max(strategy_scores(seq).values()) <= tol_strategy,
    }
    return all(checks.values()), checks, bal, r


# -------------------------------------------------------------- the generator

def generate(n, seed=None, tries=20000):
    """First fair-coin sequence that survives the audit. Seed is logged."""
    base = random.randrange(2**31) if seed is None else seed
    for k in range(tries):
        rng = random.Random(base + k)
        seq = [H if rng.random() < 0.5 else A for _ in range(n)]
        ok, checks, bal, r = audit(seq)
        if ok:
            return seq, base + k, checks, bal, r
    raise RuntimeError("no sequence passed the audit — loosen tolerances")


# --------------------------------------------------------------------- report

def report(seq, seed, checks, bal, r):
    print(f"seed          : {seed}")
    print(f"length        : {len(seq)}")
    print(f"balance       : {bal:.0%} HUMAN / {1-bal:.0%} AI")
    print(f"runs          : {r}  (longest {max(r)})")
    print(f"autocorr 1/2/3: {autocorr(seq,1):+.2f} {autocorr(seq,2):+.2f} {autocorr(seq,3):+.2f}")
    print("\nplayer strategies (a fair sequence gives every one of these ~50%):")
    for k, v in sorted(strategy_scores(seq).items(), key=lambda x: -x[1]):
        print(f"  {k:<14} {v:.0%}")
    print("\naudit:")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("\nsequence:")
    print("  " + " ".join("H" if x == H else "A" for x in seq))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-n", type=int, default=30)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    seq, seed, checks, bal, r = generate(a.n, a.seed)
    if a.json:
        print(json.dumps({"seed": seed, "labels": seq}, indent=2))
    else:
        report(seq, seed, checks, bal, r)
