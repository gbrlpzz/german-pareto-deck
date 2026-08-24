# german-pareto-deck

A German Anki deck with high-frequency words and sentence patterns.

Status: **v0.3 release candidate**.

## Start here

1. Download `german-pareto-deck.apkg` from [Releases](https://github.com/gbrlpzz/german-pareto-deck/releases/latest).
2. In Anki, choose **File -> Import**.
3. Study **German Pareto::Core** first (1,313 word cards).
4. Add **German Pareto::Patterns** from day one (562 cards).
5. Add **German Pareto::Extension** when Core feels easy (1,247 word cards).

Cards carry tier, rank-band, pattern-group, and class tags. Suspend cards freely.

## Why this design

Isolated word lists teach poorly. Everyday language is concentrated in both frequent forms and
recurrent sentence patterns.

The word list uses German Tatoeba frequencies and a spoken-register OpenSubtitles anchor. The
steepest measured gains end near 2,000 forms. The 4,000-form cutoff stays the default. A larger
band is not shipped because its measured marginal gain is small for this deck.

The pattern layer uses the 505-item PHRASE List as a list-scale anchor. It favors spoken-German
frames, collocations, modal particles, and routines. Every selected pattern has an authentic
Tatoeba sentence.

Word cards use production. Pattern cards use cloze production. Routine and particle patterns
also have recognition cards.

## What is in v0.3

The release has **3,122 cards**:

- **2,560 word cards**: 1,313 Core and 1,247 Extension.
- **500 pattern cloze cards**. All selected patterns match an exemplar.
- **62 pattern recognition cards**: 42 routines and 20 modal-particle frames.
- **No audio**. The release is smaller and fully reproducible without platform-specific voices.
- **No raw corpora**. Source files stay out of git and are downloaded by the pipeline.

The word layer now uses 882 accepted Kaikki lemma overrides. Six unsafe or malformed source links
are rejected and recorded in `derived/lemma_override_exclusions.csv`. Rows with no usable dictionary
gloss are excluded and recorded in `derived/vocab_exclusions.csv`.

![Token coverage by form rank](docs/figures/fig1_coverage_curves.png)

*Figure 1. Token coverage by form rank on two corpora.*

![Marginal coverage](docs/figures/fig2_marginal_gains.png)

*Figure 2. Extra coverage per additional 500 forms.*

![Deck composition](docs/figures/fig3_deck_pattern_mix.png)

*Figure 3. Pattern mix from `derived/selection_summary.json`.*

## Reproduce

Download the raw sources first. They are not redistributed.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python src/pipeline.py fetch
.venv/bin/python src/pipeline.py fetch-kaikki       # about 1 GB
.venv/bin/python src/pipeline.py build
```

`build` runs the deterministic stages from `freq` through `plots`. It expects the Tatoeba and
Kaikki source caches to exist. For an explicit stage list, see
[docs/METHODOLOGY.md](docs/METHODOLOGY.md).

The optional Wiktionary REST fallback is slow and rate-limited:

```bash
.venv/bin/python src/pipeline.py glosses
```

Tests:

```bash
.venv/bin/python -m unittest test_pipeline test_deck test_glosses test_phase3 test_release -v
.venv/bin/python test_lemmatize.py
```

## Documents

| Document | Content |
|---|---|
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Method, data, decisions, and limits |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Completed work and next steps |
| [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) | Release changes |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | URLs, dates, checksums, and licenses |
| [docs/ANKIWEB.md](docs/ANKIWEB.md) | Copy and steps for an AnkiWeb listing |
| [docs/ZENODO.md](docs/ZENODO.md) | Deposit checklist and metadata |
| [docs/ZENODO_METADATA.json](docs/ZENODO_METADATA.json) | Prepared Zenodo metadata |
| [LICENSE_NOTE.md](LICENSE_NOTE.md) | Code, derived data, and upstream licenses |

## Repository layout

```
├── docs/       # method, provenance, release, and publication files
├── src/        # pipeline stages and deck builder
├── derived/    # tracked, inspectable artifacts
├── data/       # gitignored source cache
└── out/        # gitignored deck and publication bundle
```

## License

Code in `src/` is MIT. Generated lists and cards are derivatives of cited sources. Raw corpora are
not redistributed. See [LICENSE_NOTE.md](LICENSE_NOTE.md) and
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
