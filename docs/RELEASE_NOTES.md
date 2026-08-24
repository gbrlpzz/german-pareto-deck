# Release notes

## v0.3 - release candidate

- 3,122 cards: 2,560 word cards, 500 pattern cloze cards, and 62 recognition cards.
- Core has 1,313 cards. Extension has 1,247 cards. Patterns has 562 cards.
- Added 882 validated Kaikki lemma overrides.
- Rejected 6 malformed or unsafe Kaikki form links, including the known `trinkst -> triften` source error.
- Added deterministic handling for `ß`/`ss` reference collisions.
- Added deterministic lexicographic tie-breaking for equal-length English translations.
- Removed 28 word rows with no usable dictionary gloss and recorded them in
  `derived/vocab_exclusions.csv`.
- Added a one-command build stage after source caches are downloaded.
- Normalized APKG ZIP metadata. Same inputs produce the same APKG hash.
- Added release tests for APKG schema, counts, deck names, no audio, and GUID uniqueness.
- Audio is intentionally not included.
- The optional 4,001-5,000 extension is intentionally not included.

## v0.2

- 3,525 cards: 2,963 word cards, 500 pattern cloze cards, and 62 recognition cards.
- Recovered all 39 patterns that v0.1 could not cloze.
- Added punctuation-tolerant and apostrophe-tolerant cloze matching.
- Added recognition cards for 42 routines and 20 modal-particle frames.
- Added Kaikki lemma glosses and Wiktionary form-of redirects.
- Added a resumable Kaikki download script.
- Replaced pipeline WIP stages with runnable commands.
- Fixed the Tatoeba links export URL.
