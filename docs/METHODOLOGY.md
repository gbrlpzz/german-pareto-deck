# Methodology

Goal: teach German with high-frequency words and patterns.
Reading-literature coverage is out of scope. That needs 8,000-9,000 word families.

## 0. Decisions at a glance

| # | Decision | Value | Status |
|---|---|---|---|
| D1 | Spoken-register proxy corpus | film-subtitle frequencies; Tatoeba as reproducible fallback | ADOPTED |
| D2 | Word deck size | core 2,000 lemmas + extension to 4,000 | ADOPTED |
| D3 | Pattern deck size | ~500 cards (min viable 300) | ADOPTED |
| D4 | Pattern class mix | see §4b table | ADOPTED |
| D5 | Card format | production cloze sentence; recognition reverse only for particles/routines | ADOPTED |
| D6 | Lemma handling | rule-based lemmatizer (`src/lemmatize.py`), 24.5% of types grouped, suppletive paradigms via closed dictionary, conservative by design | IMPLEMENTED |
| D7 | Licensing | code MIT; no raw-corpus redistribution; refetch instead | ADOPTED |

## 1. Terms

- **token** — running word instance. **form/type** — one inflected shape (*geht*, *ging*).
- **lemma** — headword (*gehen*). **family** — lemma + derivations.
- **coverage** — share of tokens in a corpus covered by the top-*k* items.
- **pattern / chunk** — recurring multiword sequence functioning as a unit
  (lexical bundle, collocation frame, or routine).

## 2. Measured curves (form-level token coverage)

| top-k forms | OpenSubtitles-2016 DE (95.9M tokens)¹ | Tatoeba deu, this repo (6.06M tokens, 778,331 sentences)² |
|---:|---:|---:|
| 1,000 | 79.9% | 77.2% |
| 2,000 | 85.3% | 83.5% |
| 3,000 | 88.2% | 86.5% |
| 4,000 | — | 88.5% |
| 5,000 | 91.3% | 89.9% |
| 10,000 | 94.8% | 93.5% |

¹ measured directly from the primary FrequencyWords dataset during research for this project.
² `derived/top_forms.csv`, produced by `src/pipeline.py freq`.

Tatoeba reads lower at equal rank (translated, noun-heavier register; smaller corpus ⇒ more
proper-noun/hapax noise). Subtitles remain the better speech proxy; the two curves bracket reality.

## 3. Literature anchors

- Subtitle frequency best predicts everyday spoken processing — Brysbaert et al. 2011 (SUBTLEX-DE).
- Spoken corpora: 2,000 word families <95% (~94.8%), 3,000 families ~96% — Adolphs & Schmitt 2003, *Applied Linguistics* 24(4).
- 95% = minimal comprehension threshold (context guessing feasible); 98% = unassisted — Laufer 1989; Laufer & Ravenhorst-Kalovski 2010.
- 98% spoken needs 6,000–7,000 families; written 8,000–9,000 — Nation 2006, *CMLR* 63(1).
- Learn top 2,000–3,000 families before mid-frequency bands — Schmitt & Schmitt 2010, *ITL*.
- German reference ceiling: 5,000 lemmas — Tschirner & Möller, *A Frequency Dictionary of German* (Routledge/Leipzig).
- ~55% of discourse is formulaic (58.6% spoken) — Erman & Warren 2003, *Text* 23(1); lexicalized sentence stems — Pawley & Syder 1983.
- PHRASE List: 505 most frequent non-transparent MWEs, nearly all built from top-1,000 words — Martinez & Schmitt 2012, *Applied Linguistics* 33(3).
- Conversation is the densest register for recurring sequences — Biber et al. 1999; Biber & Barbieri 2007.
- Production practice wins in BOTH directions — Webb 2009, *RELC* 40; contextualized/cloze retrieval beats isolated pairs (2023 study); items need repeated retrievals — Nakata 2017, *SSAL* 39.

## 4a. Why 2,000 + 4,000 words

German inflection adds ~1.5-2 forms per frequent lemma. Form-rank therefore overstates
lemma count. Form-level 85-88% is roughly 90% at lemma level for the same material.
Adolphs & Schmitt put the spoken 95% line at 3,000-4,000 families. We set the cutoff there.
Beyond 5,000 lemmas buys under 3 percentage points. That band stays an optional extension.

## 4b. Why ~500 patterns, and which

No canonical constant exists. The strongest list-scale anchor is the 505-item PHRASE List.
Bundle research shows the highest ROI in dialogue. We adopt ~500 cards with this class mix:

| Class | ~count | Example |
|---|---:|---|
| Perfekt aux frames (default spoken past) | 120 | *hab ich … gemacht* |
| Separable-verb Satzklammer frames | 100 | *rufst du mich … an?* |
| Verb+noun / prep collocations, Funktionsverbgefüge | 90 | *eine Entscheidung treffen* |
| Connectors + modal particles (*ja, doch, mal, halt*) | 70 | *das ist ja interessant* |
| Conversational routines | 50 | *es tut mir leid* |
| High-frequency lexical bundles | 70 | *ich weiß nicht, ob …* |

## 5. Card specification

Word cards use English cues and production blanks. Pattern cards delete the pattern inside a
German sentence. The learner produces the answer. Routine and particle cards also have a
recognition card. The back shows the full sentence, a short English gloss, and the English
translation when available. Every card uses one authentic Tatoeba sentence. Tags encode tier
and pattern class.

## 6. Pipeline

The stages are `fetch`, `freq`, `patterns`, `select`, `lemmatize`, `words`, `sentences`,
`translations`, `fetch-kaikki`, `lemma-glosses`, `deck`, and `plots`. Each stage writes an
inspectable artifact. Raw sources stay in `data/` and are not committed. Downloads print a
sha256 checksum.

## 7. Limitations

- Coverage curves are form-level. The rule-based lemmatizer leaves some homographs and
  irregular forms unresolved. Kaikki form-of links improve glosses but do not change grouping.
- Tatoeba is translated prose-flavored dialogue. It is a useful but imperfect speech proxy.
- The 500-pattern scale uses the PHRASE List as an anchor. The list is not German-specific.
- Sentence selection uses corpus length and frequency. The deck has no audio.

## 8. Changelog

- v0.1 - methodology fixed; empirical curves measured; first deck released.
- v0.2 - all 500 patterns receive cloze cards; 62 recognition cards added; lemma-first
  glosses added; reproducibility stages wired.

## 9. Figures

Figure 1 (`docs/figures/fig1_coverage_curves.png`) visualizes the measured curves in §2.
Figure 2 (`docs/figures/fig2_marginal_gains.png`) visualizes the marginal-return argument
in §4a. Regenerate with `.venv/bin/python src/plots.py`; anchor values for the OpenSubtitles
series live in `derived/subtitles_curve.csv`.


## 10. Decision D8 — no arbitrary thresholds (owner directive)

This applies to every selection in this repo, not only vocabulary size. Each constant is
one of three kinds:

- **(a) DATA-DERIVED** - computed by a stated formula from the corpus at run time.
- **(b) LITERATURE** - anchored to a cited source.
- **(c) HEURISTIC** - flagged as such, with rationale and observed effect.

### Selection registry

| Constant | Value | Type | Justification |
|---|---|---|---|
| Collocation admission | t ≥ 2 | LIT | conventional significance for association measures (Evert 2004; Church et al. 1991) |
| Bundle min observations | O ≥ 4 | LIT | stability floor of the t statistic (t ≤ √O as E → 0) |
| Frame min observations | O ≥ 10 | LIT+DATA | same statistic; higher floor for sparse two-slot co-occurrences |
| Function-word set | 184 tokens | DATA | linguistically defined closed class (articles, pronouns, prepositions, conjunctions, particles, auxiliaries), enumerated — not a rank cutoff |
| Proper-name blocklist | 20 tokens | HEURISTIC | manual review of top bundles; Tatoeba name-factory tokens ("Tom und Maria …") |
| Exemplar sentence window | IQR [5, 9] | DATA | the corpus's own interquartile sentence-length range, computed at run time |
| Pattern total | 500 | LIT | PHRASE-List scale (Martinez & Schmitt 2012); = D3 |
| Group targets | 50/120/100/90/70/70 | LIT | research-report reasoned mix; = D4 |
| Bundle length | n ≥ 3 tokens | LIT | listable multiword units; PHRASE-List median length 3 |
| Shortfall redistribution | ∝ D4 targets | RULE | groups with unavailable candidates release their deficit to surplus groups proportionally |
| Within-group class split | ∝ availability | DATA | e.g. perfekt/modal split 103/43 follows observed candidate pools |
| Rank within class | corpus frequency | GOAL | deck goal is coverage; significance already guaranteed at admission |
| Funktionsverbgefüge shape guards | len ≤ 9, no *ge-* | HEURISTIC | prevents *Haltestelle*→"halt" and *gebrochen*→"geb" stem collisions |
| Word cutoffs | 2,000 / 4,000 | LIT+DATA | = D2 |
| Translation choice | shortest per sentence | RULE | card fit |
| EN glosses | Kaikki lemma-first; form-of and form fallbacks; 2,937/2,963 rows | NOTE | quality enhancement, not a selection threshold |

Observed redistribution (v0.1): one move of 78 slots, funkverbgefüge (20 available of 90)
and routine (42 of 50) shortfalls absorbed by perfekt/modal, separable, particle/connector,
bundle — trace in `derived/selection_summary.json`.


## 11. Build results (v0.2)

| Artifact | Count | Notes |
|---|---:|---|
| Total Anki cards | 3,525 | 2,963 word + 500 pattern cloze + 62 recognition |
| Word cards | 2,963 | 1,507 core + 1,456 extension |
| Pattern cloze cards | 500 | all selected patterns have an exemplar; 0 cloze skips |
| Pattern recognition cards | 62 | 42 routines + 20 particle frames |
| Translated sentence IDs | 2,836/4,348 | 65.2%; untranslated cards keep the German sentence |
| Lemma gloss rows | 2,937/2,963 | Kaikki extract; form-of, alias, and two documented phrase fallbacks |
| Word cards without a gloss | 26 | mostly names or corpus-specific items |
| Tests | OK | pipeline, cloze matcher, and lemmatizer tests |

Known limitations: the word grouping remains rule-based; some forms use a clipped stem or
remain separate from their citation lemma. The source corpora are not redistributed. Tatoeba
has register and translation bias. The deck has no audio.
