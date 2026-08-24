# Roadmap

## v0.2 - complete

- Recovered all 500 pattern cloze cards.
- Added 62 recognition cards.
- Added Kaikki lemma-first glosses and form-of redirects.
- Wired the local pipeline and fixed the Tatoeba links URL.

## v0.3 - release candidate

### Complete

- Added a validated Kaikki lemma pass. It accepts 882 links and rejects 6 unsafe or malformed refs.
- Added deterministic `ß`/`ss` tie handling and deterministic translation ties.
- Removed 28 word rows with no usable dictionary gloss. Wrote every exclusion to
  `derived/vocab_exclusions.csv`.
- Added a one-command `pipeline.py build` path after source caches are downloaded.
- Added a fixed timestamp and normalized ZIP metadata. Identical inputs produce identical APKG bytes.
- Added release-artifact tests for counts, deck names, no-audio scope, and GUID uniqueness.
- Prepared Zenodo metadata and AnkiWeb copy.

### Deliberately deferred

- Sentence audio. It adds platform-specific files and long build times for a small expected gain.
- The optional 4,001-5,000 band. Its measured marginal gain does not justify changing the default deck.
- Course-level tags. No source and mapping rule has been selected.
- A reading-register deck. It needs a separate corpus.

## Next

- Publish the v0.3 APKG to GitHub Releases, Zenodo, and AnkiWeb.
- Add GitHub Actions for the lightweight tests and a tagged build.
- Review a small versioned gloss-correction file only when a concrete error list is available.
