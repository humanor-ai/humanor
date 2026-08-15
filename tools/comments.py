#!/usr/bin/env python3
"""
Comment classifier — turns free text into a vote.

This is the piece with real work in it. People do not write "HUMAN". They write
"ai fs", "definitely a machine", "🤖", "human 100%", "IA sans hésiter", "no way
a person wrote that", "H", "second one". The tally is only as good as this.

Design decisions:

  - NEGATION FIRST. "not human" is an AI vote, and any naive keyword match gets
    it exactly backwards. This is the single biggest source of silent error.
  - Deterministic rules, not a model. Every classification is explainable and
    reproducible, which matters because the fool rate becomes a public claim.
  - UNSURE is a real outcome. A comment that says "beautiful" is not a vote and
    must never be counted as one. Silent misclassification is worse than a gap.
  - Multilingual from day one: EN, FR, ES, PT, DE, IT.

Anything the rules cannot resolve is returned as UNSURE with its text, so it
can be read by a human or passed to a model later.
"""

import re
import unicodedata

HUMAN, AI, UNSURE = "HUMAN", "AI", "UNSURE"

# --------------------------------------------------------------------- lexicon

HUMAN_WORDS = [
    r"human", r"humain[e]?", r"humano?", r"mensch", r"umano",
    r"person", r"personne", r"persona", r"people", r"gente",
    r"poet", r"poete", r"poète", r"writer", r"author", r"auteur", r"escritor",
    r"real\s*(person|one)", r"vrai[e]?", r"verdadero",
]

AI_WORDS = [
    r"\bai\b", r"\ba\.i\.?\b", r"\bia\b", r"\bki\b",
    r"machine", r"maquina", r"máquina", r"maschine", r"macchina",
    r"robot", r"bot\b", r"chatgpt", r"gpt", r"claude", r"gemini", r"llm",
    r"artificial", r"artificiel[le]?", r"artificial\s*intelligence",
    r"computer", r"ordinateur", r"algorithm[e]?", r"algoritmo",
    r"generated", r"généré[e]?", r"genere[e]?", r"generado",
]

# Negation that flips the meaning of the word that follows it.
NEG = r"(?:not|no|never|isn'?t|ain'?t|aint|can'?t\s+be|couldn'?t\s+be|" \
      r"pas|jamais|aucun[e]?|ne\s+peut\s+pas|" \
      r"nunca|não|nao|nicht|kein[e]?|non)"

HUMAN_EMOJI = "🧠👤🙋👨👩🧑✍️📖❤️"
AI_EMOJI = "🤖⚙️💻🖥️🔌"

# Single letters people actually use as a whole comment.
SHORT = {"h": HUMAN, "a": AI, "ai": AI, "ia": AI, "hum": HUMAN, "hu": HUMAN}


# --------------------------------------------------------------------- helpers

def normalise(text):
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s\U0001F300-\U0001FAFF\u2600-\u27BF']", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _hits(text, words, window=28):
    """Find each keyword and whether a negation sits just before it.

    Overlapping patterns (e.g. 'human' and 'humano?') must not double-count the
    same word, or a single mention outweighs a genuine one on the other side."""
    seen = []          # spans already counted
    out = []
    for w in words:
        for m in re.finditer(w, text):
            if any(m.start() < e and s_ < m.end() for s_, e in seen):
                continue
            seen.append((m.start(), m.end()))
            before = text[max(0, m.start() - window):m.start()]
            out.append(bool(re.search(NEG + r"\s+(?:\w+\s+){0,2}$", before)))
    return out


def _is_echo(text):
    """People often just repeat the prompt: 'human or ai?', 'humain ou IA'.
    That is not a vote, and counting it would poison the tally."""
    return bool(re.search(
        r"\b(human|humain|humano|mensch)\w*\s+(or|ou|o|oder|of)\s+(ai|ia|ki)\b", text)
        or re.search(r"\b(ai|ia|ki)\s+(or|ou|o|oder)\s+(human|humain|humano)\w*\b", text))


# ------------------------------------------------------------------- classify

def classify(comment):
    """-> (vote, confidence, reason). Never guesses silently."""
    raw = comment or ""
    t = normalise(raw)
    if not t:
        return UNSURE, 0.0, "empty"

    # whole-comment shorthand
    if t in SHORT:
        return SHORT[t], 0.9, "shorthand"

    if _is_echo(t):
        return UNSURE, 0.2, "echoes the prompt, states nothing"

    h_hits = _hits(t, HUMAN_WORDS)
    a_hits = _hits(t, AI_WORDS)

    # negation flips the side: "not human" is a vote for AI
    h_score = sum(1 for n in h_hits if not n) + sum(1 for n in a_hits if n)
    a_score = sum(1 for n in a_hits if not n) + sum(1 for n in h_hits if n)

    flipped = any(h_hits) or any(a_hits) and any(_hits(t, AI_WORDS))
    negated_any = any(h_hits) or any(a_hits)

    # emoji carry weight only when no words decided it
    if h_score == a_score:
        h_score += sum(0.5 for c in HUMAN_EMOJI if c in raw)
        a_score += sum(0.5 for c in AI_EMOJI if c in raw)

    if h_score == 0 and a_score == 0:
        return UNSURE, 0.0, "no vote language"

    if h_score == a_score:
        return UNSURE, 0.3, "both sides mentioned equally"

    vote = HUMAN if h_score > a_score else AI
    lead = abs(h_score - a_score)
    total = h_score + a_score
    conf = min(0.95, 0.55 + 0.2 * lead + (0.15 if not negated_any else 0.0))
    return vote, round(conf, 2), f"h={h_score} a={a_score}"


# ------------------------------------------------------------------ self-test

CASES = [
    ("HUMAN", HUMAN), ("ai", AI), ("AI!!!", AI), ("h", HUMAN), ("IA", AI),
    ("definitely human", HUMAN),
    ("definitely a machine", AI),
    ("no way a human wrote that", AI),            # negation
    ("not human", AI),                            # negation
    ("this is not AI", HUMAN),                    # negation, other side
    ("c'est de l'IA sans hesiter", AI),
    ("humain a 100%", HUMAN),
    ("nunca un humano escribio esto", AI),        # spanish negation
    ("das ist keine maschine", HUMAN),            # german negation
    ("🤖", AI),
    ("🧠 for sure", HUMAN),
    ("a poet wrote this", HUMAN),
    ("chatgpt vibes", AI),
    ("beautiful line", UNSURE),
    ("i love this account", UNSURE),
    ("", UNSURE),
    ("human or ai? no idea", UNSURE),             # both sides named
]


def self_test():
    bad = 0
    for text, want in CASES:
        got, conf, why = classify(text)
        ok = got == want
        bad += not ok
        print(f"  {'ok ' if ok else 'FAIL'}  {text[:34]:36s} -> {got:6s} ({conf}) {why}")
    print(f"\n{len(CASES)-bad}/{len(CASES)} passed")
    return bad


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        v, c, w = classify(" ".join(sys.argv[1:]))
        print(f"{v}  confidence {c}  ({w})")
    else:
        sys.exit(1 if self_test() else 0)
