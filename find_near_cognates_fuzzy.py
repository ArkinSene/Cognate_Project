"""
Discover near-cognate patterns automatically using fuzzy string matching.

Fuzzy Logic:
  - Uses difflib.SequenceMatcher to compare words at the same rank across
    all languages in raw_data.csv (plus English from the frekwencja list).

Universal Comparison:
  - Compares every language to every other language at each rank.

Threshold:
  - A pair of words is considered a Near-Cognate if:
        similarity_score > 0.7  (70%)
    AND the words are not identical.

Pattern Extraction:
  - For every match, identifies the "delta" between the two words by
    factoring out the longest common prefix and suffix. For example:
      "Nacion" vs "Nacao" might yield something like:
        Pattern_Detected = "ci -> ca" (depending on exact spelling).

Grouping:
  - Results are grouped by Rank; each row corresponds to a single
    language pair at that rank, with the English word at that rank
    used as the English_Meaning.

Output:
  - Saves to near_cognates_discovered.csv with columns:
        Rank,
        English_Meaning,
        Language_A,
        Word_A,
        Language_B,
        Word_B,
        Similarity_Score,
        Pattern_Detected

Safety:
  - Loads raw_data.csv with encoding="utf-8", errors="replace".
  - Excludes very short words (length < 4) to avoid trivial matches.
  - All print() output is plain ASCII to avoid Windows "charmap" issues.
"""

import csv
import os
import urllib.request
import difflib
import itertools
from typing import Dict, List, Tuple, Set


RAW_DATA = "raw_data.csv"
OUTPUT_FILE = "near_cognates_discovered.csv"
ENGLISH_URL = (
    "https://raw.githubusercontent.com/"
    "frekwencja/most-common-words-multilingual/main/data/wordfrequency.info/en.txt"
)


def download_english() -> List[str]:
    """Download the English frequency list, one word per line, ordered by rank."""
    req = urllib.request.Request(ENGLISH_URL, headers={"User-Agent": "Python"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    return lines  # index 0 = rank 1, etc.


def load_raw_data(path: str) -> Tuple[Dict[Tuple[str, int], str], Set[str], int]:
    """
    Load raw_data.csv and return:
      - by_lang_rank: dict[(language_code, rank:int)] -> word
      - languages: set of language codes observed in the file
      - max_rank: maximum rank value observed

    Uses encoding="utf-8" and errors="replace" for robustness.
    """
    by_lang_rank: Dict[Tuple[str, int], str] = {}
    languages: Set[str] = set()
    max_rank = 0

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
            languages.add(lang)
            if rank > max_rank:
                max_rank = rank

    return by_lang_rank, languages, max_rank


def longest_common_prefix(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def longest_common_suffix(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[-1 - i] == b[-1 - i]:
        i += 1
    return i


def detect_delta(a: str, b: str) -> str:
    """
    Compute a simple "delta" description between two strings by factoring
    out the longest common prefix and suffix.

    Returns a human-readable description such as:
      "suffix: cion -> cao"
      "middle: at -> et"
      or an empty string if no clear localized difference is found.
    """
    if not a or not b:
        return ""

    prefix_len = longest_common_prefix(a, b)
    suffix_len = longest_common_suffix(a, b)

    # Avoid overlap between prefix and suffix.
    max_common = min(len(a), len(b))
    if prefix_len + suffix_len > max_common:
        suffix_len = max(0, max_common - prefix_len)

    a_mid = a[prefix_len : len(a) - suffix_len if suffix_len > 0 else len(a)]
    b_mid = b[prefix_len : len(b) - suffix_len if suffix_len > 0 else len(b)]

    # If the middle segments capture a decent difference, report them.
    if a_mid or b_mid:
        return f"delta: '{a_mid}' vs '{b_mid}'"

    # If we could not identify a localized middle, fall back to whole words.
    if a != b:
        return f"delta_whole: '{a}' vs '{b}'"

    return ""


def find_near_cognates(
    english_by_rank: List[str],
    by_lang_rank: Dict[Tuple[str, int], str],
    languages: Set[str],
    max_rank_data: int,
    threshold: float = 0.7,
) -> List[List[str]]:
    """
    Core fuzzy matching logic.

    - For each rank, collect all words from:
        * English list (code "en"), as English_Meaning
        * All languages present in raw_data.csv.
    - Exclude words shorter than 4 characters.
    - For every pair of languages at that rank, compute similarity and
      keep those with similarity > threshold and not identical.
    """
    rows: List[List[str]] = []
    max_rank = min(len(english_by_rank), max_rank_data)

    for rank in range(1, max_rank + 1):
        english_meaning = english_by_rank[rank - 1].strip()
        if len(english_meaning) < 1:
            continue

        # Collect all language-word pairs for this rank.
        entries: List[Tuple[str, str]] = []
        # English as reference concept
        entries.append(("en", english_meaning))

        for lang_code in sorted(languages):
            word = by_lang_rank.get((lang_code, rank), "").strip()
            if not word:
                continue
            entries.append((lang_code, word))

        # Exclude pairs where either side is shorter than 4 characters.
        entries = [(lc, w) for (lc, w) in entries if len(w) >= 4]
        if len(entries) < 2:
            continue

        # Compare every language to every other language.
        for (lang_a, word_a), (lang_b, word_b) in itertools.combinations(entries, 2):
            if word_a == word_b:
                # Identical words are perfect cognates, not "near".
                continue

            # Additional length guard
            if len(word_a) < 4 or len(word_b) < 4:
                continue

            sim = difflib.SequenceMatcher(None, word_a, word_b).ratio()
            if sim <= threshold or sim >= 1.0:
                continue

            pattern = detect_delta(word_a, word_b)

            rows.append(
                [
                    rank,
                    english_meaning,
                    lang_a,
                    word_a,
                    lang_b,
                    word_b,
                    f"{sim:.3f}",
                    pattern,
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
    by_lang_rank, languages, max_rank_data = load_raw_data(raw_path)
    print(f"  Loaded {len(by_lang_rank)} language-rank entries across {len(languages)} languages.")

    print("Finding near cognates using fuzzy matching...")
    rows = find_near_cognates(
        english_by_rank,
        by_lang_rank,
        languages,
        max_rank_data,
        threshold=0.7,
    )
    print(f"  Near-cognate rows: {len(rows)}")

    header = [
        "Rank",
        "English_Meaning",
        "Language_A",
        "Word_A",
        "Language_B",
        "Word_B",
        "Similarity_Score",
        "Pattern_Detected",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Finished. Saved near cognates to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()

