#!/usr/bin/env python3
"""Build the word list: top forms -> lemma groups -> tiers.

D2: core = lemmas whose best form ranks <= 2,000; extension = <= 4,000.
D6: lemma grouping rule-based (see src/lemmatize.py); form-level fallback.
D8: proper-name blocklist shared with the pattern extractor; single letters dropped.
Output: derived/wordlist.csv (lemma, form, rank, tier, count, forms)
"""
import collections, csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
TOP_N = 4000        # D2
CORE_N = 2000       # D2

stats = json.load(open(DERIVED / "pattern_stats.json"))
NAMES = set(stats["criteria"]["name_blocklist"])

forms = []
with open(DERIVED / "top_forms.csv") as fh:
    for i, r in enumerate(csv.DictReader(fh)):
        if i >= TOP_N:
            break
        forms.append(r)

lemma = {}
lg = DERIVED / "lemma_groups.csv"
if lg.exists():
    for r in csv.DictReader(open(lg)):
        lemma[r["form"]] = r["lemma"]
else:
    print("lemma_groups.csv missing - form-level fallback (D6)")

groups = collections.defaultdict(list)
for r in forms:
    w = r["form"]
    if w in NAMES or len(w) == 1:
        continue
    groups[lemma.get(w, w)].append(r)

rows = []
for lem, g in groups.items():
    g.sort(key=lambda r: int(r["rank"]))
    best = g[0]
    rows.append({"lemma": lem, "form": best["form"], "rank": int(best["rank"]),
                 "tier": "core" if int(best["rank"]) <= CORE_N else "ext",
                 "count": best["count"],
                 "forms": ";".join(x["form"] for x in g[:6])})
rows.sort(key=lambda r: r["rank"])

with open(DERIVED / "wordlist.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["lemma", "form", "rank", "tier", "count", "forms"])
    w.writeheader()
    w.writerows(rows)
print(f"lemmas: {len(rows)}  core: {sum(1 for r in rows if r['tier']=='core')}  "
      f"ext: {sum(1 for r in rows if r['tier']=='ext')}")
