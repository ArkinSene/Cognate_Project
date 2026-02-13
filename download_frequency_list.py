"""
Download Romance language frequency lists from GitHub and save as raw_data.csv.

Source: https://github.com/frekwencja/most-common-words-multilingual
Data: ~5050 most frequent words per language (wordfrequency.info).
"""

import csv
import urllib.request
import os

# Raw file URLs (one .txt per language: word per line, first line is language code)
BASE = "https://raw.githubusercontent.com/frekwencja/most-common-words-multilingual/main/data/wordfrequency.info"
LANGUAGES = [
    ("es", "Spanish"),
    ("fr", "French"),
    ("pt", "Portuguese"),
    ("it", "Italian"),
    ("ro", "Romanian"),
    ("ca", "Catalan"),
    ("gl", "Galician"),
]

OUTPUT_FILE = "raw_data.csv"


def download_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Python"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, OUTPUT_FILE)

    rows = []
    for code, name in LANGUAGES:
        url = f"{BASE}/{code}.txt"
        try:
            text = download_url(url)
        except Exception as e:
            print(f"Failed to download {name} ({url}): {e}")
            continue
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        # First line is often the language code; rest are words (rank = order)
        for rank, word in enumerate(lines, start=1):
            rows.append({"language": code, "language_name": name, "rank": rank, "word": word})
        print(f"Downloaded {name}: {len(lines)} words")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["language", "language_name", "rank", "word"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
