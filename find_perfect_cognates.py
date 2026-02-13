"""
Find universal perfect cognates by rank.

Universal Matching:
  - Compare every language in raw_data.csv (Spanish, French, Italian,
    Portuguese, Romanian, Catalan, Galician) plus English (from the
    frekwencja list) against each other.

Logic:
  - For every rank, build a list of all words from all languages
    (including English).
  - If the same word appears in two or more languages at that rank,
    it is a perfect cognate match.
  - Multiple matches (e.g., "Hotel" in EN, ES, FR, IT) are grouped
    together into one row.

Output:
  - Writes perfect_cognates_universal.csv with columns:
      Rank,
      English_Meaning,
      Word,
      Languages_Found (e.g., "en,es,fr,it"),
      Count

Windows safety:
  - Uses encoding="utf-8" and errors="replace" for reading raw_data.csv.
  - Uses only standard ASCII characters in print() output.
"""

import csv
import os
import urllib.request
from collections import defaultdict
from typing import Dict, List, Tuple


RAW_DATA = "raw_data.csv"
OUTPUT_FILE = "perfect_cognates_universal.csv"
ENGLISH_URL = (
    "https://raw.githubusercontent.com/"
    "frekwencja/most-common-words-multilingual/main/data/wordfrequency.info/en.txt"
)

# Target languages (codes must match those in raw_data.csv)
LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ro", "Romanian"),
    ("ca", "Catalan"),
    ("gl", "Galician"),
]


def download_english() -> List[str]:
    """Download the English frequency list, one word per line, ordered by rank."""
    req = urllib.request.Request(ENGLISH_URL, headers={"User-Agent": "Python"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return lines  # index 0 = rank 1, etc.


def load_raw_data(path: str) -> Dict[Tuple[str, int], str]:
    """
    Load raw_data.csv and return dict: (language_code, rank:int) -> word.

    Uses encoding="utf-8" and errors="replace" for robustness on Windows.
    """
    by_lang_rank: Dict[Tuple[str, int], str] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = (row.get("language") or "").strip()
            if not lang:
                continue
            try:
                rank = int((row.get("rank") or "").strip())
            except (TypeError, ValueError):
                continue
            word = (row.get("word") or "").strip()
            if not word:
                continue
            by_lang_rank[(lang, rank)] = word
    return by_lang_rank


def find_universal_perfect_cognates(
    english_by_rank: List[str],
    by_lang_rank: Dict[Tuple[str, int], str],
) -> List[List[str]]:
    """
    For every rank, compare all languages against each other and collect
    universal perfect cognates.

    - English_Meaning comes from the English list at that rank.
    - Word is the shared spelling.
    - Languages_Found is a comma-separated list of language codes that
      use that word at that rank (including "en" when applicable).
    - Count is the number of languages sharing that word.
    """
    rows: List[List[str]] = []
    max_rank = len(english_by_rank)

    for rank in range(1, max_rank + 1):
        english_meaning = english_by_rank[rank - 1].strip()
        if not english_meaning:
            continue

        # Build mapping: word -> list of language codes using that word at this rank.
        word_langs: Dict[str, List[str]] = defaultdict(list)

        # English entry for this rank (reference concept)
        word_langs[english_meaning].append("en")

        # Other languages from raw_data.csv
        for code, _name in LANGUAGES:
            if code == "en":
                continue
            word = by_lang_rank.get((code, rank), "").strip()
            if not word:
                continue
            word_langs[word].append(code)

        # For each word that appears in 2+ languages, record a universal match.
        for word, codes in word_langs.items():
            if len(codes) < 2:
                continue
            languages_found = ",".join(sorted(codes))
            count = len(codes)
            rows.append(
                [
                    rank,
                    english_meaning,
                    word,
                    languages_found,
                    count,
                ]
            )

    return rows


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(script_dir, RAW_DATA)
    out_path = os.path.join(script_dir, OUTPUT_FILE)

    if not os.path.isfile(raw_path):
        print(f"Error: {RAW_DATA} not found in {script_dir}")
        return

    print("Loading English word list (by rank)...")
    english_by_rank = download_english()
    print(f"  English words loaded: {len(english_by_rank)}")

    print(f"Loading {RAW_DATA} with utf-8 (errors='replace')...")
    by_lang_rank = load_raw_data(raw_path)
    print(f"  Loaded {len(by_lang_rank)} language-rank entries.")

    print("Finding universal perfect cognates...")
    rows = find_universal_perfect_cognates(english_by_rank, by_lang_rank)
    print(f"  Perfect cognate rows: {len(rows)}")

    header = [
        "Rank",
        "English_Meaning",
        "Word",
        "Languages_Found",
        "Count",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Finished. Saved universal perfect cognates to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()

