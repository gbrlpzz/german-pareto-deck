# Roadmap

## v0.2 - complete

- Token-span cloze matching now keeps punctuation and apostrophes.
- All 500 selected patterns have cloze cards.
- Added 62 recognition cards for routines and modal-particle frames.
- Added lemma-first glosses from the Kaikki German Wiktionary extract.
- Added form-of and alias redirects for residual inflected forms.
- Wired the full local pipeline. Fixed the Tatoeba links URL.
- Added tests for cloze matching and gloss cleanup.

The v0.2 deck is ready to use. It has 3,525 cards. Twenty-six word cards have no dictionary
gloss. They are mostly names or corpus-specific items.

## v0.3 - next

### Lemma quality

- Add a POS-aware dictionary pass to merge remaining irregular forms.
- Review clipped stems such as `bess`, `ohn`, and `jed`.
- Mark or remove names and other corpus-specific items.

### Card quality

- Add sentence audio.
- Review glosses with a small, versioned correction file.
- Add course-level tags after a source and mapping rule are chosen.

### Vocabulary coverage

- Test an optional 4,001-5,000 form band.
- Add a reading-register deck only after a separate corpus supports it.

### Maintenance

- Add GitHub Actions for tests and tagged builds.
- Publish a shared AnkiWeb deck.
- Add a Zenodo DOI for releases.
