#!/usr/bin/env python3
"""
G1 — Verbatim verification gate.

A human quote is publishable ONLY if it is found in the electronic source
text (Project Gutenberg / Wikisource). Two passes:

  PASS A (STRICT) : whitespace-normalized exact substring match.
  PASS B (NORM)   : additionally unifies dashes ( -- / — / – ), curly/straight
                    quotes, and ignores the quote's *terminal* punctuation.
                    A PASS-B match REQUIRES a human decision: the displayed
                    phrase must be updated to the source's canonical form.

No match on either pass = REJECTED. No exceptions, no matter how famous
the attribution is on the internet.

Usage:
  python3 g1_verify.py --quote "We live, as we dream — alone." --source sources/conrad_heart_of_darkness.txt
  python3 g1_verify.py --self-test
"""

import argparse
import re
import sys
import unicodedata

# ---------------------------------------------------------------- normalize

def norm_ws(text: str) -> str:
    """Collapse all whitespace runs (incl. newlines) to single spaces."""
    return re.sub(r"\s+", " ", text).strip()

def norm_punct(text: str) -> str:
    """Unify dash and quote variants. Used by PASS B only."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s*(--|—|–)\s*", "—", text)      # any dash form -> em dash, no spaces
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201C", '"').replace("\u201D", '"')
    return text

def strip_terminal(text: str) -> str:
    """Drop trailing punctuation of the QUOTE (source may end '....' etc.)."""
    return re.sub(r"[\s\.\!\?\u2026,;:]+$", "", text)

# ------------------------------------------------------------------- verify

def find(haystack: str, needle: str):
    i = haystack.lower().find(needle.lower())
    return i if i >= 0 else None

def context(source_norm: str, idx: int, needle_len: int, pad: int = 80) -> str:
    a = max(0, idx - pad)
    b = min(len(source_norm), idx + needle_len + pad)
    return ("…" if a > 0 else "") + source_norm[a:b] + ("…" if b < len(source_norm) else "")

def verify(quote: str, source_text: str) -> dict:
    src_a = norm_ws(source_text)
    q_a = norm_ws(quote)

    idx = find(src_a, q_a)
    if idx is not None:
        return {"status": "VERIFIED_STRICT", "pass": "A",
                "canonical": src_a[idx:idx + len(q_a)],
                "context": context(src_a, idx, len(q_a))}

    src_b = norm_punct(src_a)
    q_b = strip_terminal(norm_punct(q_a))
    idx = find(src_b, q_b)
    if idx is not None:
        return {"status": "VERIFIED_NORM (human decision required: "
                          "set displayed text to the canonical source form)",
                "pass": "B",
                "canonical": src_b[idx:idx + len(q_b)],
                "context": context(src_b, idx, len(q_b))}

    return {"status": "REJECTED", "pass": None, "canonical": None, "context": None}

# ---------------------------------------------------------------- self-test

SAMPLE_SOURCE = """It was the
farthest point of navigation and the culminating
point of my experience. We live, as we dream--alone....
While the dream disappears, the life goes on."""

def self_test() -> int:
    ok = True

    r1 = verify("We live, as we dream — alone.", SAMPLE_SOURCE)
    print("[T1] typographic em-dash + period vs source '--....' ->", r1["status"])
    ok &= r1["pass"] == "B" and "dream—alone" in r1["canonical"]

    r2 = verify("We live, as we dream--alone....", SAMPLE_SOURCE)
    print("[T2] exact source form (across line breaks)          ->", r2["status"])
    ok &= r2["pass"] == "A"

    r3 = verify("We live as we dream, together.", SAMPLE_SOURCE)
    print("[T3] fake variant                                    ->", r3["status"])
    ok &= r3["status"] == "REJECTED"

    print("\nSELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

# --------------------------------------------------------------------- main

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--quote")
    p.add_argument("--source")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        sys.exit(self_test())

    if not (a.quote and a.source):
        p.error("--quote and --source are required (or use --self-test)")

    with open(a.source, encoding="utf-8", errors="replace") as f:
        res = verify(a.quote, f.read())

    print("STATUS   :", res["status"])
    if res["canonical"]:
        print("CANONICAL:", res["canonical"])
        print("CONTEXT  :", res["context"])
    sys.exit(0 if res["pass"] else 1)
