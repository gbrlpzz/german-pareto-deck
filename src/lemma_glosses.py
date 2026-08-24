#!/usr/bin/env python3
"""Lemma-level English glosses from the Wiktionary extract (kaikki.org).

One deterministic download (data/kaikki_de.jsonl, sha256 recorded in
docs/DATA_SOURCES.md); no rate limits. For each deck lemma we keep the first
plain sense from the common POS order. Wiktionary form-of links fill residual
inflected groups. Spelling alternatives and two documented phrase glosses cover
remaining source gaps.

    .venv/bin/python src/lemma_glosses.py
Output: derived/glosses_lemma.csv (lemma, pos, gloss, source)
"""
import csv, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
SRC = DATA / "kaikki_de.jsonl"

POS_RANK = {
    "verb": 0, "adj": 1, "adv": 2, "conj": 3, "prep": 4,
    "pron": 5, "det": 6, "article": 6, "noun": 7, "num": 8,
    "intj": 9, "particle": 10, "prefix": 11,
}
BAD_TAGS = {"archaic", "obsolete", "dated"}
FORM_PREFIXES = (
    "inflection of", "form of", "plural of", "past participle of",
    "present participle of", "first-person", "second-person", "third-person",
    "first/third-person", "first/second-person", "comparative degree of",
    "superlative degree of", "preterite of", "subjunctive",
    "nominative", "accusative", "dative", "genitive",
)
ALT_PHRASE_GLOSSES = {
    # Wiktionary records these as spelling variants of multiword entries.
    "wieviel": "how much; how many",
    "jedesmal": "every time",
}
SOURCE_FALLBACK_GLOSSES = {
    # The extract marks the current spelling as obsolete but still gives a
    # direct translation. Keep the translation instead of an empty cue.
    "märz": "March",
}


def useful_gloss(sense):
    """Return (gloss, quality, kind); discard grammar-only form glosses."""
    glosses = [str(g).strip() for g in (sense.get("glosses") or []) if str(g).strip()]
    if not glosses:
        return None
    tags = set(sense.get("tags") or [])
    is_form = "form-of" in tags
    for gloss in glosses:
        low = gloss.casefold()
        if is_form:
            # Some form entries include the learner gloss in quotes:
            # "nominative plural of diejenige (“those”)".
            quoted = re.search(r'["“]([^"”]+)["”]', gloss)
            if quoted:
                return quoted.group(1).strip(), 0, "form-of"
        if low.startswith(("comparative degree of", "superlative degree of")):
            tail = gloss.split(";", 1)[1].strip() if ";" in gloss else ""
            if tail:
                return tail, 0, "comparative"
            continue
        if any(low.startswith(prefix) for prefix in FORM_PREFIXES):
            # A few entries omit the structured form_of field but retain a
            # useful phrase: "... plural chicken of Huhn".
            m = re.search(r"\b(?:plural|singular)\s+(.+?)\s+of\s+[^ (]+", gloss,
                          flags=re.IGNORECASE)
            candidate = m.group(1).strip() if m else ""
            if candidate and candidate.casefold() not in {
                    "of", "the", "preterite", "present", "past", "subjunctive",
                    "imperative", "singular", "plural"}:
                return candidate, 0, "form-of"
            continue
        if is_form:
            continue
        quality = int(bool(tags & BAD_TAGS))
        return gloss, quality, "entry"
    return None



def main():
    word_rows = list(csv.DictReader(open(DERIVED / "wordlist.csv", encoding="utf-8")))
    needed = {r["lemma"] for r in word_rows}
    # German nouns and some proper names are capitalized in Wiktionary.
    # Match case-insensitively but keep the deck's lemma spelling.
    aliases = {}
    for r in word_rows:
        lemma = r["lemma"]
        aliases.setdefault(lemma.casefold(), set()).add((lemma, 0))
        for form in (r.get("forms", "") + ";" + r.get("form", "")).split(";"):
            if form.strip():
                aliases.setdefault(form.strip().casefold(), set()).add((lemma, 1))

    # deck lemma -> candidates (quality, alias priority, POS priority,
    # line index, sense index, pos, gloss, source kind)
    found = {}
    redirects = {}
    ref_words = set()
    with open(SRC, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            targets = aliases.get(str(e.get("word", "")).casefold())
            if not targets:
                continue
            # Wiktionary lists spelling alternatives on the citation entry.
            # Add them before their own lines are read.
            for form_entry in e.get("forms", []):
                alt = form_entry.get("form")
                if alt and "alternative" in set(form_entry.get("tags", [])):
                    for lemma, _ in list(targets):
                        aliases.setdefault(alt.casefold(), set()).add((lemma, 1))
            pos = e.get("pos", "")
            for sense_no, sense in enumerate(e.get("senses", [])):
                for ref in sense.get("form_of", []):
                    ref_word = ref.get("word")
                    if ref_word:
                        # Kaikki may annotate a citation form as
                        # "laufen 'to run'". Keep the headword only.
                        ref_word = re.split(r"\s+['\"]", ref_word, maxsplit=1)[0].strip()
                        ref_words.add(ref_word.casefold())
                        for lemma, _ in targets:
                            redirects.setdefault(lemma, set()).add(ref_word)
                item = useful_gloss(sense)
                if item is None:
                    continue
                gloss, quality, kind = item
                for lemma, alias_priority in targets:
                    found.setdefault(lemma, []).append(
                        (quality, alias_priority, POS_RANK.get(pos, 99),
                         line_no, sense_no, pos, gloss, kind))

    # Some rule-based groups have no citation form in the selected 4,000
    # forms (for example dachte -> denken). Read only the referenced citation
    # forms in a second pass so those cards still get a real gloss.
    canonical_found = {}
    if ref_words:
        with open(SRC, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh):
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                word_key = str(e.get("word", "")).casefold()
                if word_key not in ref_words:
                    continue
                pos = e.get("pos", "")
                for sense_no, sense in enumerate(e.get("senses", [])):
                    item = useful_gloss(sense)
                    if item is None:
                        continue
                    gloss, quality, kind = item
                    canonical_found.setdefault(word_key, []).append(
                        (quality, 0, POS_RANK.get(pos, 99), line_no,
                         sense_no, pos, gloss, kind))

    direct_chosen = {}
    direct_fallback = {}
    for lemma in sorted(needed):
        direct = found.get(lemma, [])
        good = [c for c in direct if c[0] == 0]
        if good:
            direct_chosen[lemma] = min(good, key=lambda c: c[:5])
        elif direct:
            direct_fallback[lemma] = min(direct, key=lambda c: c[:5])

    resolving = set()
    resolved = {}

    def resolve(lemma):
        if lemma in resolved:
            return resolved[lemma]
        if lemma in resolving:
            return None
        resolving.add(lemma)
        prefer_redirect = (
            lemma in direct_chosen and lemma in redirects and
            direct_chosen[lemma][1] == 1 and
            direct_chosen[lemma][7] == "entry")
        if lemma in direct_chosen and not prefer_redirect:
            result = direct_chosen[lemma]
        else:
            candidates = []
            for ref_word in redirects.get(lemma, set()):
                # The citation form may sit outside the selected vocabulary.
                candidates.extend(
                    (c[0], c[1], c[2], c[3], c[4], c[5], c[6], "form-of")
                    for c in canonical_found.get(ref_word.casefold(), [])
                    if c[0] == 0)
                # Or it may resolve through another selected pseudo-lemma.
                for ref_lemma, alias_priority in aliases.get(ref_word.casefold(), set()):
                    if alias_priority == 0:
                        c = resolve(ref_lemma)
                        if c is not None:
                            candidates.append((c[0], c[1], c[2], c[3], c[4],
                                               c[5], c[6], "form-of"))
            # An alternate spelling can have a separate entry. Reuse its
            # gloss when the exact spelling has only an obsolete/form entry.
            if not candidates:
                for other, alias_priority in aliases.get(lemma.casefold(), set()):
                    if alias_priority == 1 and other != lemma:
                        c = resolve(other)
                        if c is not None:
                            candidates.append((c[0], c[1], c[2], c[3], c[4],
                                               c[5], c[6], "alias"))
            if not candidates:
                candidates = [direct_fallback[lemma]] if lemma in direct_fallback else []
            result = min(candidates, key=lambda c: c[:5]) if candidates else None
        resolving.remove(lemma)
        if result is not None:
            resolved[lemma] = result
        return result

    chosen = {lemma: resolve(lemma) for lemma in needed}
    for lemma, gloss in ALT_PHRASE_GLOSSES.items():
        if lemma in needed:
            chosen[lemma] = (0, 0, POS_RANK.get("adv", 99), 10**12, 0,
                             "adv", gloss, "curated")
    for lemma, gloss in SOURCE_FALLBACK_GLOSSES.items():
        if lemma in needed:
            chosen[lemma] = (0, 1, POS_RANK.get("noun", 99), 10**12, 0,
                             "noun", gloss, "source-fallback")

    rows = []
    for lemma in sorted(needed):
        c = chosen.get(lemma)
        if c is None:
            continue
        _, alias_priority, _, _, _, pos, gloss, kind = c
        if kind == "form-of":
            source = "form-of"
        elif kind == "alias":
            source = "alias"
        elif kind == "curated":
            source = "curated-phrase"
        elif kind == "source-fallback":
            source = "source-fallback"
        elif kind == "comparative":
            source = "lemma" if alias_priority == 0 else "form-fallback"
        else:
            source = "lemma" if alias_priority == 0 else "form-fallback"
        rows.append({"lemma": lemma, "pos": pos, "gloss": gloss[:180],
                     "source": source})
    with open(DERIVED / "glosses_lemma.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["lemma", "pos", "gloss", "source"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"lemma glosses: {len(rows)}/{len(needed)} ({len(rows) / len(needed) * 100:.0f}%)")


if __name__ == "__main__":
    main()
