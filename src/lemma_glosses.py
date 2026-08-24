#!/usr/bin/env python3
"""Lemma-level English glosses from the Wiktionary extract (kaikki.org).

One deterministic download (data/kaikki_de.jsonl, sha256 recorded in
docs/DATA_SOURCES.md); no rate limits. For each deck lemma we keep the first
plain sense of the preferred part of speech (verb > noun > adj > adv > other),
skipping senses tagged archaic/obsolete/dated when others exist.

    .venv/bin/python src/lemma_glosses.py
Output: derived/glosses_lemma.csv (lemma, pos, gloss)
"""
import csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
SRC = DATA / "kaikki_de.jsonl"

POS_RANK = {"verb": 0, "noun": 1, "adj": 2, "adv": 3}
BAD_TAGS = {"archaic", "obsolete", "dated"}


def sense_gloss(sense):
    g = sense.get("glosses") or []
    return g[0].strip() if g else ""


def main():
    needed = {r["lemma"] for r in csv.DictReader(open(DERIVED / "wordlist.csv"))}
    found = {}   # word -> {pos: (gloss, n_bad_tags)}
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            w = e.get("word")
            if w not in needed:
                continue
            pos = e.get("pos", "")
            for s in e.get("senses", []):
                g = sense_gloss(s)
                if not g:
                    continue
                tags = set(s.get("tags", []))
                n_bad = len(tags & BAD_TAGS)
                cur = found.setdefault(w, {})
                if pos not in cur or n_bad < cur[pos][1]:
                    cur[pos] = (g, n_bad)
    rows = []
    for w in sorted(needed):
        per_pos = found.get(w)
        if not per_pos:
            continue
        pos = sorted(per_pos, key=lambda p: (POS_RANK.get(p, 9), per_pos[p][1]))[0]
        g, _ = per_pos[pos]
        rows.append({"lemma": w, "pos": pos, "gloss": g[:180]})
    with open(DERIVED / "glosses_lemma.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["lemma", "pos", "gloss"])
        w.writeheader()
        w.writerows(rows)
    print(f"lemma glosses: {len(rows)}/{len(needed)} ({len(rows) / len(needed) * 100:.0f}%)")


if __name__ == "__main__":
    main()
