from __future__ import annotations

from pathlib import Path

import pandas as pd
from Bio import Entrez

from src.config import PROCESSED_DATA_DIR


Entrez.email = "thxrun2025@gmail.com"


def search_ncbi_genes(
    disease_query: str,
    max_results: int = 20,
) -> list[str]:
    """
    Search NCBI Gene for human genes associated with a disease.

    Returns:
        A list of NCBI Gene IDs.
    """

    search_term = (
    f'("{disease_query}"[Disease Name]) '
    f'AND "Homo sapiens"[Organism]'
)

    with Entrez.esearch(
        db="gene",
        term=search_term,
        retmax=max_results,
        sort="relevance",
    ) as handle:
        results = Entrez.read(handle)

    return list(results.get("IdList", []))


def fetch_gene_summaries(
    gene_ids: list[str],
) -> pd.DataFrame:
    """
    Retrieve official summaries for NCBI Gene IDs.
    """

    columns = [
        "Gene_ID",
        "Symbol",
        "Name",
        "Description",
        "Chromosome",
        "Map_Location",
        "Organism",
        "Summary",
    ]

    if not gene_ids:
        return pd.DataFrame(columns=columns)

    with Entrez.esummary(
        db="gene",
        id=",".join(gene_ids),
        retmode="xml",
    ) as handle:
        records = Entrez.read(handle)

    genes = []

    document_summaries = records.get(
        "DocumentSummarySet",
        {},
    ).get(
        "DocumentSummary",
        [],
    )

    for record in document_summaries:
        genes.append(
            {
                "Gene_ID": str(
                    record.attributes.get(
                        "uid",
                        "",
                    )
                ),
                "Symbol": str(
                    record.get(
                        "Name",
                        "Unknown",
                    )
                ),
                "Name": str(
                    record.get(
                        "Description",
                        "Unknown",
                    )
                ),
                "Description": str(
                    record.get(
                        "Description",
                        "Unknown",
                    )
                ),
                "Chromosome": str(
                    record.get(
                        "Chromosome",
                        "Unknown",
                    )
                ),
                "Map_Location": str(
                    record.get(
                        "MapLocation",
                        "Unknown",
                    )
                ),
                "Organism": str(
                    record.get(
                        "Organism",
                        {},
                    ).get(
                        "ScientificName",
                        "Unknown",
                    )
                ),
                "Summary": str(
                    record.get(
                        "Summary",
                        "No summary available",
                    )
                ),
            }
        )

    return pd.DataFrame(
        genes,
        columns=columns,
    )


def create_disease_id(
    disease_query: str,
) -> str:
    """Convert a disease query into a safe identifier."""

    return (
        disease_query.lower()
        .replace(" disease", "")
        .replace(" ", "_")
        .replace("/", "_")
    )
def filter_gene_records(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Remove mapped disease loci and incomplete phenotype records.

    Keeps records that look like usable human gene entries.
    """

    if dataframe.empty:
        return dataframe.copy()

    filtered = dataframe.copy()

    filtered["Symbol"] = (
        filtered["Symbol"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    filtered["Summary"] = (
        filtered["Summary"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    filtered["Chromosome"] = (
        filtered["Chromosome"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    filtered["Map_Location"] = (
        filtered["Map_Location"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Remove phenotype-style records such as AD5, AD10 and AD17.
    phenotype_pattern = r"^AD\d+$"

    filtered = filtered[
        ~filtered["Symbol"].str.match(
            phenotype_pattern,
            case=False,
            na=False,
        )
    ]

    # Require a usable chromosome, map location and biological summary.
    filtered = filtered[
        (filtered["Chromosome"] != "")
        & (filtered["Map_Location"] != "")
        & (filtered["Summary"] != "")
    ]

    return filtered.reset_index(drop=True)

def save_gene_data(
    dataframe: pd.DataFrame,
    disease_query: str,
) -> Path:
    """Save official gene results."""

    disease_id = create_disease_id(
        disease_query
    )

    output_directory = (
        PROCESSED_DATA_DIR
        / disease_id
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_directory
        / "ncbi_gene_results.csv"
    )

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path


def collect_ncbi_genes(
    disease_query: str,
    max_results: int = 20,
    display_results: bool = True,
) -> dict:
    """Run the complete NCBI Gene collection process."""

    gene_ids = search_ncbi_genes(
        disease_query=disease_query,
        max_results=max_results,
    )

    gene_dataframe = fetch_gene_summaries(
        gene_ids
    )

    filtered_gene_dataframe = filter_gene_records(
    gene_dataframe
)

    output_path = save_gene_data(
    dataframe=filtered_gene_dataframe,
    disease_query=disease_query,
)

    results = {
    "disease_query": disease_query,
    "gene_ids_found": len(gene_ids),
    "genes_retrieved": len(gene_dataframe),
    "genes_after_filtering": len(
        filtered_gene_dataframe
    ),
    "genes": filtered_gene_dataframe,
    "output_path": output_path,
}

    if display_results:
        print_gene_results(results)

    return results


def print_gene_results(
    results: dict,
) -> None:
    """Display NCBI Gene results."""

    print("\n" + "=" * 60)
    print("PROJECT GENESIS — NCBI GENE COLLECTOR")
    print("=" * 60)

    print(
        f"\nDisease query: "
        f"{results['disease_query']}"
    )

    print(
        f"Gene IDs found: "
        f"{results['gene_ids_found']}"
    )

    print(
        f"Gene records retrieved: "
        f"{results['genes_retrieved']}"
    )

    print(
    f"Usable genes after filtering: "
    f"{results['genes_after_filtering']}"
)

    print("\nOFFICIAL GENE RESULTS")
    print("-" * 60)

    genes = results["genes"]

    if genes.empty:
        print("No NCBI Gene records were found.")
    else:
        display_columns = [
            "Gene_ID",
            "Symbol",
            "Name",
            "Chromosome",
            "Map_Location",
        ]

        print(
            genes[display_columns].to_string(
                index=False
            )
        )

    print(
        f"\nSaved to: "
        f"{results['output_path']}"
    )


def main() -> None:
    """Test the collector from the terminal."""

    disease_query = "Alzheimer disease"

    try:
        collect_ncbi_genes(
            disease_query=disease_query,
            max_results=20,
        )

    except Exception as error:
        print(
            "\nNCBI Gene collection failed: "
            f"{error}"
        )


if __name__ == "__main__":
    main()