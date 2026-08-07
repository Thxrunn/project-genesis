from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def classify_gap_status(
    paper_count: int,
) -> str:
    """Classify recent literature coverage for a gene."""

    if paper_count == 0:
        return "Underrepresented in recent sample"

    if paper_count <= 2:
        return "Limited recent coverage"

    return "Higher recent coverage"


def calculate_research_gaps(
    gene_scores: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identify official genes with comparatively low coverage
    in the recent PubMed sample.

    This is a research-gap signal only. It does not prove that
    a gene is scientifically neglected or clinically important.
    """

    output_columns = [
        "Rank",
        "Symbol",
        "Paper_Count",
        "Evidence_Score",
        "Gap_Status",
        "Gap_Priority",
    ]

    if gene_scores.empty:
        return pd.DataFrame(
            columns=output_columns
        )

    required_columns = {
        "Rank",
        "Symbol",
        "Paper_Count",
        "Evidence_Score",
    }

    missing_columns = required_columns.difference(
        gene_scores.columns
    )

    if missing_columns:
        raise ValueError(
            "Gene score data is missing these columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    gaps = gene_scores.copy()

    gaps["Paper_Count"] = pd.to_numeric(
        gaps["Paper_Count"],
        errors="coerce",
    ).fillna(0).astype(int)

    gaps["Evidence_Score"] = pd.to_numeric(
        gaps["Evidence_Score"],
        errors="coerce",
    ).fillna(0)

    gaps["Gap_Status"] = gaps[
        "Paper_Count"
    ].apply(
        classify_gap_status
    )

    gaps["Gap_Priority"] = (
        100
        - gaps["Paper_Count"] * 20
    ).clip(
        lower=0,
        upper=100,
    )

    gaps = gaps.sort_values(
        by=[
            "Gap_Priority",
            "Evidence_Score",
            "Symbol",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(drop=True)

    gaps["Rank"] = range(
        1,
        len(gaps) + 1,
    )

    return gaps[
        output_columns
    ].copy()


def save_research_gaps(
    research_gaps: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save research-gap results as a CSV file."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    research_gaps.to_csv(
        output_path,
        index=False,
    )


def run_research_gap_analysis(
    disease_id: str,
) -> Path:
    """Run research-gap analysis for one disease."""

    processed_directory = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / disease_id
    )

    gene_scores_path = (
        processed_directory
        / "gene_scores.csv"
    )

    output_path = (
        processed_directory
        / "research_gaps.csv"
    )

    if not gene_scores_path.exists():
        raise FileNotFoundError(
            "Gene score data was not found: "
            f"{gene_scores_path}"
        )

    gene_scores = pd.read_csv(
        gene_scores_path
    )

    research_gaps = calculate_research_gaps(
        gene_scores
    )

    save_research_gaps(
        research_gaps=research_gaps,
        output_path=output_path,
    )

    print("\n" + "=" * 60)
    print("PROJECT GENESIS — RESEARCH GAP FINDER")
    print("=" * 60)

    print(f"\nDisease dataset: {disease_id}")

    if research_gaps.empty:
        print(
            "\nNo gene evidence was available "
            "for research-gap analysis."
        )
    else:
        print(
            "\n"
            + research_gaps.to_string(
                index=False
            )
        )

    print(f"\nSaved to: {output_path}")

    return output_path


def main() -> None:
    """Run the research-gap finder from the terminal."""

    disease_id = "alzheimer"

    try:
        run_research_gap_analysis(
            disease_id=disease_id
        )

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
    ) as error:
        print(
            f"\nResearch-gap analysis failed: "
            f"{error}"
        )


if __name__ == "__main__":
    main()