from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def calculate_gene_scores(
    gene_summary: pd.DataFrame,
    ncbi_genes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate an explainable evidence score for each official NCBI gene.

    Scoring method:
    - 50 base points for appearing in the official NCBI Gene results.
    - 10 additional points for each paper in the recent PubMed sample
      that mentions the gene.

    The score is a research-prioritization signal. It does not prove
    biological importance, disease causality, or clinical relevance.
    """

    result_columns = [
        "Rank",
        "Symbol",
        "Paper_Count",
        "Evidence_Score",
        "Chromosome",
    ]

    if ncbi_genes.empty:
        return pd.DataFrame(columns=result_columns)

    scored = ncbi_genes.copy()

    required_ncbi_columns = {
        "Symbol",
        "Chromosome",
    }

    missing_ncbi_columns = required_ncbi_columns.difference(
        scored.columns
    )

    if missing_ncbi_columns:
        raise ValueError(
            "NCBI gene data is missing these columns: "
            + ", ".join(sorted(missing_ncbi_columns))
        )

    scored["Symbol"] = (
        scored["Symbol"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if gene_summary.empty:
        scored["Paper_Count"] = 0

    else:
        required_summary_columns = {
            "Gene",
            "Paper_Count",
        }

        missing_summary_columns = (
            required_summary_columns.difference(
                gene_summary.columns
            )
        )

        if missing_summary_columns:
            raise ValueError(
                "Gene summary data is missing these columns: "
                + ", ".join(
                    sorted(missing_summary_columns)
                )
            )

        literature_data = gene_summary[
            ["Gene", "Paper_Count"]
        ].copy()

        literature_data["Gene"] = (
            literature_data["Gene"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        literature_data["Paper_Count"] = pd.to_numeric(
            literature_data["Paper_Count"],
            errors="coerce",
        ).fillna(0)

        scored = scored.merge(
            literature_data,
            how="left",
            left_on="Symbol",
            right_on="Gene",
        )

        scored["Paper_Count"] = (
            scored["Paper_Count"]
            .fillna(0)
            .astype(int)
        )

    scored["Evidence_Score"] = (
        50
        + scored["Paper_Count"] * 10
    )

    scored = scored.sort_values(
        by=[
            "Evidence_Score",
            "Paper_Count",
            "Symbol",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(drop=True)

    scored["Rank"] = range(
        1,
        len(scored) + 1,
    )

    result = scored[
        result_columns
    ].copy()

    return result


def save_gene_scores(
    scored_genes: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save the ranked gene evidence table as a CSV file."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scored_genes.to_csv(
        output_path,
        index=False,
    )


def run_gene_scoring(
    disease_id: str,
) -> Path:
    """
    Calculate and save scores for one disease dataset.

    Example disease IDs:
    - alzheimer
    - parkinson
    """

    processed_directory = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / disease_id
    )

    gene_summary_path = (
        processed_directory
        / "gene_summary.csv"
    )

    ncbi_genes_path = (
        processed_directory
        / "ncbi_gene_results.csv"
    )

    output_path = (
        processed_directory
        / "gene_scores.csv"
    )

    if not ncbi_genes_path.exists():
        raise FileNotFoundError(
            "NCBI gene results were not found: "
            f"{ncbi_genes_path}"
        )

    ncbi_genes = pd.read_csv(
        ncbi_genes_path
    )

    if gene_summary_path.exists():
        gene_summary = pd.read_csv(
            gene_summary_path
        )
    else:
        gene_summary = pd.DataFrame(
            columns=[
                "Gene",
                "Paper_Count",
            ]
        )

    scored_genes = calculate_gene_scores(
        gene_summary=gene_summary,
        ncbi_genes=ncbi_genes,
    )

    save_gene_scores(
        scored_genes=scored_genes,
        output_path=output_path,
    )

    print("\n" + "=" * 60)
    print("PROJECT GENESIS — GENE EVIDENCE SCORING")
    print("=" * 60)

    print(f"\nDisease dataset: {disease_id}")

    if scored_genes.empty:
        print("\nNo official genes were available to score.")
    else:
        print(
            "\n"
            + scored_genes.to_string(
                index=False
            )
        )

    print(f"\nSaved to: {output_path}")

    return output_path


def main() -> None:
    """Run the scoring module from the terminal."""

    disease_id = "alzheimer"

    try:
        run_gene_scoring(
            disease_id=disease_id
        )

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
    ) as error:
        print(f"\nGene scoring failed: {error}")


if __name__ == "__main__":
    main()