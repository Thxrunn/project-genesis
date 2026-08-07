from pathlib import Path

from src.analysis.disease_profile import build_profile
from src.analysis.gene_extractor import run_gene_extraction
from src.analysis.gene_scoring import run_gene_scoring
from src.analysis.research_explorer import analyze_research
from src.analysis.research_gap import run_research_gap_analysis

from src.collectors.ncbi_gene_collector import collect_ncbi_genes
from src.collectors.pubmed_collector import collect_pubmed_articles

from src.config import (
    APP_NAME,
    DEFAULT_DISEASE_QUERY,
    DEFAULT_MAX_RESULTS,
    DEFAULT_YEARS_BACK,
)


def create_disease_id(
    disease_query: str,
) -> str:
    """
    Convert a disease query into the identifier
    used by Project GENESIS file names.

    Example:
        Alzheimer disease -> alzheimer
        Parkinson disease -> parkinson
    """

    return (
        disease_query.lower()
        .replace(" disease", "")
        .replace(" ", "_")
        .replace("/", "_")
        .strip()
    )


def get_user_settings() -> tuple[str, int, int]:
    """Ask the user for pipeline settings."""

    print("\nEnter a disease to research.")

    print(
        f"Press Enter to use the default: "
        f"{DEFAULT_DISEASE_QUERY}"
    )

    disease_query = input(
        "\nDisease: "
    ).strip()

    if not disease_query:
        disease_query = DEFAULT_DISEASE_QUERY

    years_input = input(
        f"Years of recent research "
        f"[default {DEFAULT_YEARS_BACK}]: "
    ).strip()

    results_input = input(
        f"Maximum number of papers "
        f"[default {DEFAULT_MAX_RESULTS}]: "
    ).strip()

    try:
        years_back = (
            int(years_input)
            if years_input
            else DEFAULT_YEARS_BACK
        )

        max_results = (
            int(results_input)
            if results_input
            else DEFAULT_MAX_RESULTS
        )

        if years_back <= 0:
            raise ValueError(
                "Years must be greater than zero."
            )

        if max_results <= 0:
            raise ValueError(
                "Maximum results must be greater than zero."
            )

    except ValueError as error:
        print(
            f"\nInvalid input: {error}"
        )

        print(
            "Default settings will be used."
        )

        years_back = DEFAULT_YEARS_BACK
        max_results = DEFAULT_MAX_RESULTS

    return (
        disease_query,
        years_back,
        max_results,
    )


def display_pipeline_header(
    disease_query: str,
    years_back: int,
    max_results: int,
) -> None:
    """Display selected pipeline settings."""

    print("\n" + "=" * 60)

    print(APP_NAME.upper())

    print(
        "BIOMEDICAL RESEARCH INTELLIGENCE PIPELINE"
    )

    print("=" * 60)

    print(
        f"\nDisease: {disease_query}"
    )

    print(
        f"Recent years: {years_back}"
    )

    print(
        f"Maximum papers: {max_results}"
    )


def run_pipeline(
    disease_query: str,
    years_back: int,
    max_results: int,
) -> Path | None:
    """
    Run the complete Project GENESIS pipeline.
    """

    disease_id = create_disease_id(
        disease_query
    )

    display_pipeline_header(
        disease_query=disease_query,
        years_back=years_back,
        max_results=max_results,
    )

    # -------------------------------------------------
    # STEP 1
    # -------------------------------------------------

    print(
        "\n[1/7] Collecting recent PubMed papers..."
    )

    dataset_path = collect_pubmed_articles(
        query=disease_query,
        years_back=years_back,
        max_results=max_results,
    )

    if dataset_path is None:
        print(
            "\nPipeline stopped because no "
            "papers were collected."
        )

        return None

    # -------------------------------------------------
    # STEP 2
    # -------------------------------------------------

    print(
        "\n[2/7] Analyzing research trends..."
    )

    research_results = analyze_research(
        input_file=dataset_path,
        display_results=False,
    )

    print(
        f"Research analysis completed for "
        f"{research_results['total_papers']} papers."
    )

    # -------------------------------------------------
    # STEP 3
    # -------------------------------------------------

    print(
        "\n[3/7] Collecting official NCBI Gene records..."
    )

    ncbi_results = collect_ncbi_genes(
        disease_query=disease_query,
        max_results=20,
        display_results=False,
    )

    print(
        f"Official NCBI genes retrieved: "
        f"{ncbi_results['genes_retrieved']}"
    )

    # -------------------------------------------------
    # STEP 4
    # -------------------------------------------------

    print(
        "\n[4/7] Extracting gene mentions "
        "from recent literature..."
    )

    gene_results = run_gene_extraction(
        disease_id=disease_id
    )

    print(
        f"Official genes loaded: "
        f"{gene_results['official_gene_count']}"
    )

    print(
        f"Papers containing official genes: "
        f"{gene_results['papers_with_genes']}"
    )

    # -------------------------------------------------
    # STEP 5
    # -------------------------------------------------

    print(
        "\n[5/7] Calculating gene evidence scores..."
    )

    run_gene_scoring(
        disease_id=disease_id
    )

    # -------------------------------------------------
    # STEP 6
    # -------------------------------------------------

    print(
        "\n[6/7] Identifying potential research gaps..."
    )

    run_research_gap_analysis(
        disease_id=disease_id
    )

    # -------------------------------------------------
    # STEP 7
    # -------------------------------------------------

    print(
        "\n[7/7] Building disease research profile..."
    )

    build_profile(
        dataset_path
    )

    # -------------------------------------------------
    # COMPLETE
    # -------------------------------------------------

    print("\n" + "=" * 60)

    print(
        "PROJECT GENESIS PIPELINE COMPLETED SUCCESSFULLY"
    )

    print("=" * 60)

    print(
        f"\nDisease: {disease_query}"
    )

    print(
        f"Dataset: {dataset_path}"
    )

    print(
        f"Processed results: "
        f"data/processed/{disease_id}/"
    )

    print(
        "\nYou can now launch the dashboard with:"
    )

    print(
        "streamlit run app/dashboard.py"
    )

    return dataset_path


def main() -> None:
    """Start Project GENESIS."""

    try:
        (
            disease_query,
            years_back,
            max_results,
        ) = get_user_settings()

        run_pipeline(
            disease_query=disease_query,
            years_back=years_back,
            max_results=max_results,
        )

    except KeyboardInterrupt:
        print(
            "\n\nPipeline cancelled by the user."
        )

    except (
        FileNotFoundError,
        ValueError,
        KeyError,
    ) as error:
        print(
            f"\nPipeline error: {error}"
        )

    except Exception as error:
        print(
            "\nAn unexpected error occurred: "
            f"{error}"
        )


if __name__ == "__main__":
    main()