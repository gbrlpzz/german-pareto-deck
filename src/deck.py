#!/usr/bin/env python3
"""Build out/german-pareto-deck.apkg.

Card spec (METHODOLOGY D5):
  Word cards    production: EN gloss + blanked example -> recall the German form.
  Pattern cards cloze: the pattern deleted inside one authentic sentence.
Stable GUIDs: re-import updates existing cards instead of duplicating.
"""
import collections, csv, pathlib, re

import genanki

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
OUT = ROOT / "out" / "german-pareto-deck.apkg"

DECK_IDS = {"core": 1704000001, "ext": 1704000002, "pat": 1704000003}
MODEL_WORD = 1607392319
MODEL_PAT = 1607392398

CSS = """.card{font-family:-apple-system,Helvetica,sans-serif;font-size:20px;
text-align:center;color:#222;background:#fafafa}
.ex{margin:14px 0;font-size:22px}
.de{font-size:30px;font-weight:700;margin:10px 0}
.en{color:#555;font-style:italic}
.tier{font-size:12px;color:#999;text-transform:uppercase;letter-spacing:1px}
.cloze{font-weight:700;color:#2c5aa0}"""

word_model = genanki.Model(
    MODEL_WORD, "GP Word (production)",
    fields=[{"name": "Form"}, {"name": "GlossEN"}, {"name": "ExampleBlanked"},
            {"name": "ExampleDE"}, {"name": "ExampleEN"}, {"name": "Tier"}],
    templates=[{"name": "production",
                "qfmt": '<div class="tier">{{Tier}}</div>{{GlossEN}}'
                        '<div class="ex">{{ExampleBlanked}}</div>',
                "afmt": '{{FrontSide}}<hr id=answer><div class="de">{{Form}}</div>'
                        '<div class="ex">{{ExampleDE}}</div>'
                        '<div class="en">{{ExampleEN}}</div>'}],
    css=CSS)

pattern_model = genanki.Model(
    MODEL_PAT, "GP Pattern (cloze)",
    fields=[{"name": "Sentence"}, {"name": "Translation"}, {"name": "Class"}],
    model_type=genanki.MODEL_CLOZE,
    templates=[{"name": "cloze", "qfmt": "{{cloze:Sentence}}",
                "afmt": "{{cloze:Sentence}}<br><div class=\"en\">{{Translation}}</div>"}],
    css=CSS)


def load(path):
    p = DERIVED / path
    return list(csv.DictReader(open(p))) if p.exists() else []


def blank(text, form):
    pat = re.compile(r"\b" + re.escape(form) + r"\b", re.IGNORECASE)
    return pat.sub("______", text, count=1)


def main():
    gloss = {r["form"]: (r["pos"], r["gloss"]) for r in load("glosses.csv")}
    trans = {r["deu_sid"]: r["eng_text"] for r in load("translations.csv") if r["has_en"] == "yes"}
    ws = {r["form"]: r for r in load("word_sentences.csv")}

    decks = {k: genanki.Deck(v, f"German Pareto::{k.capitalize()}")
             for k, v in DECK_IDS.items()}

    n_words = 0
    for r in load("wordlist.csv"):
        f = r["form"]
        s = ws.get(f)
        if not s or not s["sid"]:
            continue
        de = s["de_text"]
        en = trans.get(s["sid"], "")
        _, g = gloss.get(f, ("", ""))
        note = genanki.Note(
            model=word_model,
            fields=[f, g, blank(de, f), de, en, r["tier"]],
            guid=genanki.guid_for("gpword", r["lemma"]),
            tags=[r["tier"], f"rank::{int(r['rank']) // 500 * 500}"])
        decks[r["tier"]].add_note(note)
        n_words += 1

    n_pat = 0
    for r in load("patterns_selected.csv"):
        exs = [x for x in r["examples"].split(";") if x]
        sent_sid = exs[0] if exs else ""
        if not sent_sid:
            continue
        # sentence text: recover from translations input corpus via word_sentences? no -
        # pattern sentences come from the corpus; we stored only ids in patterns.csv.
        # The deck stage therefore reads the corpus once for the needed sids.
        n_pat += 1  # placeholder replaced below

    # pattern sentence texts
    need = set()
    for r in load("patterns_selected.csv"):
        for x in r["examples"].split(";"):
            if x:
                need.add(x)
    import bz2
    sid_text = {}
    if need:
        with bz2.open(ROOT / "data" / "deu_sentences_detailed.tsv.bz2", "rt",
                      encoding="utf-8") as fh:
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 3 and p[0] in need:
                    sid_text[p[0]] = p[2]

    for r in load("patterns_selected.csv"):
        exs = [x for x in r["examples"].split(";") if x and x in sid_text]
        if not exs:
            continue
        de = sid_text[exs[0]]
        pattern = r["pattern"]
        cloze = de
        if " \u2026 " in pattern:
            a, b = pattern.split(" \u2026 ")
            m1 = re.search(r"\b" + re.escape(a) + r"\b", cloze, re.IGNORECASE)
            if m1:
                cloze = cloze[:m1.start()] + "{{c1::" + m1.group(0) + "}}" + cloze[m1.end():]
            m2 = re.search(r"\b" + re.escape(b) + r"\b", cloze, re.IGNORECASE)
            if m2:
                cloze = cloze[:m2.start()] + "{{c2::" + m2.group(0) + "}}" + cloze[m2.end():]
        else:
            m = re.search(r"\b" + re.escape(pattern) + r"\b", cloze, re.IGNORECASE)
            if m:
                cloze = cloze[:m.start()] + "{{c1::" + m.group(0) + "}}" + cloze[m.end():]
        note = genanki.Note(
            model=pattern_model,
            fields=[cloze, trans.get(exs[0], ""), r["class"]],
            guid=genanki.guid_for("gppat", pattern),
            tags=[r["group"], r["class"]])
        decks["pat"].add_note(note)
        n_pat += 1

    OUT.parent.mkdir(exist_ok=True)
    genanki.Package(list(decks.values())).write_to_file(str(OUT))
    print(f"word cards: {n_words}  pattern cards: {n_pat}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
