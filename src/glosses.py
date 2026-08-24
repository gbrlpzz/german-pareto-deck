#!/usr/bin/env python3
"""Best-effort EN glosses for core word cards from Wiktionary REST definitions.

Not a selection threshold: failures leave the field empty and the card still
ships with its translated example sentence. Resume-safe.
"""
import csv, pathlib, re, time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
OUT = DERIVED / "glosses.csv"
TAG = re.compile(r"<[^>]+>")

done = set()
if OUT.exists():
    done = {r["form"] for r in csv.DictReader(open(OUT)) if r["gloss"].strip()}

forms = []
with open(DERIVED / "top_forms.csv") as fh:
    for i, r in enumerate(csv.DictReader(fh)):
        if i >= 2000:
            break
        forms.append(r["form"])

new_file = not OUT.exists()
out = open(OUT, "a", newline="", encoding="utf-8")
w = csv.writer(out)
if new_file:
    w.writerow(["form", "pos", "gloss"])

fetched = 0
for f in forms:
    if f in done:
        continue
    gloss, pos = "", ""
    try:
        resp = requests.get(
            "https://en.wiktionary.org/api/rest_v1/page/definition/" + f,
            timeout=10,
            headers={"User-Agent": "german-pareto-deck/0.1 (open-source Anki deck)"})
        if resp.status_code == 200:
            for d in resp.json().get("de", []):
                defs = d.get("definitions") or []
                if defs:
                    pos = d.get("partOfSpeech", "")
                    gloss = TAG.sub("", defs[0].get("definition", ""))[:180]
                    break
    except Exception:
        pass
    w.writerow([f, pos, gloss])
    out.flush()
    fetched += 1
    if fetched % 200 == 0:
        print("fetched", fetched, flush=True)
    time.sleep(0.55)   # stay well under Wiktionary anonymous rate limits
out.close()
print("glosses complete:", fetched)
