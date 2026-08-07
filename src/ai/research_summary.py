from __future__ import annotations

import pandas as pd


def get_year_range(articles: pd.DataFrame) -> str:
    """Return a readable publication-year range."""

    if articles.empty or "Year" not in articles.columns:
        return "an unspecified period"

    years = pd.to_numeric(
        articles["Year"],
        errors="coerce",
    ).dropna()

    if years.empty:
        return "an unspecified period"

    earliest_year = int(years.min())
    latest_year = int(years.max())

    if earliest_year == latest_year:
        return str(earliest_year)

    return f"{earliest_year}–{latest_year}"


def get_values(
    dataframe: pd.DataFrame,
    column_name: str,
    limit: int,
) -> list[str]:
    """Safely retrieve values from a dataframe column."""

    if dataframe.empty:
        return []

    if column_name not in dataframe.columns:
        return []

    values = (
        dataframe[column_name]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[values != ""]

    return values.head(limit).tolist()


def join_readable(values: list[str]) -> str:
    """Join values using natural-language punctuation."""

    if not values:
        return ""

    if len(values) == 1:
        return values[0]

    if len(values) == 2:
        return f"{values[0]} and {values[1]}"

    return (
        ", ".join(values[:-1])
        + f", and {values[-1]}"
    )


def generate_summary(
    disease: str,
    articles: pd.DataFrame,
    journals: pd.DataFrame,
    keywords: pd.DataFrame,
    genes: pd.DataFrame,
) -> str:
    """Generate a safe executive-style research summary."""

    total_papers = len(articles)
    year_range = get_year_range(articles)

    top_journals = get_values(
        dataframe=journals,
        column_name="Journal",
        limit=3,
    )

    top_topics = get_values(
        dataframe=keywords,
        column_name="Keyword",
        limit=5,
    )

    top_genes = get_values(
        dataframe=genes,
        column_name="Symbol",
        limit=6,
    )

    if top_journals:
        journal_sentence = (
            "The current literature sample is concentrated "
            f"in journals including "
            f"{join_readable(top_journals)}."
        )
    else:
        journal_sentence = (
            "Journal-level concentration could not be "
            "determined from the available data."
        )

    if top_topics:
        topic_sentence = (
            "Frequently observed research themes include "
            f"{join_readable(top_topics)}. These themes "
            "represent topics receiving attention in the "
            "selected recent-publication sample."
        )
    else:
        topic_sentence = (
            "No reliable research-topic summary is "
            "available for this dataset."
        )

    if top_genes:
        gene_sentence = (
            "Official NCBI Gene records identified in the "
            f"current analysis include "
            f"{join_readable(top_genes)}. These records can "
            "be compared with their representation in the "
            "recent literature."
        )
    else:
        gene_sentence = (
            "Official disease-associated genes have not "
            "yet been collected for this dataset. Gene "
            "evidence scoring and research-gap analysis "
            "are therefore unavailable."
        )

    return (
        "Executive Summary\n\n"
        f"Project GENESIS analyzed {total_papers} recent "
        f"{disease} publications from {year_range}. "
        f"{journal_sentence}\n\n"
        f"{topic_sentence}\n\n"
        f"{gene_sentence}\n\n"
        "All summaries, rankings, and research-gap signals "
        "are exploratory outputs based on a limited public "
        "dataset. They do not prove scientific novelty, "
        "disease causality, biological importance, or "
        "clinical relevance."
    )


def main() -> None:
    """Confirm that this updated module is loading."""

    print(
        "Updated Project GENESIS research-summary "
        "module loaded successfully."
    )


if __name__ == "__main__":
    main()