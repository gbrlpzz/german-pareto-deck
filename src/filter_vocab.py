#!/usr/bin/env python3
"""Remove word groups with no usable English gloss.

The rule is data-derived: keep a row when its lemma or selected form has a
non-empty Kaikki/form gloss after the same grammar-only cleanup as the deck.
This removes names and corpus-specific items that do not make useful cards.

Inputs: derived/wordlist.csv, derived/glosses_lemma.csv, derived/glosses.csv
Outputs: filtered derived/wordlist.csv and derived/vocab_exclusions.csv
"""
import csv
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
JUNK_PREFIXES = (
    "nominative", "genitive", "dative", "accusative", "inflection of",
    "third-person", "second-person", "first-person", "plural of",
    "past participle of", "present participle of", "preterite",
    "singular of",
)


def clean(value):
    value = (value or "").strip()
    low = value.casefold()
    return "" if any(low.startswith(prefix) for prefix in JUNK_PREFIXES) else value


def read_map(name, key):
    path = DERIVED / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return {row[key]: clean(row.get("gloss", "")) for row in csv.DictReader(fh)}


def main():
    rows = list(csv.DictReader(open(DERIVED / "wordlist.csv", encoding="utf-8")))
    lemma_gloss = read_map("glosses_lemma.csv", "lemma")
    form_gloss = read_map("glosses.csv", "form")
    kept, excluded = [], []
    for row in rows:
        if lemma_gloss.get(row["lemma"]) or form_gloss.get(row["form"]):
            kept.append(row)
        else:
            excluded.append({**row, "reason": "no_usable_dictionary_gloss"})
    fields = ["lemma", "form", "rank", "tier", "count", "forms"]
    with open(DERIVED / "wordlist.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept)
    with open(DERIVED / "vocab_exclusions.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields + ["reason"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(excluded)
    print(f"vocabulary: kept {len(kept)}; excluded {len(excluded)}")


if __name__ == "__main__":
    main()
