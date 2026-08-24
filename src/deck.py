#!/usr/bin/env python3
"""Build out/german-pareto-deck.apkg.

Card spec (METHODOLOGY D5):
  Word cards    production: EN gloss + blanked example -> recall the German form.
  Pattern cards cloze: the pattern deleted inside one authentic sentence.
Stable GUIDs: re-import updates existing cards instead of duplicating.
"""
import collections, csv, pathlib, re, time, zipfile

import genanki

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
OUT = ROOT / "out" / "german-pareto-deck.apkg"

DECK_IDS = {"core": 1704000001, "ext": 1704000002, "patterns": 1704000003}
MODEL_WORD = 1607392319
MODEL_PAT = 1607392398
BUILD_TIMESTAMP = 1700000000

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
    model_type=genanki.Model.CLOZE,
    templates=[{"name": "cloze", "qfmt": "{{cloze:Sentence}}",
                "afmt": "{{cloze:Sentence}}<br><div class=\"en\">{{Translation}}</div>"}],
    css=CSS)


pattern_rec_model = genanki.Model(
    1607392399, "GP Pattern (recognize)",
    fields=[{"name": "Chunk"}, {"name": "Sentence"}, {"name": "Translation"},
            {"name": "Class"}],
    templates=[{"name": "recognize",
                "qfmt": '<div class="de">{{Chunk}}</div>'
                        '<div class="ex">{{Sentence}}</div>',
                "afmt": '{{FrontSide}}<hr id=answer>'
                        '<div class="en">{{Translation}}</div>'}],
    css=CSS)


def load(path):
    p = DERIVED / path
    return list(csv.DictReader(open(p, encoding="utf-8", newline=""))) if p.exists() else []


def normalize_apkg(path):
    """Normalize ZIP metadata so identical inputs produce identical bytes."""
    temporary = path.with_suffix(path.suffix + ".normalized")
    stamp = time.gmtime(BUILD_TIMESTAMP)[:6]
    with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name in sorted(source.namelist()):
            info = zipfile.ZipInfo(name, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o600 << 16
            target.writestr(info, source.read(name))
    temporary.replace(path)


def blank(text, form):
    pat = re.compile(r"\b" + re.escape(form) + r"\b", re.IGNORECASE)
    return pat.sub("______", text, count=1)


WORD_RE = re.compile(r"[A-Za-z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df']+")

JUNK_GLOSS_PREFIXES = ("nominative", "genitive", "dative", "accusative",
                       "inflection of", "third-person", "second-person",
                       "first-person", "plural of", "past participle of",
                       "present participle of", "preterite", "singular of")


def clean_gloss(g):
    """Drop grammar-only descriptors; an empty cue beats a junk cue."""
    g = (g or "").strip()
    low = g.lower()
    if any(low.startswith(p) for p in JUNK_GLOSS_PREFIXES):
        return ""
    return g


def _norm_word(w):
    return w.lower().replace("'", "\u2019").replace("\u2019", "")


def make_cloze(de, pattern):
    """Cloze `pattern` inside sentence `de`; None if absent.

    Token-span matching: tolerant of punctuation and apostrophes between and
    inside words (geht's <-> gehts, "ich wei\u00df nicht, ob" keeps its comma).
    Each matched word gets its own {{c1::...}}; punctuation stays visible.
    """
    pwords = [_norm_word(w) for w in WORD_RE.findall(pattern)]
    toks = [(m.group(0), m.start(), m.end()) for m in WORD_RE.finditer(de)]
    nt = [_norm_word(t[0]) for t in toks]
    if " \u2026 " in pattern:
        if len(pwords) != 2:
            return None
        ia = next((i for i, w in enumerate(nt) if w == pwords[0]), None)
        if ia is None:
            return None
        ib = next((i for i in range(ia + 1, len(nt)) if nt[i] == pwords[1]), None)
        if ib is None:
            return None
        spans = [toks[ia], toks[ib]]
    else:
        n = len(pwords)
        spans = None
        for i in range(len(nt) - n + 1):
            if nt[i:i + n] == pwords:
                spans = toks[i:i + n]
                break
        if spans is None:
            return None
    out = de
    for word, s, e in sorted(spans, key=lambda x: -x[1]):
        out = out[:s] + "{{c1::" + word + "}}" + out[e:]
    return out


def main():
    gloss = {r["form"]: (r["pos"], r["gloss"]) for r in load("glosses.csv")}
    for r in load("glosses_lemma.csv"):      # lemma-level glosses win (v0.2)
        if r["gloss"].strip():
            gloss[r["lemma"]] = (r["pos"], r["gloss"])
    trans = {r["deu_sid"]: r["eng_text"] for r in load("translations.csv") if r["has_en"] == "yes"}
    ws = {r["form"]: r for r in load("word_sentences.csv")}

    deck_names = {"core": "Core", "ext": "Extension", "patterns": "Patterns"}
    decks = {k: genanki.Deck(v, f"German Pareto::{deck_names[k]}")
             for k, v in DECK_IDS.items()}

    n_words = 0
    for r in load("wordlist.csv"):
        f = r["form"]
        s = ws.get(f)
        if not s or not s["sid"]:
            continue
        de = s["de_text"]
        en = trans.get(s["sid"], "")
        g = clean_gloss(gloss.get(r["lemma"], gloss.get(f, ("", "")))[1])
        note = genanki.Note(
            model=word_model,
            fields=[f, g, blank(de, f), de, en, r["tier"]],
            guid=genanki.guid_for("gpword", r["lemma"]),
            tags=[r["tier"], f"rank::{int(r['rank']) // 500 * 500}"])
        decks[r["tier"]].add_note(note)
        n_words += 1

    n_pat = 0
    n_rec = 0
    n_skipped = [0]
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
                    sid_text[p[0]] = p[2].strip()

    for r in load("patterns_selected.csv"):
        exs = [x for x in r["examples"].split(";") if x and x in sid_text]
        if not exs:
            continue
        de = sid_text[exs[0]]
        cloze = make_cloze(de, r["pattern"])
        if cloze is None:
            n_skipped[0] += 1
            continue
        note = genanki.Note(
            model=pattern_model,
            fields=[cloze, trans.get(exs[0], ""), r["class"]],
            guid=genanki.guid_for("gppat", r["pattern"]),
            tags=[r["group"], r["class"]])
        decks["patterns"].add_note(note)
        n_pat += 1

    for r in load("patterns_selected.csv"):
        if r["class"] not in ("routine", "particle_frame"):
            continue
        exs = [x for x in r["examples"].split(";") if x and x in sid_text]
        if not exs:
            continue
        note = genanki.Note(
            model=pattern_rec_model,
            fields=[r["pattern"], sid_text[exs[0]], trans.get(exs[0], ""), r["class"]],
            guid=genanki.guid_for("gppatr", r["pattern"]),
            tags=[r["group"], r["class"], "recognize"])
        decks["patterns"].add_note(note)
        n_rec += 1

    OUT.parent.mkdir(exist_ok=True)
    genanki.Package(list(decks.values())).write_to_file(
        str(OUT), timestamp=BUILD_TIMESTAMP)
    normalize_apkg(OUT)
    print(f"word cards: {n_words}  pattern cards: {n_pat}  patterns skipped (no cloze match): {n_skipped[0]}  recognition cards: {n_rec}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
