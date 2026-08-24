#!/usr/bin/env python3
"""german-pareto-deck reproducible pipeline.

Stages: fetch -> freq -> patterns -> sentences -> deck
Every artifact lands in data/ (gitignored) or derived/ (tracked, inspectable).
"""
import argparse, bz2, collections, csv, hashlib, pathlib, re, sys
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"; DERIVED = ROOT / "derived"
TATOEBA = "https://downloads.tatoeba.org/exports/per_language"

FILES = {
    "deu": f"{TATOEBA}/deu/deu_sentences_detailed.tsv.bz2",
    "eng": f"{TATOEBA}/eng/eng_sentences_detailed.tsv.bz2",
    "links": f"{TATOEBA}/deu/deu_links.tsv.bz2",
}
TOKEN_RE = re.compile(r"[a-z\u00e4\u00f6\u00fc\u00df']+")

LOCAL_NAMES = {
    "deu": "deu_sentences_detailed.tsv.bz2",
    "eng": "eng_sentences_detailed.tsv.bz2",
    "links": "links.tar.bz2",
}

def fetch():
    DATA.mkdir(exist_ok=True)
    for key, url in FILES.items():
        out = DATA / LOCAL_NAMES[key]
        pos = out.stat().st_size if out.exists() else 0
        total = int(requests.head(url, timeout=20).headers.get("Content-Length", 0))
        while 0 < pos < total or (pos == 0 and not out.exists()):
            r = requests.get(url, headers={"Range": f"bytes={pos}-"} if pos else {},
                             stream=True, timeout=(10, 30))
            mode = "ab" if r.status_code == 206 and pos else "wb"
            if mode == "wb":
                pos = 0
            with open(out, mode) as fh:
                for ch in r.iter_content(262144):
                    fh.write(ch); pos += len(ch)
            if pos >= total:
                break
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        print(f"{key}: {pos:,} bytes  sha256={digest}")

def _tokens(text):
    for m in TOKEN_RE.findall(text.lower()):
        w = m.strip("'")
        if w:
            yield w

def freq():
    src = DATA / "deu_sentences_detailed.tsv.bz2"
    counter = collections.Counter(); total_tokens = 0
    with bz2.open(src, "rt", encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 3 and parts[1] == "deu":
                for w in _tokens(parts[2]):
                    counter[w] += 1; total_tokens += 1
    DERIVED.mkdir(exist_ok=True)
    cum = 0
    with open(DERIVED / "top_forms.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh); wr.writerow(["rank", "form", "count", "cum_share_pct"])
        for i, (w, c) in enumerate(counter.most_common(), 1):
            cum += c
            wr.writerow([i, w, c, round(cum / total_tokens * 100, 4)])
    print(f"forms: {len(counter):,}; tokens: {total_tokens:,} -> {DERIVED/'top_forms.csv'}")

def patterns():
    sys.exit("patterns: WIP (n-gram extraction + class templates)")

def sentences():
    sys.exit("sentences: WIP")

def deck():
    sys.exit("deck: WIP (genanki)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage", choices=["fetch", "freq", "patterns", "sentences", "deck"])
    args = ap.parse_args()
    globals()[args.stage]()
