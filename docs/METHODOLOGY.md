# Methodology

Goal: an Anki deck teaching German through the Pareto-optimal set of words AND patterns,
with every number either measured here or cited. Non-goal: reading-literature coverage
(that needs 8,000–9,000 word families; out of scope).

## 0. Decisions at a glance

| # | Decision | Value | Status |
|---|---|---|---|
| D1 | Spoken-register proxy corpus | film-subtitle frequencies; Tatoeba as reproducible fallback | ADOPTED |
| D2 | Word deck size | core 2,000 lemmas + extension to 4,000 | ADOPTED |
| D3 | Pattern deck size | ~500 cards (min viable 300) | ADOPTED |
| D4 | Pattern class mix | see §4b table | ADOPTED |
| D5 | Card format | production cloze sentence; recognition reverse only for particles/routines | ADOPTED |
| D6 | Lemma handling | form-level lists + lemmatization pass; bias documented | PARTIAL |
| D7 | Licensing | code Apache-2.0; no raw-corpus redistribution; refetch instead | ADOPTED |

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
² `derived/coverage_curve.csv`, reproducible via `src/pipeline.py freq`.

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

German inflection means ~1.5–2 forms per frequent lemma, so form-rank overstates lemma count.
Form-level 85–88% ≈ roughly 90% at lemma level for the same material. Cross-checking with
Adolphs & Schmitt (spoken families): the 95% line lands between 3,000 and 4,000 lemmas.
Beyond 5,000 lemmas buys under 3 percentage points — parked as optional extension, not built.

## 4b. Why ~500 patterns, and which

No canonical constant exists; the strongest list-scale anchor is the 505-item PHRASE List,
and bundle research shows ROI peaking in dialogue. Class mix adopted for the German deck:

| Class | ~count | Example |
|---|---:|---|
| Perfekt aux frames (default spoken past) | 120 | *hab ich … gemacht* |
| Separable-verb Satzklammer frames | 100 | *rufst du mich … an?* |
| Verb+noun / prep collocations, Funktionsverbgefüge | 90 | *eine Entscheidung treffen* |
| Connectors + modal particles (*ja, doch, mal, halt*) | 70 | *das ist ja interessant* |
| Conversational routines | 50 | *es tut mir leid* |
| High-frequency lexical bundles | 70 | *ich weiß nicht, ob …* |

## 5. Card specification

Default: German sentence, pattern cloze-deleted, **production** answer; back shows the completed
sentence, a short EN gloss of the chunk, and (when available) the EN sentence translation.
Recognition-reverse cards reserved for modal particles and routines. Every card carries exactly
one authentic Tatoeba example sentence. Tags encode tier + pattern class for suspend/skip control.

## 6. Pipeline

fetch → freq → patterns → sentences → deck (see README quickstart). Each stage writes
inspectable artifacts; raw corpora are never committed, only re-fetched with recorded sha256.

## 7. Limitations

- Form-level curves approximate lemma coverage; lemmatization pass pending (D6).
- Tatoeba is translated prose-flavored dialogue — good, imperfect speech proxy.
- 500-pattern scale extrapolates from English list research (PHRASE List), acknowledged medium confidence.
- Sentence selection optimizes length/naturalness heuristics; no audio.

## 8. Changelog

- v0.1 — methodology fixed; both research reports merged; empirical curves measured.

## 9. Figures

Figure 1 (`docs/figures/fig1_coverage_curves.png`) visualizes the measured curves in §2.
Figure 2 (`docs/figures/fig2_marginal_gains.png`) visualizes the marginal-return argument
in §4a. Regenerate with `.venv/bin/python src/plots.py`; anchor values for the OpenSubtitles
series live in `derived/subtitles_curve.csv`.
