# Methodology

Goal: teach German with high-frequency words and recurring sentence patterns.
Reading-register coverage is out of scope. That needs a separate corpus and a larger vocabulary.

## 1. Decisions at a glance

| ID | Decision | Value | Basis |
|---|---|---:|---|
| D1 | Spoken-register proxy | OpenSubtitles frequency anchor; Tatoeba fallback | literature + data |
| D2 | Word bands | top 2,000 forms for Core; ranks 2,001-4,000 for Extension | literature + data |
| D3 | Pattern size | 500 cards | PHRASE List scale |
| D4 | Pattern mix | source candidate pools with documented redistribution | literature + data |
| D5 | Card format | production word cards; cloze patterns; recognition only for routines and particles | learning design |
| D6 | Lemmas | conservative rules plus validated Kaikki links | implementation |
| D7 | Licensing | MIT code; no raw-corpus redistribution | policy |
| D8 | Threshold policy | every constant is data-derived, literature-based, or marked heuristic | owner directive |

## 2. Terms

- **token** — one running word instance.
- **form/type** — one surface shape, such as *geht* or *ging*.
- **lemma** — a citation form, such as *gehen*.
- **pattern/chunk** — a recurring multiword unit, frame, collocation, or routine.
- **coverage** — the share of corpus tokens covered by the top-*k* items.

## 3. Measured curves

| top-k forms | OpenSubtitles-2016 German | Tatoeba German in this repo |
|---:|---:|---:|
| 1,000 | 79.9% | 77.2% |
| 2,000 | 85.3% | 83.5% |
| 3,000 | 88.2% | 86.5% |
| 4,000 | — | 88.5% |
| 5,000 | 91.3% | 89.9% |
| 10,000 | 94.8% | 93.5% |

The Tatoeba values come from `derived/top_forms.csv`. The OpenSubtitles values are the
measured anchor in `derived/subtitles_curve.csv`. Tatoeba is smaller and has more translated
prose and proper-name noise. The two curves are treated as a bracket, not as one exact estimate.

## 4. Evidence anchors

- Subtitle frequency predicts everyday spoken processing — Brysbaert et al. 2011.
- Spoken corpora place 2,000 families below 95% and 3,000 families near the 95% range — Adolphs & Schmitt 2003.
- 95% is a minimal context-guessing threshold; 98% is a stronger unassisted target — Laufer 1989; Laufer & Ravenhorst-Kalovski 2010.
- Written coverage needs more families than spoken coverage — Nation 2006.
- High-frequency families should be learned before mid-frequency bands — Schmitt & Schmitt 2010.
- German frequency work uses a 5,000-lemma reference ceiling — Tschirner & Möller.
- About 55% of discourse is formulaic — Erman & Warren 2003; lexicalized sentence stems — Pawley & Syder 1983.
- PHRASE List: 505 frequent non-transparent multiword expressions — Martinez & Schmitt 2012.
- Conversation has dense recurring sequences — Biber et al. 1999; Biber & Barbieri 2007.
- Production and contextual retrieval support durable learning — Webb 2009; Nakata 2017.

## 5. Vocabulary selection

The corpus supplies the rank and count. The literature supplies the 2,000/4,000 band design.
The optional 4,001-5,000 experiment is not shipped: it added limited measured coverage relative
to its extra cards. The release keeps the 4,000-form default.

The v0.3 build has 2,560 word cards:

- Core: 1,313 cards after grouping and exclusions.
- Extension: 1,247 cards after grouping and exclusions.
- 28 rows with no usable dictionary gloss are excluded. Every row is recorded in
  `derived/vocab_exclusions.csv`.

## 6. Lemma handling

The base pass is a conservative rule-based lemmatizer in `src/lemmatize.py`. It protects
admitted headwords, handles common conjugation and declension shapes, and keeps ambiguous
homographs separate.

The Kaikki pass in `src/lemma_overrides.py` adds a link only when:

1. the surface entry has no competing lexical sense;
2. it points to one reference;
3. the reference is a single-word, lexical headword in the extract; and
4. the reference passes deterministic spelling selection.

The pass accepts 882 overrides. Six malformed or unsafe links are rejected and recorded in
`derived/lemma_override_exclusions.csv`. The known `trinkst -> triften` source error is rejected.
A malformed ref such as `verhalten he/she/it behaves` is reduced to the single headword
`verhalten`, not copied as a lemma.

Casefold collisions use a deterministic choice that prefers a German `ß` spelling when the
extract offers both `ß` and `ss`. This avoids hash-seed-dependent builds.

## 7. Pattern selection

The PHRASE List gives the 500-card scale. Candidate groups use corpus frequency, association
scores, minimum observations, and the D8 registry. Sentence examples use Tatoeba. The sentence
length window is the corpus interquartile range `[5, 9]`. All 500 selected patterns match.

The deck has 500 cloze cards and 62 recognition cards. Recognition cards cover 42 routines and
20 modal-particle frames.

## 8. Card specification

Word cards show an English gloss and a blanked German example on the front. The back shows the
German form, full sentence, gloss, and English translation when available.

Pattern cards delete the selected pattern inside one authentic German sentence. The back shows
the full cloze sentence and translation. Every pattern has one exemplar.

The release has no audio. This is intentional. The native macOS voice path was not included
because it adds platform-specific files and a slow build without enough benefit for this release.

## 9. Reproducible pipeline

Raw sources must be present in `data/`. Run:

```text
fetch -> fetch-kaikki -> build
```

`build` runs:

```text
freq -> patterns -> select -> lemma-overrides -> lemmatize -> words
-> lemma-glosses -> filter-vocab -> lemma-glosses -> sentences
-> translations -> deck -> plots
```

The translation rule is shortest English text. Equal-length candidates use lexicographic order.
The deck builder fixes its build timestamp and normalizes APKG ZIP metadata. Two builds from the
same inputs are byte-identical.

## 10. D8 selection registry

Every constant has one stated basis:

| Constant | Value | Basis and reason |
|---|---:|---|
| Collocation admission | t ≥ 2 | literature convention for association measures |
| Bundle minimum | observations ≥ 4 | stability floor for the t statistic |
| Frame minimum | observations ≥ 10 | higher floor for sparse two-slot frames |
| Function-word set | 184 tokens | enumerated linguistic closed class |
| Pattern total | 500 | PHRASE List scale |
| Bundle length | at least 3 tokens | PHRASE List style multiword unit |
| Exemplar length | IQR `[5, 9]` | data-derived from Tatoeba |
| Word bands | 2,000 / 4,000 | literature plus measured curves |
| Translation | shortest; lexical tie-break | card fit plus deterministic rule |
| Proper-name blocklist | 20 tokens | heuristic manual review of recurring name bundles |
| No-gloss exclusion | no usable lemma/form gloss | data-derived quality gate |
| Kaikki anomaly list | 6 rejected refs | source validation; explicit audit trail |
| ZIP timestamp | fixed build value | reproducibility engineering |

The pattern allocation and all candidate shortfalls are inspectable in
`derived/selection_summary.json`.

## 11. v0.3 build results

| Artifact | Count | Notes |
|---|---:|---|
| Total Anki cards | 3,122 | 2,560 word + 500 cloze + 62 recognition |
| Word cards | 2,560 | 1,313 Core + 1,247 Extension |
| Pattern cloze cards | 500 | 500/500 matched |
| Pattern recognition cards | 62 | 42 routines + 20 particle frames |
| Lemma overrides | 882 | validated Kaikki links |
| Rejected lemma refs | 6 | recorded source anomalies |
| Excluded vocabulary rows | 28 | no usable dictionary gloss |
| Word gloss rows | 2,560/2,560 | no blank word-card glosses |
| Translated sentence IDs | 2,596/3,966 | untranslated cards keep German text |
| Tests | 25 unittest + lemmatizer checks | all pass |

## 12. Limits

- Coverage curves are form-level. The lemma pass remains conservative.
- Tatoeba has translation and register bias.
- The PHRASE List is not German-specific.
- The deck has no audio and no reading-register corpus.
- Raw corpora are not redistributed.
