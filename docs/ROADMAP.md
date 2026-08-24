# Roadmap

Prioritized follow-ups, each tied to a documented limitation (see
[METHODOLOGY.md §7/§11](METHODOLOGY.md)). Nothing here blocks daily use of v0.1.

## v0.2 — card quality
- Punctuation-tolerant cloze matching to recover the 39 skipped patterns.
- Lemma-level English glosses from a curatable dictionary source (current: form-level Wiktionary best-effort).
- Recognition reverses for all modal-particle and routine cards.

## v0.3 — vocabulary depth
- Optional extension band: forms 4,001–5,000 (documented <3% marginal coverage).
- Lemmatizer: POS-aware disambiguation of residual homograph merges (~0.3%); preterite vowel-change forms (ging, kam, nahm).
- Audio: TTS for example sentences.

## v0.4 — coverage & maintenance
- Reading-register companion deck (8,000–9,000 word families; Nation 2006).
- Corpus refresh pipeline (re-run `fetch` annually; curves and selections regenerate).
- Course-alignment tags (A1–C1).

## Infrastructure
- GitHub Actions CI: run tests on push, rebuild deck artifact on tag.
- AnkiWeb shared-deck publication; Zenodo DOI for citable releases.
