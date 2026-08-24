#!/usr/bin/env python3
"""Download the German Kaikki/Wiktionary extract with resume support.

The 1 GB source stays in data/ and is not committed. The script prints its
size and sha256 after the download.
"""
import hashlib
import pathlib
import time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
URL = "https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl"
OUT = ROOT / "data" / "kaikki_de.jsonl"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.parent.mkdir(exist_ok=True)
    total = int(requests.head(URL, timeout=30).headers.get("Content-Length", 0))
    pos = OUT.stat().st_size if OUT.exists() else 0
    attempts = 0
    while not total or pos < total:
        attempts += 1
        if attempts > 10:
            raise RuntimeError("download did not complete after 10 attempts")
        headers = {"Range": f"bytes={pos}-"} if pos else {}
        try:
            with requests.get(URL, headers=headers, stream=True,
                              timeout=(30, 120)) as response:
                response.raise_for_status()
                if pos and response.status_code != 206:
                    pos = 0
                mode = "ab" if pos and response.status_code == 206 else "wb"
                with open(OUT, mode) as fh:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            fh.write(chunk)
                            pos += len(chunk)
        except requests.RequestException:
            time.sleep(2)
            continue
        if total and pos >= total:
            break
    print(f"kaikki: {OUT.stat().st_size:,} bytes  sha256={sha256(OUT)}")


if __name__ == "__main__":
    main()
