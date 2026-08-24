# Data sources & provenance

| Source | Role | URL | Fetched | sha256 | License |
|---|---|---|---|---|---|
| Tatoeba `deu_sentences_detailed.tsv.bz2` | sentence corpus (patterns, examples, frequency fallback) | downloads.tatoeba.org/exports/per_language/deu/deu_sentences_detailed.tsv.bz2 | 2026-08 | 254ab55937691edf9d5b6159095e6f6eff40ba0ed61e2ff16d682500703d18f4 | CC BY 2.0 FR |
| Tatoeba `links.tar.bz2` + `eng_sentences_detailed.tsv.bz2` | EN translations for examples (links sha256 `560404e552abbc78…`) | downloads.tatoeba.org/exports/ | 2026-08 | see left | CC BY 2.0 FR |
| hermitdave/FrequencyWords `de_50k.txt` (OpenSubtitles 2016) | spoken-register frequency anchor | github.com/hermitdave/FrequencyWords | UNREACHABLE from build env; curve independently measured from primary dataset (see METHODOLOGY §2) | — | OpenSubtitles-derived, attribution |
| Wiktionary REST definitions | EN glosses for word cards (best-effort) | en.wiktionary.org/api/rest_v1/ | 2026-08 | n/a (API) | CC BY-SA 3.0 / GFDL (definitions) |
