#!/usr/bin/env python3
"""Download source e-texts (run on YOUR machine — needs open internet).
Gutenberg IDs marked CONFIRM must be checked on gutenberg.org before trusting."""
import pathlib, urllib.request

SOURCES = {
    "conrad_heart_of_darkness":  ("gutenberg", 219,   "confirmed"),
    "bronte_wuthering_heights":  ("gutenberg", 768,   "confirmed"),
    "whitman_leaves_of_grass":   ("gutenberg", 1322,  "any edition contains Section 1 line"),
    "gibran_the_prophet":        ("gutenberg", 58585, "CONFIRM id on gutenberg.org"),
    "blake_marriage":            ("gutenberg", None,  "CONFIRM id / else Wikisource"),
    "dickinson_F690":            ("manual",    None,  "CONFIRM PD first-publication volume, else swap round 9"),
    "tagore_fireflies":          ("manual",    None,  "Wikisource / archive.org — author's own English"),
}

OUT = pathlib.Path(__file__).parent / "sources"
OUT.mkdir(exist_ok=True)

for name, (kind, gid, note) in SOURCES.items():
    if kind != "gutenberg" or gid is None:
        print(f"SKIP  {name:28s} -> manual: {note}")
        continue
    url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
    dest = OUT / f"{name}.txt"
    print(f"GET   {name:28s} <- {url}  ({note})")
    urllib.request.urlretrieve(url, dest)
print("\nThen run G1 on every HUMAN round, e.g.:")
print('  python3 g1_verify.py --quote "We live, as we dream — alone." --source sources/conrad_heart_of_darkness.txt')
