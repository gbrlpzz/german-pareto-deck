#!/usr/bin/env python3
"""Write the public v0.3 release manifest from local build artifacts."""
import collections
import csv
import hashlib
import json
import pathlib
import sqlite3
import subprocess
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DERIVED = ROOT / "derived"
DATA = ROOT / "data"
APKG = ROOT / "out" / "german-pareto-deck.apkg"
OUT = ROOT / "docs" / "RELEASE_MANIFEST.json"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(name):
    with open(DERIVED / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def apkg_counts():
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(APKG) as package:
            media = json.loads(package.read("media"))
            package.extract("collection.anki2", td)
        db = sqlite3.connect(pathlib.Path(td) / "collection.anki2")
        notes = db.execute("select mid from notes").fetchall()
        cards = db.execute("select count(*) from cards").fetchone()[0]
        db.close()
    return {
        "notes": len(notes),
        "cards": cards,
        "models": dict(collections.Counter(str(mid) for (mid,) in notes)),
        "media_files": len(media),
    }


def main():
    source_files = {
        "tatoeba_deu": DATA / "deu_sentences_detailed.tsv.bz2",
        "tatoeba_eng": DATA / "eng_sents.tsv.bz2",
        "tatoeba_links": DATA / "links.tar.bz2",
        "kaikki_german": DATA / "kaikki_de.jsonl",
    }
    sources = {}
    for name, path in source_files.items():
        if path.exists():
            sources[name] = {"path": str(path.relative_to(ROOT)),
                             "bytes": path.stat().st_size,
                             "sha256": sha256(path)}
    wordlist = rows("wordlist.csv")
    manifest = {
        "release": "v0.3",
        "artifact": {
            "path": "out/german-pareto-deck.apkg",
            "bytes": APKG.stat().st_size,
            "sha256": sha256(APKG),
        },
        "apkg": apkg_counts(),
        "word_cards": {
            "total": len(wordlist),
            "core": sum(row["tier"] == "core" for row in wordlist),
            "extension": sum(row["tier"] == "ext" for row in wordlist),
        },
        "patterns": {
            "selected": len(rows("patterns_selected.csv")),
            "recognition": sum(row["class"] in ("routine", "particle_frame")
                                for row in rows("patterns_selected.csv")),
        },
        "lemma_overrides": {
            "accepted": len(rows("lemma_overrides.csv")),
            "rejected": len(rows("lemma_override_exclusions.csv")),
        },
        "vocabulary_exclusions": len(rows("vocab_exclusions.csv")),
        "translations": {
            "total": len(rows("translations.csv")),
            "translated": sum(row["has_en"] == "yes" for row in rows("translations.csv")),
        },
        "derived_sha256": {
            name: sha256(DERIVED / name)
            for name in ("wordlist.csv", "lemma_overrides.csv",
                         "lemma_override_exclusions.csv", "vocab_exclusions.csv",
                         "translations.csv")
        },
        "source_checksums": sources,
        "source_revision": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "build": ".venv/bin/python src/pipeline.py build",
        "tests": [
            ".venv/bin/python -m unittest test_pipeline test_deck test_glosses test_phase3 test_release -v",
            ".venv/bin/python test_lemmatize.py",
        ],
        "scope": {"audio": False, "raw_corpora_redistributed": False,
                  "optional_5k_band": False},
        "licenses": {
            "code": "MIT",
            "tatoeba": "CC BY 2.0 FR",
            "kaikki_wiktionary": "CC BY-SA 3.0",
        },
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["artifact"], ensure_ascii=False))


if __name__ == "__main__":
    main()
