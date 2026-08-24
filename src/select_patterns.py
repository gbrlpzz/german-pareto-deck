#!/usr/bin/env python3
"""Select the final pattern set.

Rule chain (every constant justified, METHODOLOGY D3/D4/D8):
  1. TOTAL = 500 .................. literature anchor (PHRASE List scale, Martinez &
                                    Schmitt 2012; adopted as D3).
  2. Group targets = D4 mix ....... research-report reasoned shares:
                                    perfekt+modal 120, separable 100, funkverb 90,
                                    particle+connector 70, routines 50, bundles 70.
  3. Bundle eligibility n >= 3 .... listable multiword units (PHRASE List median
                                    length 3); shorter n-grams are syntax, not chunks.
  4. Shortfall redistribution .... groups with unavailable candidates release their
                                    deficit to groups with surplus, proportional to
                                    the D4 targets (single documented rule).
  5. Within-group class split ..... proportional to candidate availability (data).
  6. Rank within class ............ corpus frequency (deck goal is coverage;
                                    significance already guaranteed at admission, D8a).

Output: derived/patterns_selected.csv, derived/selection_summary.json
"""
import csv, json, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
TOTAL = 500
GROUPS = [
    ("routine", 50, ["routine"]),
    ("perfekt_modal", 120, ["perfekt_frame", "modal_frame"]),
    ("separable", 100, ["separable_frame"]),
    ("funkverb", 90, ["funkverbgefüge"]),
    ("particle_connector", 70, ["particle_frame", "connector_bundle"]),
    ("bundle", 70, ["lexical_bundle"]),
]

rows = list(csv.DictReader(open(DERIVED / "patterns.csv")))

cand = {}
for g, target, classes in GROUPS:
    pool = [r for r in rows if r["class"] in classes and int(r["count"]) > 0
            and r["examples"].strip()]   # D5: every card needs an authentic sentence
    if g == "bundle":
        pool = [r for r in pool if int(r.get("n") or 0) >= 3]
    pool.sort(key=lambda r: -int(r["count"]))
    cand[g] = pool

assigned = {g: min(t, len(cand[g])) for g, t, _ in GROUPS}
leftover = TOTAL - sum(assigned.values())
redist = []
for _ in range(20):
    if leftover <= 0:
        break
    open_groups = [g for g, t, _ in GROUPS if len(cand[g]) - assigned[g] > 0]
    if not open_groups:
        break
    tot = sum(t for g, t, _ in GROUPS if g in open_groups)
    moved = 0
    for g, t, _ in GROUPS:
        if g in open_groups:
            add = min(int(leftover * t / tot + 0.5), len(cand[g]) - assigned[g])
            assigned[g] += add
            moved += add
    redist.append(moved)
    leftover = TOTAL - sum(assigned.values())

out = []
for g, target, classes in GROUPS:
    a = assigned[g]
    avail = {c: len([r for r in cand[g] if r["class"] == c]) for c in classes}
    tot_avail = sum(avail.values()) or 1
    taken = 0
    for i, c in enumerate(classes):
        share = a * avail[c] / tot_avail
        k = int(round(share)) if i < len(classes) - 1 else a - taken
        k = max(0, min(k, avail[c], a - taken))
        taken += k
        for rank, r in enumerate([r for r in cand[g] if r["class"] == c][:k], 1):
            out.append({**r, "group": g, "rank": rank})

with open(DERIVED / "patterns_selected.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["group", "rank", "class", "pattern", "count",
                                       "tscore", "kind", "n", "examples"])
    w.writeheader()
    w.writerows(out)

summary = {
    "total_target": TOTAL,
    "groups": {g: {"target": t, "available": len(cand[g]), "assigned": assigned[g],
                   "classes": {c: sum(1 for r in out if r["group"] == g and r["class"] == c)
                               for c in classes}}
               for g, t, classes in GROUPS},
    "redistribution_moves": redist,
    "final_total": len(out),
}
(DERIVED / "selection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False, indent=2))
