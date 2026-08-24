# Zenodo publication handoff

## Files to deposit

Use the verified publication bundle after the v0.3 release build:

- `german-pareto-deck-v0.3-zenodo.zip`
- `RELEASE_MANIFEST.json`
- `ZENODO_METADATA.json`
- `LICENSE`
- `LICENSE_NOTE.md`
- `docs/DATA_SOURCES.md`
- `docs/METHODOLOGY.md`

Do not upload `data/`. The raw Tatoeba, English, links, or Kaikki files are not redistributed.

## Metadata

`docs/ZENODO_METADATA.json` contains prepared metadata. Replace the creator handle if a personal
or institutional name is preferred. The composite license note is intentional: the code is MIT,
Tatoeba-derived sentence material is CC BY 2.0 FR, and Kaikki/Wiktionary-derived glosses and form
links are CC BY-SA 3.0.

## Deposit steps

1. Sign in to Zenodo or Zenodo Sandbox.
2. Create a new upload.
3. Add the bundle and the manifest.
4. Paste the JSON fields from `ZENODO_METADATA.json`.
5. Check the license and attribution text.
6. Save a draft first. Confirm the file hash against `RELEASE_MANIFEST.json`.
7. Publish only after the GitHub v0.3 release is live.
8. Add the DOI to the GitHub release and README.

Zenodo deposit and publication require the owner's account authorization. No token is stored in
this repository.
