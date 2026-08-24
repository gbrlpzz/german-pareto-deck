#!/usr/bin/env python3
"""Attach authentic EN translations to selected pattern exemplars.

Inputs: derived/patterns_selected.csv (examples column), data/links.tar.bz2
        (member links.csv), data/eng_sents.tsv.bz2.
Rule: shortest available translation per sentence (brevity = card fit), with
lexicographic tie-breaking for reproducibility.
Output: derived/translations.csv (deu_sid, has_en, eng_text)
"""
import bz2
import csv
import io
import pathlib
import tarfile
import collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"


def shortest_translation(candidates):
    return min(candidates, key=lambda text: (len(text), text))


def main():
    need = set()
    with open(DERIVED / "patterns_selected.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for sentence_id in row["examples"].split(";"):
                if sentence_id.strip():
                    need.add(sentence_id.strip())
    word_sentences = DERIVED / "word_sentences.csv"
    if word_sentences.exists():
        with open(word_sentences, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row["sid"]:
                    need.add(row["sid"])
    print("sentences needing translation:", len(need), flush=True)

    tid_for = collections.defaultdict(set)
    with tarfile.open(DATA / "links.tar.bz2", "r:bz2") as archive:
        stream = io.TextIOWrapper(archive.extractfile("links.csv"), encoding="utf-8")
        for line in stream:
            german_id, _, english_id = line.rstrip("\n").partition("\t")
            if german_id in need:
                tid_for[german_id].add(english_id)
    print("with >=1 link:", len(tid_for), flush=True)

    wanted = set()
    for ids in tid_for.values():
        wanted |= ids
    texts = {}
    with bz2.open(DATA / "eng_sents.tsv.bz2", "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[1] == "eng" and parts[0] in wanted:
                texts[parts[0]] = parts[2]

    rows = []
    have = 0
    for sentence_id in sorted(need):
        candidates = [texts[translation_id]
                      for translation_id in tid_for.get(sentence_id, ())
                      if translation_id in texts]
        if candidates:
            have += 1
            rows.append((sentence_id, "yes", shortest_translation(candidates)))
        else:
            rows.append((sentence_id, "no", ""))

    with open(DERIVED / "translations.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(["deu_sid", "has_en", "eng_text"])
        writer.writerows(rows)
    print(f"translations: {have}/{len(need)} ({have / len(need) * 100:.1f}%)")


if __name__ == "__main__":
    main()
