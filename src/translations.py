#!/usr/bin/env python3
"""Attach authentic EN translations to selected pattern exemplars.

Inputs: derived/patterns_selected.csv (examples column), data/links.tar.bz2
        (member links.csv), data/eng_sents.tsv.bz2.
Rule: shortest available translation per sentence (brevity = card fit).
Output: derived/translations.csv (deu_sid, has_en, eng_text)
"""
import bz2, csv, io, pathlib, tarfile, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"

need = set()
for r in csv.DictReader(open(DERIVED / "patterns_selected.csv")):
    for s in r["examples"].split(";"):
        if s.strip():
            need.add(s.strip())
ws = DERIVED / "word_sentences.csv"
if ws.exists():
    for r in csv.DictReader(open(ws)):
        if r["sid"]:
            need.add(r["sid"])
print("sentences needing translation:", len(need), flush=True)

tid_for = collections.defaultdict(set)
with tarfile.open(DATA / "links.tar.bz2", "r:bz2") as tf:
    stream = io.TextIOWrapper(tf.extractfile("links.csv"), encoding="utf-8")
    for line in stream:
        a, sep, b = line.rstrip("\n").partition("\t")
        if a in need:
            tid_for[a].add(b)
print("with >=1 link:", len(tid_for), flush=True)

wanted = set()
for s in tid_for.values():
    wanted |= s
texts = {}
with bz2.open(DATA / "eng_sents.tsv.bz2", "rt", encoding="utf-8") as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3 and p[1] == "eng" and p[0] in wanted:
            texts[p[0]] = p[2]

rows = []
have = 0
for sid in sorted(need):
    cands = [texts[t] for t in tid_for.get(sid, ()) if t in texts]
    if cands:
        have += 1
        rows.append((sid, "yes", min(cands, key=len)))
    else:
        rows.append((sid, "no", ""))

with open(DERIVED / "translations.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["deu_sid", "has_en", "eng_text"])
    w.writerows(rows)
print(f"translations: {have}/{len(need)} ({have / len(need) * 100:.1f}%)")
