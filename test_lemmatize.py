#!/usr/bin/env python3
"""Plain-assert tests for src/lemmatize.py (run: .venv/bin/python test_lemmatize.py)."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from lemmatize import load_vocab, build_admitted, lemmatize  # noqa: E402

RANK, COUNT = load_vocab(ROOT / "derived" / "top_forms.csv")
ADM = build_admitted(RANK, COUNT)
VOCAB = set(RANK)


def lem(form):
    return lemmatize(form, RANK, COUNT, ADM)[0]


def method(form):
    return lemmatize(form, RANK, COUNT, ADM)[1]


# 1. gehen-conjugation set collapses to gehen
for f in ["gehe", "geht", "geht", "gehst", "gehend", "gegangen"]:
    assert lem(f) == "gehen", (f, lem(f))
assert lem("gehen") == "gehen"          # infinitive itself stays the headword
assert method("geht") == "verb"
assert method("gegangen") == "participle"

# 2. adjective declension
assert lem("guten") == "gut"
assert lem("gute") == "gut"
assert method("guten") == "declension"

# 3. noun plural with attested singular
assert lem("frauen") == "frau"

# 4. weak ge-participle
assert lem("gemacht") == "machen"
assert method("gemacht") == "participle"

# 5. 'abend' stays ungrouped
assert lem("abend") == "abend" and method("abend") == "ungrouped"

# 6. unknown form stays ungrouped
assert lem("qxyzblor") == "qxyzblor" and method("qxyzblor") == "ungrouped"

# --- additional conservative-behaviour guards -------------------------------
assert lem("dass") == "dass"            # orthographic homograph of das
assert lem("etwas") == "etwas"          # indeclinable
assert lem("unser") == "unser"          # suppletive possessive paradigm
assert lem("ihnen") == "ihnen"          # pronoun paradigm, not ihn+en
assert lem("seite") != "seit"           # preposition base is blocked
assert lem("sicher") != "sich"          # pronoun base is blocked
assert lem("muss") != "mus"             # bare -s impossible on s-final stem
assert lem("eine") == "ein"             # article declension still works
assert lem("arbeiten") == "arbeiten"    # admitted headword protected from L4
assert lem("gearbeitet") == "arbeiten"  # ge...et participle
assert lem("autos") == "auto"           # -s plural with attested singular
assert lem("kinder") == "kind"          # -er plural
assert lem("hauses") == "haus"          # genitive shape via declension rule
assert lem("geht") == "gehen" and lem("machst") == "machen"

print("all tests passed")
