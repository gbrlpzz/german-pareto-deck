#!/usr/bin/env python3
"""Build safe POS-aware lemma overrides from the Kaikki extract.

Rules:
- Use a Kaikki ``form_of`` link only when the surface entry has no lexical
  sense and points to one citation form.
- For a clipped rule-based group, use the surface as the lemma only when its
  dictionary entry has one safe non-verb POS.
- Leave ambiguous forms unchanged.

Outputs: derived/lemma_overrides.csv and
lemma_override_exclusions.csv for rejected source links.
"""
import csv
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lemmatize import build_admitted, load_vocab, lemmatize  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
SRC = DATA / "kaikki_de.jsonl"
MAX_RANK = 5000
SAFE_HEADWORD_POS = {"adj", "adv", "conj", "det", "noun", "prep", "pron", "article"}
REF_WORD = re.compile(r"^[A-Za-zÄÖÜäöüßẞ]+(?:[-'][A-Za-zÄÖÜäöüßẞ]+)*$")
# This Kaikki entry is a known source error: trinkst is a form of trinken,
# not triften. Keep the anomaly visible and do not turn it into a card merge.
KNOWN_BAD_FORM_REFS = {
    ("trinkst", "triften"): "Kaikki source link conflicts with the German form",
}


def ref_headword(value):
    raw = str(value).strip()
    candidate = raw.split()[0] if raw else ""
    return candidate if REF_WORD.fullmatch(candidate) else None


def canonical_ref(values):
    """Choose one spelling deterministically for casefold-equivalent refs."""
    return min(values, key=lambda value: (
        0 if "ß" in value.lower() else 1,
        value.casefold(),
        value.lower(),
    )).lower()


def main():
    forms = []
    with open(DERIVED / "top_forms.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["rank"]) > MAX_RANK:
                break
            forms.append(row["form"])
    form_keys = {form.casefold() for form in forms}
    rank_of, count_of = load_vocab(DERIVED / "top_forms.csv")
    admitted = build_admitted(rank_of, count_of)
    base_lemmas = {
        form: lemmatize(form, rank_of, count_of, admitted, overrides={})[0]
        for form in forms
    }

    data = {}
    lexical_headwords = set()
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            word = str(entry.get("word", ""))
            key = word.casefold()
            has_real = False
            parsed_senses = entry.get("senses", [])
            for sense in parsed_senses:
                tags = set(sense.get("tags") or [])
                if "form-of" not in tags and "alt-of" not in tags and "morpheme" not in tags:
                    has_real = True
            if has_real:
                lexical_headwords.add(key)
            if key not in form_keys:
                continue
            item = data.setdefault(key, {"refs": set(), "invalid_refs": set(),
                                         "real": False, "pos": set()})
            item["pos"].add(entry.get("pos", ""))
            item["real"] = item["real"] or has_real
            for sense in parsed_senses:
                tags = set(sense.get("tags") or [])
                if "form-of" in tags:
                    for ref in sense.get("form_of", []):
                        if ref.get("word"):
                            parsed = ref_headword(ref["word"])
                            if parsed:
                                item["refs"].add(parsed)
                            else:
                                item["invalid_refs"].add(str(ref["word"]))

    rows = []
    exclusions = []
    for form in forms:
        current = base_lemmas.get(form, form)
        item = data.get(form.casefold())
        if not item:
            continue
        by_key = {}
        for ref in item["refs"]:
            by_key.setdefault(ref.casefold(), []).append(ref)
        refs = {key: canonical_ref(values) for key, values in by_key.items()}
        target = None
        source = None
        for ref in sorted(item["invalid_refs"]):
            exclusions.append({"form": form, "ref": ref, "reason": "invalid-single-word-reference"})
        if len(refs) == 1 and not item["real"]:
            candidate = next(iter(refs.values()))
            pair = (form.casefold(), candidate.casefold())
            if pair in KNOWN_BAD_FORM_REFS:
                exclusions.append({"form": form, "ref": candidate,
                                   "reason": KNOWN_BAD_FORM_REFS[pair]})
            elif candidate.casefold() not in lexical_headwords:
                exclusions.append({"form": form, "ref": candidate,
                                   "reason": "target-is-not-a-lexical-headword"})
            else:
                target = candidate
            source = "kaikki-form-of"
        elif (item["real"] and not item["refs"]
              and current.casefold() != form.casefold()
              and ((len(item["pos"]) == 1 and item["pos"] <= SAFE_HEADWORD_POS)
                   or (item["pos"] <= {"adv", "conj", "prep", "det", "pron", "article"}))):
            target = form.lower()
            source = "kaikki-headword"
        if target and target.casefold() != current.casefold():
            rows.append({"form": form, "lemma": target, "source": source,
                         "pos": ";".join(sorted(item["pos"]))})

    with open(DERIVED / "lemma_overrides.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["form", "lemma", "source", "pos"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with open(DERIVED / "lemma_override_exclusions.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["form", "ref", "reason"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(exclusions)
    print(f"lemma overrides: {len(rows)}; rejected refs: {len(exclusions)}")


if __name__ == "__main__":
    main()
