import re
from collections import Counter
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)

PROCESSED_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def load_articles(
    disease_id: str,
) -> pd.DataFrame:
    """Load the recent PubMed dataset for a disease."""

    input_file = (
        RAW_DATA_DIR
        / f"{disease_id}_recent_articles.csv"
    )

    if not input_file.exists():
        raise FileNotFoundError(
            f"Article dataset not found: {input_file}"
        )

    dataframe = pd.read_csv(input_file)

    required_columns = {
        "PMID",
        "Title",
        "Abstract",
    }

    missing_columns = required_columns.difference(
        dataframe.columns
    )

    if missing_columns:
        raise ValueError(
            "Article dataset is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    return dataframe


def load_official_genes(
    disease_id: str,
) -> set[str]:
    """
    Load official disease-associated gene symbols
    from the NCBI Gene results.
    """

    gene_file = (
        PROCESSED_DATA_DIR
        / disease_id
        / "ncbi_gene_results.csv"
    )

    if not gene_file.exists():
        raise FileNotFoundError(
            f"NCBI Gene results not found: {gene_file}"
        )

    dataframe = pd.read_csv(gene_file)

    if dataframe.empty:
        return set()

    if "Symbol" not in dataframe.columns:
        raise ValueError(
            "NCBI Gene results do not contain "
            "a Symbol column."
        )

    symbols = (
        dataframe["Symbol"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    symbols = symbols[
        symbols != ""
    ]

    return set(symbols.tolist())


def normalize_text(text: str) -> str:
    """Remove simple HTML and normalize whitespace."""

    text = re.sub(
        r"<[^>]+>",
        " ",
        str(text),
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def extract_genes_from_text(
    text: str,
    known_genes: set[str],
) -> list[str]:
    """
    Find official disease-associated genes
    inside article text.
    """

    if not known_genes:
        return []

    normalized_text = normalize_text(text)

    genes_found = []

    for gene in known_genes:

        pattern = (
            r"(?<![A-Za-z0-9])"
            + re.escape(gene)
            + r"(?![A-Za-z0-9])"
        )

        if re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE,
        ):
            genes_found.append(gene)

    return sorted(
        set(genes_found)
    )


def analyze_gene_mentions(
    articles: pd.DataFrame,
    known_genes: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract genes per paper and count paper coverage."""

    article_gene_rows = []
    gene_counter = Counter()

    for _, article in articles.iterrows():

        title = str(
            article.get(
                "Title",
                "",
            )
        )

        abstract = str(
            article.get(
                "Abstract",
                "",
            )
        )

        combined_text = (
            f"{title} {abstract}"
        )

        genes = extract_genes_from_text(
            text=combined_text,
            known_genes=known_genes,
        )

        for gene in genes:

            article_gene_rows.append(
                {
                    "PMID": str(
                        article["PMID"]
                    ),
                    "Title": title,
                    "Gene": gene,
                }
            )

            # Count each gene once per paper.
            gene_counter[gene] += 1

    gene_mentions = pd.DataFrame(
        article_gene_rows,
        columns=[
            "PMID",
            "Title",
            "Gene",
        ],
    )

    gene_summary = pd.DataFrame(
        gene_counter.most_common(),
        columns=[
            "Gene",
            "Paper_Count",
        ],
    )

    return (
        gene_mentions,
        gene_summary,
    )


def save_gene_results(
    disease_id: str,
    gene_mentions: pd.DataFrame,
    gene_summary: pd.DataFrame,
) -> None:
    """Save disease-specific literature gene results."""

    output_directory = (
        PROCESSED_DATA_DIR
        / disease_id
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    gene_mentions.to_csv(
        output_directory
        / "gene_mentions.csv",
        index=False,
    )

    gene_summary.to_csv(
        output_directory
        / "gene_summary.csv",
        index=False,
    )


def run_gene_extraction(
    disease_id: str,
) -> dict:
    """
    Run dynamic gene extraction for one disease.

    Gene symbols come from that disease's
    NCBI Gene results instead of a hard-coded list.
    """

    articles = load_articles(
        disease_id
    )

    official_genes = load_official_genes(
        disease_id
    )

    (
        gene_mentions,
        gene_summary,
    ) = analyze_gene_mentions(
        articles=articles,
        known_genes=official_genes,
    )

    save_gene_results(
        disease_id=disease_id,
        gene_mentions=gene_mentions,
        gene_summary=gene_summary,
    )

    papers_with_genes = (
        gene_mentions["PMID"].nunique()
        if not gene_mentions.empty
        else 0
    )

    print("\n" + "=" * 60)
    print("PROJECT GENESIS — DYNAMIC GENE EXTRACTION")
    print("=" * 60)

    print(
        f"\nDisease: {disease_id}"
    )

    print(
        f"Official NCBI genes loaded: "
        f"{len(official_genes)}"
    )

    print(
        f"Papers analyzed: "
        f"{len(articles)}"
    )

    print(
        f"Papers containing official genes: "
        f"{papers_with_genes}"
    )

    print("\nGENE LITERATURE COVERAGE")
    print("-" * 40)

    if gene_summary.empty:
        print(
            "None of the official genes were found "
            "in this recent PubMed sample."
        )

    else:
        print(
            gene_summary.to_string(
                index=False
            )
        )

    print(
        "\nResults saved inside: "
        f"data/processed/{disease_id}/"
    )

    return {
        "disease_id": disease_id,
        "official_gene_count": len(
            official_genes
        ),
        "papers_analyzed": len(
            articles
        ),
        "papers_with_genes":
            papers_with_genes,
        "gene_mentions":
            gene_mentions,
        "gene_summary":
            gene_summary,
    }


def main() -> None:
    """Terminal test."""

    disease_id = "alzheimer"

    try:
        run_gene_extraction(
            disease_id=disease_id
        )

    except (
        FileNotFoundError,
        ValueError,
    ) as error:

        print(
            f"\nGene extraction failed: "
            f"{error}"
        )


if __name__ == "__main__":
    main()