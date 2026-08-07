from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
from Bio import Entrez


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import (
    DEFAULT_DISEASE_QUERY,
    DEFAULT_MAX_RESULTS,
    DEFAULT_YEARS_BACK,
    RAW_DATA_DIR,
)


Entrez.email = "thxrun2025@gmail.com"


def search_pubmed_for_year(
    query: str,
    year: int,
    max_results: int,
) -> list[str]:
    """
    Search PubMed for papers indexed to one publication year.
    """

    if max_results <= 0:
        return []

    year_query = (
        f"({query}) AND "
        f'("{year}/01/01"[Date - Publication] : '
        f'"{year}/12/31"[Date - Publication])'
    )

    with Entrez.esearch(
        db="pubmed",
        term=year_query,
        retmax=max_results,
        sort="pub date",
    ) as handle:
        results = Entrez.read(handle)

    return list(
        results.get(
            "IdList",
            [],
        )
    )


def search_pubmed(
    query: str,
    max_results: int,
    years_back: int,
) -> dict[str, int]:
    """
    Collect a balanced set of PubMed IDs across years.

    Returns:
        Dictionary mapping PMID -> sampled publication year.
    """

    if years_back <= 0:
        raise ValueError(
            "years_back must be greater than zero."
        )

    if max_results <= 0:
        raise ValueError(
            "max_results must be greater than zero."
        )

    current_year = datetime.now().year

    start_year = (
        current_year
        - years_back
        + 1
    )

    years = list(
        range(
            start_year,
            current_year + 1,
        )
    )

    base_per_year = (
        max_results
        // len(years)
    )

    remainder = (
        max_results
        % len(years)
    )

    pmid_year_map: dict[str, int] = {}

    print(
        "\nBalanced PubMed sampling by year"
    )

    print("-" * 45)

    for index, year in enumerate(years):

        extra = (
            1
            if (
                remainder > 0
                and index
                >= len(years) - remainder
            )
            else 0
        )

        year_limit = (
            base_per_year
            + extra
        )

        article_ids = search_pubmed_for_year(
            query=query,
            year=year,
            max_results=year_limit,
        )

        print(
            f"{year}: "
            f"{len(article_ids)} papers "
            f"(requested {year_limit})"
        )

        for pmid in article_ids:
            pmid_year_map.setdefault(
                str(pmid),
                year,
            )

    return pmid_year_map


def extract_journal_year(
    article_info: dict,
) -> str:
    """
    Extract the journal issue year.

    This is retained separately for reference.
    The analysis Year is based on the PubMed
    year used during balanced sampling.
    """

    pub_date = (
        article_info
        .get("Journal", {})
        .get("JournalIssue", {})
        .get("PubDate", {})
    )

    if "Year" in pub_date:
        return str(
            pub_date["Year"]
        )

    if "MedlineDate" in pub_date:
        return str(
            pub_date["MedlineDate"]
        )[:4]

    return "Unknown"


def extract_authors(
    article_info: dict,
) -> str:
    """Extract author names."""

    authors = []

    for author in article_info.get(
        "AuthorList",
        [],
    ):
        first_name = str(
            author.get(
                "ForeName",
                "",
            )
        )

        last_name = str(
            author.get(
                "LastName",
                "",
            )
        )

        full_name = (
            f"{first_name} {last_name}"
            .strip()
        )

        if full_name:
            authors.append(
                full_name
            )

    if not authors:
        return "Unknown"

    return "; ".join(authors)


def extract_abstract(
    article_info: dict,
) -> str:
    """Extract article abstract."""

    abstract_sections = (
        article_info
        .get("Abstract", {})
        .get("AbstractText", [])
    )

    if not abstract_sections:
        return "No abstract available"

    return " ".join(
        str(section)
        for section in abstract_sections
    )


def fetch_article_batch(
    article_ids: list[str],
    pmid_year_map: dict[str, int],
) -> list[dict]:
    """Fetch one batch of PubMed article records."""

    if not article_ids:
        return []

    with Entrez.efetch(
        db="pubmed",
        id=",".join(article_ids),
        rettype="medline",
        retmode="xml",
    ) as handle:
        records = Entrez.read(handle)

    articles = []

    for record in records.get(
        "PubmedArticle",
        [],
    ):
        citation = record[
            "MedlineCitation"
        ]

        article_info = citation[
            "Article"
        ]

        pmid = str(
            citation["PMID"]
        )

        sampled_year = (
            pmid_year_map.get(
                pmid
            )
        )

        articles.append(
            {
                "PMID": pmid,

                "Title": str(
                    article_info.get(
                        "ArticleTitle",
                        "Unknown",
                    )
                ),

                "Authors": extract_authors(
                    article_info
                ),

                "Journal": str(
                    article_info
                    .get("Journal", {})
                    .get(
                        "Title",
                        "Unknown",
                    )
                ),

                # This is the year used by GENESIS
                # for balanced publication analysis.
                "Year": sampled_year,

                # Keep journal issue year separately
                # for transparency.
                "Journal_Year":
                    extract_journal_year(
                        article_info
                    ),

                "Abstract":
                    extract_abstract(
                        article_info
                    ),
            }
        )

    return articles


def fetch_articles(
    pmid_year_map: dict[str, int],
    batch_size: int = 25,
) -> pd.DataFrame:
    """
    Fetch PubMed records in smaller batches.

    Batch retrieval is more reliable than requesting
    a large list of records in one call.
    """

    columns = [
        "PMID",
        "Title",
        "Authors",
        "Journal",
        "Year",
        "Journal_Year",
        "Abstract",
    ]

    article_ids = list(
        pmid_year_map.keys()
    )

    if not article_ids:
        return pd.DataFrame(
            columns=columns
        )

    articles = []

    total_ids = len(article_ids)

    for start in range(
        0,
        total_ids,
        batch_size,
    ):
        batch = article_ids[
            start:
            start + batch_size
        ]

        batch_articles = (
            fetch_article_batch(
                article_ids=batch,
                pmid_year_map=
                    pmid_year_map,
            )
        )

        articles.extend(
            batch_articles
        )

        print(
            f"Fetched "
            f"{min(start + batch_size, total_ids)}"
            f"/{total_ids} PubMed IDs"
        )

    dataframe = pd.DataFrame(
        articles,
        columns=columns,
    )

    if dataframe.empty:
        return dataframe

    dataframe = (
        dataframe
        .drop_duplicates(
            subset=["PMID"]
        )
        .reset_index(
            drop=True
        )
    )

    return dataframe


def create_filename(
    query: str,
) -> str:
    """Convert disease query into a safe filename."""

    safe_name = (
        query.lower()
        .replace(
            " disease",
            "",
        )
        .replace(
            " ",
            "_",
        )
        .replace(
            "/",
            "_",
        )
        .strip()
    )

    return (
        f"{safe_name}"
        "_recent_articles.csv"
    )


def collect_pubmed_articles(
    query: str,
    years_back: int,
    max_results: int,
) -> Path | None:
    """
    Run balanced PubMed collection.
    """

    current_year = datetime.now().year

    start_year = (
        current_year
        - years_back
        + 1
    )

    print(
        f"\nSearching PubMed for "
        f"'{query}'"
    )

    print(
        f"Target period: "
        f"{start_year}–{current_year}"
    )

    print(
        f"Target total papers: "
        f"{max_results}"
    )

    pmid_year_map = search_pubmed(
        query=query,
        max_results=max_results,
        years_back=years_back,
    )

    if not pmid_year_map:
        print(
            "\nNo recent papers were found."
        )
        return None

    print(
        f"\nUnique PubMed IDs collected: "
        f"{len(pmid_year_map)}"
    )

    print(
        "\nDownloading article details..."
    )

    articles = fetch_articles(
        pmid_year_map=
            pmid_year_map
    )

    if articles.empty:
        print(
            "\nNo article details "
            "could be retrieved."
        )
        return None

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RAW_DATA_DIR
        / create_filename(
            query
        )
    )

    articles.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nRetrieved "
        f"{len(articles)} papers."
    )

    print(
        f"Dataset saved to: "
        f"{output_path}"
    )

    year_counts = (
        articles["Year"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
    )

    print(
        "\nFinal balanced papers "
        "by analysis year"
    )

    print("-" * 45)

    for year, count in year_counts.items():
        print(
            f"{year}: {count}"
        )

    return output_path


def main() -> None:
    """Run the default PubMed collection."""

    current_year = datetime.now().year

    start_year = (
        current_year
        - DEFAULT_YEARS_BACK
        + 1
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "PROJECT GENESIS — "
        "BALANCED PUBMED COLLECTOR"
    )

    print(
        "=" * 60
    )

    print(
        f"\nDefault disease: "
        f"{DEFAULT_DISEASE_QUERY}"
    )

    print(
        f"Year range: "
        f"{start_year}–{current_year}"
    )

    print(
        f"Maximum papers: "
        f"{DEFAULT_MAX_RESULTS}"
    )

    collect_pubmed_articles(
        query=DEFAULT_DISEASE_QUERY,
        years_back=
            DEFAULT_YEARS_BACK,
        max_results=
            DEFAULT_MAX_RESULTS,
    )


if __name__ == "__main__":
    main()