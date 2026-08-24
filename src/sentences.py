#!/usr/bin/env python3
"""Pick exemplar sentences for word cards.

D8d window (corpus IQR); preference: most top-2,000-form tokens (context density),
then shortest. Output: derived/word_sentences.csv (form, sid, alt, de_text)
"""
import bz2, collections, csv, heapq, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
TOKEN_RE = re.compile(r"[a-z\u00e4\u00f6\u00fc\u00df']+")


def toks(text):
    return [w for w in (m.strip("'") for m in TOKEN_RE.findall(text.lower())) if w]


wl = list(csv.DictReader(open(DERIVED / "wordlist.csv")))
targets = {r["form"] for r in wl}
top2 = set()
with open(DERIVED / "top_forms.csv") as fh:
    for i, r in enumerate(csv.DictReader(fh)):
        if i >= 2000:
            break
        top2.add(r["form"])
q1, q3 = json.load(open(DERIVED / "pattern_stats.json"))["length_iqr"]

best = collections.defaultdict(list)
texts = {}
with bz2.open(DATA / "deu_sentences_detailed.tsv.bz2", "rt", encoding="utf-8") as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) < 3 or p[1] != "deu":
            continue
        sid, text = p[0], p[2].strip()
        tk = toks(text)
        if not (q1 <= len(tk) <= q3):
            continue
        hits = {w for w in tk if w in targets}
        if not hits:
            continue
        density = len({w for w in tk if w in top2})
        texts[sid] = text
        for w in hits:
            heapq.heappush(best[w], (-density, len(tk), sid))
            if len(best[w]) > 4:
                heapq.heappop(best[w])

rows = []
for r in wl:
    h = best.get(r["form"])
    if not h:
        rows.append({"form": r["form"], "sid": "", "alt": "", "de_text": ""})
        continue
    ordered = sorted(h)                      # highest density first
    sid = ordered[0][2]
    rows.append({"form": r["form"], "sid": sid,
                 "alt": ";".join(s for _, _, s in ordered[1:4]),
                 "de_text": texts[sid]})

with open(DERIVED / "word_sentences.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["form", "sid", "alt", "de_text"],
                      lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
covered = sum(1 for r in rows if r["sid"])
print(f"word exemplars: {covered}/{len(rows)} ({covered / len(rows) * 100:.1f}%)")
