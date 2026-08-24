# Data sources and provenance

| Source | Role | URL | Fetched | Size | sha256 | License |
|---|---|---|---|---:|---|---|
| Tatoeba `deu_sentences_detailed.tsv.bz2` | sentence corpus, patterns, examples, frequency fallback | https://downloads.tatoeba.org/exports/per_language/deu/deu_sentences_detailed.tsv.bz2 | 2026-08 | 17,539,296 bytes | `254ab55937691edf9d5b6159095e6f6eff40ba0ed61e2ff16d682500703d18f4` | CC BY 2.0 FR |
| Tatoeba `links.tar.bz2` + English sentence export | English translations | https://downloads.tatoeba.org/exports/ | 2026-08 | links: 149,334,724 bytes; English: 34,837,075 bytes | links: `560404e552abbc78f1849c596e143fade91aca79648e111c602ae17b52655d30`; English: `53159b53f4f3a8de8df7c797b73be8adbf1e498c19ed9b8e7bad0ba1ab1e8273` | CC BY 2.0 FR |
| hermitdave/FrequencyWords `de_50k.txt` (OpenSubtitles 2016) | spoken-register frequency anchor | https://github.com/hermitdave/FrequencyWords | unavailable from the build environment; measured data is stored as a derived anchor | - | - | OpenSubtitles-derived, attribution |
| Wiktionary German extract (Kaikki / wiktextract) | lemma-level English glosses and form-of links | https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl | 2026-08 | 1,071,113,941 bytes | `8ad43b9407e4e632d234ba93ff97e9373e0f1bc47f0a186999f21f4441737fb7` | CC BY-SA 3.0 (Wiktionary) |
| Wiktionary REST definitions | form-level fallback glosses | https://en.wiktionary.org/api/rest_v1/ | 2026-08 | API | - | CC BY-SA 3.0 / GFDL (definitions) |

Raw sources are not redistributed. `src/pipeline.py fetch` and
`src/fetch_kaikki.py` download them again and print checksums.

## Generated publication artifacts

The v0.3 manifest records the final APKG hash, local source hashes, card counts, and build revision:
[docs/RELEASE_MANIFEST.json](RELEASE_MANIFEST.json).

The release does not upload `data/`. Rebuild it with the URLs above.
