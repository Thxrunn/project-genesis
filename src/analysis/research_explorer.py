import re
from collections import Counter
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DATA_DIR


STOP_WORDS = {
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
    "results",
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
    "and",
"are",
"been",
"being",
"can",
"did",
"does",
"each",
"for",
"has",
"its",
"may",
"not",
"our",
"the",
"was",
"will",
}


def load_articles(file_path: Path) -> pd.DataFrame:
    """Load and validate a PubMed article dataset."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    dataframe = pd.read_csv(file_path)

    required_columns = {
        "PMID",
        "Title",
        "Authors",
        "Journal",
        "Year",
        "Abstract",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )

    if missing_columns:
        raise ValueError(
            "The dataset is missing these columns: "
            + ", ".join(sorted(missing_columns))
        )

    return dataframe


def prepare_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Clean article fields before analysis."""

    cleaned_data = dataframe.copy()

    cleaned_data["Year"] = pd.to_numeric(
        cleaned_data["Year"],
        errors="coerce",
    )

    cleaned_data["Journal"] = (
        cleaned_data["Journal"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    cleaned_data["Title"] = (
        cleaned_data["Title"]
        .fillna("")
        .astype(str)
    )

    cleaned_data["Abstract"] = (
        cleaned_data["Abstract"]
        .fillna("")
        .astype(str)
    )

    return cleaned_data


def calculate_publication_trends(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Count collected papers by publication year."""

    valid_years = dataframe.dropna(
        subset=["Year"]
    ).copy()

    trends = (
        valid_years
        .groupby("Year")
        .size()
        .reset_index(name="Paper_Count")
        .sort_values("Year")
    )

    trends["Year"] = trends["Year"].astype(int)

    return trends


def calculate_top_journals(
    dataframe: pd.DataFrame,
    limit: int = 10,
) -> pd.DataFrame:
    """Find the most common journals."""

    journals = (
        dataframe["Journal"]
        .value_counts()
        .head(limit)
        .reset_index()
    )

    journals.columns = [
        "Journal",
        "Paper_Count",
    ]

    return journals


def clean_text(text: str) -> list[str]:
    """Extract useful words from biomedical text."""

    text = re.sub(
        r"<[^>]+>",
        " ",
        str(text),
    )

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z-]{2,}\b",
        text.lower(),
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


def calculate_top_keywords(
    dataframe: pd.DataFrame,
    limit: int = 20,
) -> pd.DataFrame:
    """Find common terms in titles and abstracts."""

    all_words = []

    for _, article in dataframe.iterrows():
        combined_text = (
            f"{article['Title']} "
            f"{article['Abstract']}"
        )

        all_words.extend(
            clean_text(combined_text)
        )

    word_counts = Counter(all_words)

    return pd.DataFrame(
        word_counts.most_common(limit),
        columns=[
            "Keyword",
            "Frequency",
        ],
    )


def count_missing_abstracts(
    dataframe: pd.DataFrame,
) -> int:
    """Count papers without usable abstracts."""

    abstract_text = (
        dataframe["Abstract"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    missing_abstracts = abstract_text.isin(
        {
            "",
            "nan",
            "none",
            "no abstract available",
        }
    )

    return int(missing_abstracts.sum())


def get_dataset_name(
    input_file: Path,
) -> str:
    """Get the disease identifier from a dataset filename."""

    return input_file.stem.replace(
        "_recent_articles",
        "",
    )


def save_results(
    publication_trends: pd.DataFrame,
    top_journals: pd.DataFrame,
    top_keywords: pd.DataFrame,
    dataset_name: str,
) -> dict[str, Path]:
    """Save disease-specific analysis results."""

    output_directory = (
        PROCESSED_DATA_DIR
        / dataset_name
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths = {
        "publication_trends":
            output_directory
            / "publication_trends.csv",
        "top_journals":
            output_directory
            / "top_journals.csv",
        "top_keywords":
            output_directory
            / "top_keywords.csv",
    }

    publication_trends.to_csv(
        paths["publication_trends"],
        index=False,
    )

    top_journals.to_csv(
        paths["top_journals"],
        index=False,
    )

    top_keywords.to_csv(
        paths["top_keywords"],
        index=False,
    )

    return paths


def analyze_research(
    input_file: Path,
    display_results: bool = True,
) -> dict:
    """Run the complete research analysis."""

    articles = load_articles(input_file)
    articles = prepare_data(articles)

    publication_trends = (
        calculate_publication_trends(articles)
    )

    top_journals = calculate_top_journals(
        articles
    )

    top_keywords = calculate_top_keywords(
        articles
    )

    missing_abstracts = count_missing_abstracts(
        articles
    )

    dataset_name = get_dataset_name(
        input_file
    )

    output_paths = save_results(
        publication_trends=publication_trends,
        top_journals=top_journals,
        top_keywords=top_keywords,
        dataset_name=dataset_name,
    )

    results = {
        "dataset_name": dataset_name,
        "total_papers": len(articles),
        "missing_abstracts": missing_abstracts,
        "publication_trends":
            publication_trends,
        "top_journals": top_journals,
        "top_keywords": top_keywords,
        "output_paths": output_paths,
    }

    if display_results:
        print_research_results(results)

    return results


def print_research_results(
    results: dict,
) -> None:
    """Display research analysis results."""

    print("\n" + "=" * 60)
    print("PROJECT GENESIS — RESEARCH EXPLORER")
    print("=" * 60)

    print(
        f"\nDisease dataset: "
        f"{results['dataset_name']}"
    )

    print(
        f"Total papers collected: "
        f"{results['total_papers']}"
    )

    print(
        f"Papers without abstracts: "
        f"{results['missing_abstracts']}"
    )

    print("\nPUBLICATIONS BY YEAR")
    print("-" * 30)
    print(
        results["publication_trends"].to_string(
            index=False
        )
    )

    print("\nTOP JOURNALS")
    print("-" * 30)
    print(
        results["top_journals"].to_string(
            index=False
        )
    )

    print("\nTOP RESEARCH TERMS")
    print("-" * 30)
    print(
        results["top_keywords"].to_string(
            index=False
        )
    )

    print(
        "\nAnalysis files saved inside: "
        f"data/processed/"
        f"{results['dataset_name']}/"
    )


def main() -> None:
    """Run research analysis from the terminal."""

    from src.config import RAW_DATA_DIR

    input_file = (
        RAW_DATA_DIR
        / "alzheimer_recent_articles.csv"
    )

    try:
        analyze_research(input_file)

    except (FileNotFoundError, ValueError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()