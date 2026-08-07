from collections import Counter
from pathlib import Path
import re

import pandas as pd

from src.config import RAW_DATA_DIR


STOPWORDS = {
    "about",
    "after",
    "also",
    "among",
    "analysis",
    "article",
    "associated",
    "based",
    "before",
    "between",
    "both",
    "clinical",
    "could",
    "disease",
    "during",
    "from",
    "have",
    "into",
    "more",
    "most",
    "other",
    "paper",
    "patients",
    "potential",
    "results",
    "score",
    "study",
    "studies",
    "such",
    "than",
    "that",
    "their",
    "these",
    "this",
    "through",
    "using",
    "were",
    "which",
    "with",
    "within",
    "without",
    "alzheimer",
    "alzheimers",
    "parkinson",
    "parkinsons",
}


def tokenize(text: str) -> list[str]:
    """Convert article text into useful topic words."""

    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)

    words = re.findall(r"[a-zA-Z]{4,}", text)

    return [
        word
        for word in words
        if word not in STOPWORDS
    ]


def get_disease_name(csv_file: Path) -> str:
    """Create a readable disease name from the filename."""

    disease_name = csv_file.stem.replace(
        "_recent_articles",
        "",
    )

    return disease_name.replace("_", " ").title()


def calculate_top_topics(
    dataframe: pd.DataFrame,
    limit: int = 10,
) -> list[tuple[str, int]]:
    """Calculate the most common research terms."""

    words = []

    for _, row in dataframe.iterrows():
        title = str(row.get("Title", ""))
        abstract = str(row.get("Abstract", ""))

        words.extend(
            tokenize(f"{title} {abstract}")
        )

    return Counter(words).most_common(limit)


def build_profile(csv_file: Path) -> None:
    """Build and display a disease research profile."""

    if not csv_file.exists():
        print(f"\nDataset not found: {csv_file}")
        return

    dataframe = pd.read_csv(csv_file)

    if dataframe.empty:
        print("\nThe dataset is empty.")
        return

    dataframe["Year"] = pd.to_numeric(
        dataframe["Year"],
        errors="coerce",
    )

    valid_years = dataframe["Year"].dropna()

    print("=" * 60)
    print("PROJECT GENESIS")
    print("Disease Research Profile")
    print("=" * 60)

    print("\nDisease")
    print(get_disease_name(csv_file))

    print("\nTotal Papers")
    print(len(dataframe))

    print("\nYears")

    if valid_years.empty:
        print("Unknown")
    else:
        print(
            f"{int(valid_years.min())} - "
            f"{int(valid_years.max())}"
        )

    print("\nTop Journals")

    top_journals = (
        dataframe["Journal"]
        .fillna("Unknown")
        .value_counts()
        .head(5)
    )

    for journal, count in top_journals.items():
        print(f"{journal} ({count})")

    print("\nTop Research Topics")

    for topic, count in calculate_top_topics(dataframe):
        print(f"{topic} ({count})")


def list_available_datasets() -> list[Path]:
    """Find all collected disease datasets."""

    return sorted(
        RAW_DATA_DIR.glob("*_recent_articles.csv")
    )


def main() -> None:
    """Allow the user to choose a disease dataset."""

    datasets = list_available_datasets()

    if not datasets:
        print(
            "\nNo disease datasets were found in "
            f"{RAW_DATA_DIR}"
        )
        return

    print("\nAvailable disease datasets:\n")

    for number, dataset in enumerate(
        datasets,
        start=1,
    ):
        print(
            f"{number}. {get_disease_name(dataset)}"
        )

    selection = input(
        "\nEnter the dataset number: "
    ).strip()

    try:
        selected_index = int(selection) - 1
        selected_dataset = datasets[selected_index]
    except (ValueError, IndexError):
        print("\nInvalid selection.")
        return

    print()
    build_profile(selected_dataset)


if __name__ == "__main__":
    main()