#!/usr/bin/env python3
"""
Commit-reveal seals. The answer is sealed BEFORE anyone votes.

  seal   : proof = SHA-256("LABEL|round-id|salt"), salt kept secret.
           -> prints the caption line, stores the secret in proof/private/seals.json
              (git-ignored — NEVER committed before reveal).
  reveal : publishes label + salt, moves the entry to proof/revealed.json (public).

Anyone verifies with proof/verify.sh — no trust required.

Usage:
  python3 seal.py seal   --round 001 --label AI
  python3 seal.py reveal --round 001
"""

import argparse
import hashlib
import json
import pathlib
import secrets
import sys

HERE = pathlib.Path(__file__).parent
PRIVATE = HERE / "private" / "seals.json"      # git-ignored
PUBLIC = HERE / "revealed.json"                # committed after reveal

def load(path):
    return json.loads(path.read_text()) if path.exists() else {}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def digest(label: str, round_id: str, salt: str) -> str:
    return hashlib.sha256(f"{label}|round-{round_id}|{salt}".encode()).hexdigest()

def seal(round_id: str, label: str):
    label = label.upper()
    assert label in ("HUMAN", "AI"), "label must be HUMAN or AI"
    seals = load(PRIVATE)
    if round_id in seals:
        sys.exit(f"round {round_id} already sealed — refusing to overwrite")
    salt = secrets.token_hex(16)
    h = digest(label, round_id, salt)
    seals[round_id] = {"label": label, "salt": salt, "sha256": h}
    save(PRIVATE, seals)
    print(f"round        : {round_id}")
    print(f"sha256       : {h}")
    print(f"caption line : proof {h[:12]} · humanor.ai/proof")
    print("(salt stored in proof/private/ — publish NOTHING else today)")

def reveal(round_id: str):
    seals = load(PRIVATE)
    if round_id not in seals:
        sys.exit(f"no private seal for round {round_id}")
    entry = seals.pop(round_id)
    revealed = load(PUBLIC)
    revealed[round_id] = entry
    save(PUBLIC, revealed)
    save(PRIVATE, seals)
    print(f"REVEAL round {round_id}")
    print(f"label  : {entry['label']}")
    print(f"salt   : {entry['salt']}")
    print(f"sha256 : {entry['sha256']}")
    print(f"verify : ./verify.sh {entry['label']} {round_id} {entry['salt']}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["seal", "reveal"])
    p.add_argument("--round", required=True)
    p.add_argument("--label")
    a = p.parse_args()
    if a.cmd == "seal":
        if not a.label:
            p.error("--label required for seal")
        seal(a.round, a.label)
    else:
        reveal(a.round)
