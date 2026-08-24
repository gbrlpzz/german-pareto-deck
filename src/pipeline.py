#!/usr/bin/env python3
"""Run one reproducible stage of the German Anki deck pipeline.

Stages write inspectable files in derived/ or the built deck in out/.
Raw sources stay in data/ and are not committed.
"""
import argparse
import bz2
import collections
import csv
import hashlib
import pathlib
import re
import subprocess
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = ROOT / "derived"
TATOEBA = "https://downloads.tatoeba.org/exports"
FILES = {
    "deu": f"{TATOEBA}/per_language/deu/deu_sentences_detailed.tsv.bz2",
    "eng": f"{TATOEBA}/per_language/eng/eng_sentences_detailed.tsv.bz2",
    "links": f"{TATOEBA}/links.tar.bz2",
}
LOCAL_NAMES = {
    "deu": "deu_sentences_detailed.tsv.bz2",
    "eng": "eng_sents.tsv.bz2",
    "links": "links.tar.bz2",
}
TOKEN_RE = re.compile(r"[a-zäöüß']+")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(key, url, out):
    total = int(requests.head(url, timeout=30).headers.get("Content-Length", 0))
    pos = out.stat().st_size if out.exists() else 0
    for attempt in range(1, 11):
        if total and pos >= total:
            break
        headers = {"Range": f"bytes={pos}-"} if pos else {}
        try:
            with requests.get(url, headers=headers, stream=True,
                              timeout=(30, 120)) as response:
                response.raise_for_status()
                append = pos > 0 and response.status_code == 206
                if not append:
                    pos = 0
                with open(out, "ab" if append else "wb") as fh:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            fh.write(chunk)
                            pos += len(chunk)
            if not total or pos >= total:
                break
        except requests.RequestException as exc:
            if attempt == 10:
                raise RuntimeError(f"{key}: download failed: {exc}") from exc
            time.sleep(2)
    digest = _sha256(out)
    print(f"{key}: {out.stat().st_size:,} bytes  sha256={digest}")


def fetch():
    DATA.mkdir(exist_ok=True)
    for key, url in FILES.items():
        _download(key, url, DATA / LOCAL_NAMES[key])


def _tokens(text):
    for match in TOKEN_RE.findall(text.lower()):
        word = match.strip("'")
        if word:
            yield word


def freq():
    src = DATA / "deu_sentences_detailed.tsv.bz2"
    counter = collections.Counter()
    total_tokens = 0
    with bz2.open(src, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[1] == "deu":
                for word in _tokens(parts[2]):
                    counter[word] += 1
                    total_tokens += 1
    DERIVED.mkdir(exist_ok=True)
    cumulative = 0
    with open(DERIVED / "top_forms.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["rank", "form", "count", "cum_share_pct"])
        for rank, (word, count) in enumerate(counter.most_common(), 1):
            cumulative += count
            writer.writerow([rank, word, count,
                             round(cumulative / total_tokens * 100, 4)])
    print(f"forms: {len(counter):,}; tokens: {total_tokens:,} -> {DERIVED/'top_forms.csv'}")


def run_script(name):
    subprocess.run([sys.executable, str(ROOT / "src" / name)], check=True)


def patterns():
    run_script("patterns.py")


def select():
    run_script("select_patterns.py")


def lemmatize():
    run_script("lemmatize.py")


def words():
    run_script("words.py")


def lemma_overrides():
    run_script("lemma_overrides.py")


def lemma_glosses():
    run_script("lemma_glosses.py")


def filter_vocab():
    run_script("filter_vocab.py")


def sentences():
    run_script("sentences.py")


def translations():
    run_script("translations.py")


def fetch_kaikki():
    run_script("fetch_kaikki.py")


def glosses():
    run_script("glosses.py")


def deck():
    run_script("deck.py")


def plots():
    run_script("plots.py")


def build():
    """Build all derived artifacts from already downloaded source caches."""
    for name in ("freq", "patterns", "select", "lemma-overrides", "lemmatize",
                 "words", "lemma-glosses", "filter-vocab", "lemma-glosses",
                 "sentences", "translations", "deck", "plots"):
        STAGES[name]()


STAGES = {
    "fetch": fetch,
    "freq": freq,
    "patterns": patterns,
    "select": select,
    "lemmatize": lemmatize,
    "words": words,
    "lemma-overrides": lemma_overrides,
    "lemma-glosses": lemma_glosses,
    "filter-vocab": filter_vocab,
    "sentences": sentences,
    "translations": translations,
    "fetch-kaikki": fetch_kaikki,
    "glosses": glosses,
    "deck": deck,
    "plots": plots,
    "build": build,
}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=sorted(STAGES))
    STAGES[ap.parse_args().stage]()
