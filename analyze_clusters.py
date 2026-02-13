"""
Analyze clusters of universal Romance cognates.

Reads universal_cognates.csv (produced by find_perfect_cognates.py) and:

- Groups words by which languages they share (the "cluster" of languages).
- Identifies the "Spanish-Italian Connection":
    words that are identical in Spanish and Italian (they may also appear in
    other languages).
- Identifies the "Balkan-Romance Connection":
    words that are identical in Romanian and at least one other Romance
    language.
- Prints a summary of the top 5 most common language pairs
    (e.g. "Spanish & Portuguese share 1,200 identical words").
"""

import csv
import os
import itertools
from collections import defaultdict, Counter


INPUT_FILE = "universal_cognates.csv"


def load_universal_cognates(path):
    """
    Load universal_cognates.csv and return:
      - clusters: dict[frozenset(language_names)] -> list of words
      - pair_counts: Counter[frozenset({lang_a, lang_b})] -> int
      - spanish_italian_words: list of words with both Spanish and Italian
      - romanian_connections: Counter[other_language_name] -> int
    """
    clusters = defaultdict(list)
    pair_counts: Counter = Counter()
    spanish_italian_words = []
    romanian_connections: Counter = Counter()

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # We expect first columns to be: Word, Language_Count, then language names.
        fieldnames = reader.fieldnames or []
        if "Word" not in fieldnames:
            raise ValueError("Expected 'Word' column in universal_cognates.csv")
        if "Language_Count" not in fieldnames:
            raise ValueError("Expected 'Language_Count' column in universal_cognates.csv")

        # All columns after Language_Count are language-name columns.
        lang_start_index = fieldnames.index("Language_Count") + 1
        language_columns = fieldnames[lang_start_index:]

        for row in reader:
            word = row["Word"].strip()
            if not word:
                continue

            # Determine which languages share this word
            languages_present = [
                lang_name
                for lang_name in language_columns
                if row.get(lang_name, "").strip()
            ]

            if len(languages_present) < 2:
                # By construction this shouldn't happen, but be safe.
                continue

            # Cluster by the set of languages
            key = frozenset(languages_present)
            clusters[key].append(word)

            # Count all language pairs for this word
            for a, b in itertools.combinations(sorted(languages_present), 2):
                pair_counts[frozenset({a, b})] += 1

            # Spanish-Italian connection
            if "Spanish" in languages_present and "Italian" in languages_present:
                spanish_italian_words.append(word)

            # Balkan-Romance connection: Romanian + at least one other language
            if "Romanian" in languages_present:
                for other in languages_present:
                    if other == "Romanian":
                        continue
                    romanian_connections[other] += 1

    return clusters, pair_counts, spanish_italian_words, romanian_connections


def print_summary(
    clusters,
    pair_counts,
    spanish_italian_words,
    romanian_connections,
    top_n_pairs: int = 5,
):
    total_words = sum(len(words) for words in clusters.values())
    total_clusters = len(clusters)

    print("\n=== Universal Cognate Cluster Summary ===")
    print(f"Total clusters (unique language combinations): {total_clusters}")
    print(f"Total words covered by clusters: {total_words}")

    # Optional: show a few of the largest clusters
    largest_clusters = sorted(
        clusters.items(), key=lambda kv: len(kv[1]), reverse=True
    )[:5]
    print("\nTop 5 largest clusters by shared languages:")
    for langs, words in largest_clusters:
        langs_list = ", ".join(sorted(langs))
        print(f"  - {langs_list}: {len(words)} words")

    # Spanish-Italian Connection
    print("\n=== Spanish-Italian Connection ===")
    print(
        "Words that are identical in Spanish and Italian "
        "(they may also appear in other languages)."
    )
    count_si = len(spanish_italian_words)
    print(f"Total Spanish-Italian shared words: {count_si}")
    if count_si:
        sample = sorted(set(spanish_italian_words))[:20]
        print("Sample (up to 20): " + ", ".join(sample))

    # Balkan-Romance Connection (Romanian + others)
    print("\n=== Balkan-Romance Connection (Romanian + others) ===")
    total_balkan_words = sum(romanian_connections.values())
    print(
        "Words that are identical in Romanian and at least one other Romance language."
    )
    if not romanian_connections:
        print("No Romanian connections found.")
    else:
        print(f"Total Romanian-other language links (with multiplicity): {total_balkan_words}")
        for other_lang, cnt in romanian_connections.most_common():
            print(f"  - Romanian & {other_lang}: {cnt} words")

    # Top N language pairs overall
    print(f"\n=== Top {top_n_pairs} Language Pairs (by shared identical words) ===")
    if not pair_counts:
        print("No language pairs found.")
        return

    for i, (pair, cnt) in enumerate(
        pair_counts.most_common(top_n_pairs), start=1
    ):
        langs = sorted(pair)
        pair_label = " & ".join(langs)
        print(f"{i}. {pair_label} share {cnt} identical words")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    in_path = os.path.join(script_dir, INPUT_FILE)

    if not os.path.isfile(in_path):
        print(f"Error: {INPUT_FILE} not found in {script_dir}")
        return

    (
        clusters,
        pair_counts,
        spanish_italian_words,
        romanian_connections,
    ) = load_universal_cognates(in_path)

    print_summary(
        clusters,
        pair_counts,
        spanish_italian_words,
        romanian_connections,
        top_n_pairs=5,
    )


if __name__ == "__main__":
    main()

