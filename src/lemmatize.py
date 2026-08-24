#!/usr/bin/env python3
"""Rule-based conservative German lemmatizer for derived/top_forms.csv (D6 pass).

Implements METHODOLOGY.md D6 (lemmatization pass over form-level lists) under the
D8 discipline (src/patterns.py: no arbitrary thresholds; every constant carries a
linguistic justification). Reads derived/top_forms.csv, writes derived/lemma_groups.csv
with columns: form,rank,lemma,group_id,method. group_id == lemma (the shared headword
string identifies the group deterministically).

Rules (applied in this order; first hit wins; anything unmatched stays
lemma=form, method='ungrouped' -- D-rule L7):

L0  IRREGULAR_PARTICIPLES + SUPPLETIVE_FINITE  closed dictionaries of
    strong/suppletive forms whose lemma CANNOT be recovered by suffix surgery.
    Participles: German Ablaut changes the stem unpredictably (gegangen->gehen,
    gewesen->sein, gebracht->bringen ...). Finite forms of the suppletive verbs
    sein/haben/werden/hassen likewise alternate stems (bin-/war-, hab-/hat-,
    werd-/wur-, hasst with ss-doubling), so their highest-frequency shapes are
    mapped by dictionary knowledge, not thresholds. Ambiguous forms are
    deliberately excluded (gestanden -> stehen OR gestehen) per L7.
    whose infinitive CANNOT be recovered by suffix surgery, because German Ablaut
    changes the stem vowel/consonants unpredictably (gegangen->gehen, gewesen->sein,
    gebracht->bringen ...). Dictionary knowledge, not a threshold; each entry is one
    standard dictionary correspondence and is kept only if the target infinitive is
    attested in the vocabulary. Ambiguous forms are deliberately excluded
    (gestanden -> stehen OR gestehen) per L7.

L1  ge-participles (circumfix ge-...-t/-en). For form = ge + rest: weak participles
    recover the infinitive as rest-minus-{en,t,et} + '-en' (gemacht->machen,
    gearbeitet->arbeiten); rest itself may already be the infinitive
    (gesehen->sehen, getragen->tragen). Umlauts need no folding here because the
    participle preserves the stem vowel (hören->gehört->hören).

L2  Verb finite inflection. strip suffix in {ende,end,est,et,st,t,e} (longest first)
    and append '-en': geht/gehe/gehst/gehend->gehen. Suffix set = 1sg/2sg/3sg
    agreement + present-participle endings; '-en' itself is excluded because the
    infinitive is the citation form, not a derived shape.

L3  Target admission gate (finite-agreement evidence). An infinitive candidate c is
    accepted only if some OTHER vocabulary form attests finite verbal morphology for
    it: f = stem + {t,st,et,est} with stem+'en' == c. Bare existence of c is not
    evidence (jahre/seite/augen otherwise misfire onto jahren/seiten/augen).
    Twin veto: c is rejected when its n-less twin c[:-1] is attested and OUTNUMBER
    it (einen < eine, hasen < hase, sollten < sollte): an infinitive is the
    frequency-dominant member of its paradigm, so a more frequent n-less sibling
    marks c as an inflected non-verbal form. Measured corpus dominance, not a rank
    cutoff.

L4  Adjective/adverb declension (superset rule). form = base + {e,en,er,em,es} with
    base attested: guten/gute->gut, kleinen->klein. The same suffixes cover noun
    dative/genitive shapes (hauses->haus, jahren->jahr) and article/possessive
    declension (einen/einem/einer->ein); outcome is identical whichever analysis is
    true, so no POS guessing is attempted.

L5  Noun plural -e/-en/-er/-s, singular attested (frauen->frau, kinder->kind,
    autos->auto). Shared suffixes with L4 are consumed by L4 first; L5 contributes
    the -s class. Phonotactic guard: bare -s is impossible on bases ending in
    s/beta/z/x (German uses -es there), which blocks muss->mus-type artifacts.

L6  Guards, all closed-class linguistic knowledge (no thresholds):
    MIN_STEM = 3      German content stems are >= 3 graphemes; blocks degenerate
                      strips like ende->w(en), ehe->eh.
    CLOSED_CLASS_BASES = {sich, seit, schon, sehr, dann, mal}
                      pronoun/particle/preposition/adverb strings that never host
                      adjectival or nominal inflection; every observed collision was
                      a different lexeme (sicher->sich, seite->seit, maler->mal).
    EXCEPTION_FORMS = {dass, etwas, unser, ihnen, heute, wegen}
                      surface homographs whose ending is NOT inflection: dass/das is
                      orthographic; etwas is indeclinable; unser/ihnen belong to
                      suppletive pronoun paradigms; the -e of heute and the -en of
                      wegen are lexical.

L7  Conservatism. Never merge across word classes; ambiguous or unknown forms stay
    lemma=form, method='ungrouped'. Exact string matching only -- umlaut alternations
    (maenner, groesser) and preterite/vowel-change forms outside L0/L1 stay
    ungrouped by construction.

Known residual imperfections (accepted, documented):
- Some groups are keyed by clipped or superlative stems (jed<-jede..., bess<-besser...,
  erst<-erste...): membership is correct (one paradigm), headword spelling is not
  normalized without a POS resource.
- Simple-past 1sg/3sg forms sometimes group under the past-plural shape
  (hatte->hatten) when the twin veto rejects the past plural as a target; families
  stay cohesive, headwords imperfect.
- war/wart/warst cluster under waren; aufs/fuers-class contractions group under
  their preposition.

Output: derived/lemma_groups.csv. If present, derived/lemma_overrides.csv
adds safe dictionary links before the rule set runs.
"""
import csv
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOP_FORMS = ROOT / "derived" / "top_forms.csv"
OUT = ROOT / "derived" / "lemma_groups.csv"
OVERRIDES = ROOT / "derived" / "lemma_overrides.csv"

VOCAB_VERB_MAX_RANK = 15000   # D8: infinitives beyond the top 15k forms sit below
                              # 95.17% cumulative token share where hapax/proper-noun
                              # noise dominates; capping bounds spurious stem hits
MIN_STEM = 3                  # see L6

VERB_SUFFIXES = ("ende", "end", "est", "et", "st", "t", "e")     # longest-first
FINITE_SUFFIXES = ("est", "st", "et", "t")                       # L3 evidence set
ADJ_SUFFIXES = ("en", "er", "em", "es", "e")                     # L4, longest-first
PLURAL_SUFFIXES = ("en", "er", "e", "s")                         # L5
NO_BARE_S_STEM = ("s", "ß", "z", "x")                       # L5 phonotactics

CLOSED_CLASS_BASES = frozenset({"sich", "seit", "schon", "sehr", "dann", "mal"})
EXCEPTION_FORMS = frozenset({
    "dass", "etwas", "unser", "ihnen", "heute", "wegen",
    "nichte", "nichten",   # die Nichte (niece), not an inflection of nicht
})

IRREGULAR_PARTICIPLES = {
    "gegangen": "gehen", "gewesen": "sein", "geworden": "werden",
    "worden": "werden", "geblieben": "bleiben", "gebracht": "bringen",
    "gekannt": "kennen", "gewusst": "wissen", "genommen": "nehmen",
    "getan": "tun", "gesungen": "singen", "getrunken": "trinken",
    "geschrieben": "schreiben", "gesprochen": "sprechen",
    "geschlagen": "schlagen", "getroffen": "treffen", "geworfen": "werfen",
    "gesessen": "sitzen", "gelegen": "liegen", "geholfen": "helfen",
}

# Suppletive finite forms (L0): stem-alternating paradigms of the three
# irregular auxiliaries plus the ss-doubling verb hassen. Every entry is a
# standard dictionary correspondence; targets are verified against the vocab.
SUPPLETIVE_FINITE = {
    "bin": "sein", "bist": "sein", "ist": "sein", "sind": "sein",
    "seid": "sein", "war": "sein", "warst": "sein", "wart": "sein",
    "waren": "sein", "wäre": "sein", "wären": "sein",
    "hab": "haben", "hast": "haben", "hat": "haben", "habt": "haben",
    "hatte": "haben", "hatten": "haben", "hattest": "haben",
    "habe": "haben",
    "hattet": "haben", "hätte": "haben", "hätten": "haben",
    "wird": "werden", "wirst": "werden", "ward": "werden",
    "wurde": "werden", "wurden": "werden", "würde": "werden",
    "würden": "werden", "hasst": "hassen",
}


def load_vocab(path):
    """Read top_forms.csv -> (rank_of, count_of) dicts keyed by form."""
    rank_of, count_of = {}, {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            form = row["form"]
            rank_of[form] = int(row["rank"])
            count_of[form] = int(row["count"])
    return rank_of, count_of


def build_admitted(rank_of, count_of):
    """L3: infinitives with finite-agreement evidence, minus twin-veto losers."""
    vocab = set(rank_of)
    evidence = defaultdict(set)
    for form in vocab:
        if form in SUPPLETIVE_FINITE:
            continue
        for suf in FINITE_SUFFIXES:
            if form.endswith(suf) and len(form) - len(suf) >= MIN_STEM:
                cand = form[: -len(suf)] + "en"
                r = rank_of.get(cand)
                if cand != form and r is not None and r <= VOCAB_VERB_MAX_RANK:
                    evidence[cand].add(form)
    admitted = {}
    for cand, att in evidence.items():
        twin = cand[:-1]                       # n-less sibling (L3 twin veto)
        if twin in vocab and twin != cand and count_of[twin] > count_of[cand]:
            continue
        admitted[cand] = sorted(att)[0]
    return admitted


def load_overrides(path=OVERRIDES):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return {row["form"]: row["lemma"] for row in csv.DictReader(fh)}


def lemmatize(form, rank_of, count_of, admitted=None, irregular=None, overrides=None):
    """Return (lemma, method) for one form. Pure and deterministic."""
    if admitted is None:
        admitted = build_admitted(rank_of, count_of)
    if irregular is None:
        vocab = set(rank_of)
        irregular = {k: v for k, v in IRREGULAR_PARTICIPLES.items() if v in vocab}
        irregular.update({k: v for k, v in SUPPLETIVE_FINITE.items() if v in vocab})
    if overrides is None:
        overrides = {}

    if form in overrides:
        return overrides[form], "dictionary"
    if form in EXCEPTION_FORMS or len(form) < MIN_STEM:
        return form, "ungrouped"

    # L0 irregular / suppletive forms (dictionary knowledge outranks surgery)
    if form in irregular:
        return irregular[form], "participle"

    # L1 ge-participle
    if len(form) >= 6 and form.startswith("ge"):
        rest = form[2:]
        if rest.endswith("en") and rest in admitted:
            return rest, "participle"
        if rest.endswith("et") and rest[:-2] + "en" in admitted:
            return rest[:-2] + "en", "participle"
        if rest.endswith("t") and rest[:-1] + "en" in admitted:
            return rest[:-1] + "en", "participle"

    # L2 verb finite inflection onto admitted infinitives
    for suf in VERB_SUFFIXES:
        if form.endswith(suf) and len(form) - len(suf) >= MIN_STEM:
            cand = form[: -len(suf)] + "en"
            if cand != form and cand in admitted:
                return cand, "verb"

    # Attested headwords are never stripped further (protects gehen/haben/sein).
    if form in admitted or form in irregular.values():
        return form, "ungrouped"

    vocab = rank_of
    # L4 adjective/adverb declension (superset: covers noun dat/gen shapes too)
    for suf in ADJ_SUFFIXES:
        if form.endswith(suf) and len(form) - len(suf) >= MIN_STEM:
            base = form[: -len(suf)]
            if base in vocab and base not in CLOSED_CLASS_BASES:
                return base, "declension"

    # L5 noun plural
    for suf in PLURAL_SUFFIXES:
        if form.endswith(suf) and len(form) - len(suf) >= MIN_STEM:
            base = form[: -len(suf)]
            if suf == "s" and base.endswith(NO_BARE_S_STEM):
                continue
            if base in vocab and base not in CLOSED_CLASS_BASES:
                return base, "plural"

    return form, "ungrouped"


def main():
    rank_of, count_of = load_vocab(TOP_FORMS)
    admitted = build_admitted(rank_of, count_of)
    vocab = set(rank_of)
    irregular = {k: v for k, v in IRREGULAR_PARTICIPLES.items() if v in vocab}
    irregular.update({k: v for k, v in SUPPLETIVE_FINITE.items() if v in vocab})
    overrides = load_overrides()

    rows_out = []
    with open(TOP_FORMS, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            form = row["form"]
            lemma, method = lemmatize(form, rank_of, count_of, admitted, irregular, overrides)
            rows_out.append((form, row["rank"], lemma, lemma, method))

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["form", "rank", "lemma", "group_id", "method"])
        w.writerows(rows_out)

    grouped = sum(1 for r in rows_out if r[4] != "ungrouped")
    tokens = sum(count_of[r[0]] for r in rows_out)
    tok_grouped = sum(count_of[r[0]] for r in rows_out if r[4] != "ungrouped")
    print(f"wrote {OUT} rows={len(rows_out)}")
    print(f"grouped types: {grouped}/{len(rows_out)} ({100*grouped/len(rows_out):.2f}%)")
    print(f"grouped tokens: {tok_grouped}/{tokens} ({100*tok_grouped/tokens:.2f}%)")


if __name__ == "__main__":
    main()
