import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.ai.research_summary import generate_summary
from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


st.set_page_config(
    page_title="Project GENESIS",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .genesis-header {
        padding: 2rem;
        border-radius: 18px;
        background: linear-gradient(
            120deg,
            #102a43,
            #176b87
        );
        color: white;
        margin-bottom: 1.5rem;
    }

    .genesis-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }

    .genesis-header p {
        margin-top: 0.7rem;
        margin-bottom: 0;
        font-size: 1.05rem;
        opacity: 0.92;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e6e9ef;
        padding: 1rem;
        border-radius: 14px;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }

    .summary-box {
        background-color: #eaf4ff;
        border-left: 5px solid #176b87;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
"""


EXPECTED_GENE_COLUMNS = [
    "Gene_ID",
    "Symbol",
    "Name",
    "Description",
    "Chromosome",
    "Map_Location",
    "Organism",
    "Summary",
]


def get_available_diseases() -> dict[str, Path]:
    """Find all disease datasets collected from PubMed."""

    disease_files = sorted(
        RAW_DATA_DIR.glob("*_recent_articles.csv")
    )

    diseases: dict[str, Path] = {}

    for file_path in disease_files:
        disease_id = file_path.stem.replace(
            "_recent_articles",
            "",
        )

        display_name = (
            disease_id
            .replace("_", " ")
            .title()
        )

        diseases[display_name] = file_path

    return diseases


@st.cache_data
def load_csv(file_path: Path) -> pd.DataFrame:
    """Load a CSV file safely."""

    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)

    except Exception as error:
        st.error(
            f"Could not load {file_path.name}: {error}"
        )
        return pd.DataFrame()


def ensure_gene_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ensure the expected NCBI Gene columns exist.

    This prevents crashes when official gene data has not yet
    been collected for a disease such as Parkinson.
    """

    if dataframe.empty:
        return pd.DataFrame(
            columns=EXPECTED_GENE_COLUMNS
        )

    safe_dataframe = dataframe.copy()

    for column in EXPECTED_GENE_COLUMNS:
        if column not in safe_dataframe.columns:
            safe_dataframe[column] = pd.NA

    return safe_dataframe[
        EXPECTED_GENE_COLUMNS
    ]


def display_header() -> None:
    """Display the application header."""

    st.markdown(
        """
        <div class="genesis-header">
            <h1>🧬 Project GENESIS</h1>
            <p>
                Genomic Novel Evidence & Scientific Insight System
            </p>
            <p>
                Explore recent biomedical research, disease trends,
                scientific topics, official gene evidence, and
                potential research gaps.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def calculate_summary(
    articles: pd.DataFrame,
    journals: pd.DataFrame,
    keywords: pd.DataFrame,
    official_genes: pd.DataFrame,
) -> dict:
    """Calculate dashboard summary metrics."""

    years = pd.to_numeric(
        articles.get(
            "Year",
            pd.Series(dtype=float),
        ),
        errors="coerce",
    ).dropna()

    if years.empty:
        year_range = "Unknown"
    else:
        year_range = (
            f"{int(years.min())}–"
            f"{int(years.max())}"
        )

    if "Journal" in articles.columns:
        journal_count = int(
            articles["Journal"]
            .dropna()
            .nunique()
        )
    else:
        journal_count = len(journals)

    official_gene_count = 0

    if (
        not official_genes.empty
        and "Symbol" in official_genes.columns
    ):
        official_gene_count = int(
            official_genes["Symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda values: values != ""]
            .nunique()
        )

    return {
        "total_papers": len(articles),
        "year_range": year_range,
        "journal_count": journal_count,
        "topic_count": (
            len(keywords)
            if not keywords.empty
            else 0
        ),
        "gene_count": official_gene_count,
    }


def display_metrics(summary: dict) -> None:
    """Display summary metric cards."""

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Research Papers",
        summary["total_papers"],
    )

    col2.metric(
        "Years Covered",
        summary["year_range"],
    )

    col3.metric(
        "Journals",
        summary["journal_count"],
    )

    col4.metric(
        "Research Topics",
        summary["topic_count"],
    )

    col5.metric(
        "Official Genes",
        summary["gene_count"],
    )


def display_ai_summary(ai_summary: str) -> None:
    """Display the generated research summary."""

    st.subheader("🧠 Automated Research Summary")

    formatted_summary = ai_summary.replace(
        "\n",
        "<br>",
    )

    st.markdown(
        f"""
        <div class="summary-box">
            {formatted_summary}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "This summary is generated from the selected "
        "PubMed sample and available NCBI Gene records."
    )


def display_publication_trends(
    dataframe: pd.DataFrame,
) -> None:
    """Display an interactive publication trend chart."""

    st.subheader("📈 Publication Trends")

    if dataframe.empty:
        st.info(
            "Publication trend data is unavailable."
        )
        return

    required_columns = {
        "Year",
        "Paper_Count",
    }

    if not required_columns.issubset(
        dataframe.columns
    ):
        st.warning(
            "Publication trend columns are missing."
        )
        return

    chart_data = dataframe.copy()

    chart_data["Year"] = pd.to_numeric(
        chart_data["Year"],
        errors="coerce",
    )

    chart_data["Paper_Count"] = pd.to_numeric(
        chart_data["Paper_Count"],
        errors="coerce",
    )

    chart_data = (
        chart_data
        .dropna(
            subset=[
                "Year",
                "Paper_Count",
            ]
        )
        .sort_values("Year")
    )

    if chart_data.empty:
        st.info(
            "No valid publication trend values "
            "are available."
        )
        return

    chart_data["Year"] = (
        chart_data["Year"]
        .astype(int)
        .astype(str)
    )

    figure = px.bar(
        chart_data,
        x="Year",
        y="Paper_Count",
        labels={
            "Year": "Publication Year",
            "Paper_Count": "Number of Papers",
        },
        text="Paper_Count",
    )

    figure.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>Year:</b> %{x}<br>"
            "<b>Papers:</b> %{y}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        height=350,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10,
        ),
        xaxis_title="Publication Year",
        yaxis_title="Number of Papers",
        showlegend=False,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": False,
        },
    )


def display_top_journals(
    dataframe: pd.DataFrame,
) -> None:
    """Display top journals."""

    st.subheader("📰 Leading Journals")

    if dataframe.empty:
        st.info(
            "Journal analysis is unavailable."
        )
        return

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
        height=350,
    )


def display_top_keywords(
    dataframe: pd.DataFrame,
) -> None:
    """Display interactive research-topic results."""

    st.subheader("🔎 Top Research Topics")

    if dataframe.empty:
        st.info(
            "Topic analysis is unavailable."
        )
        return

    required_columns = {
        "Keyword",
        "Frequency",
    }

    if not required_columns.issubset(
        dataframe.columns
    ):
        st.warning(
            "Research-topic columns are missing."
        )
        return

    chart_data = dataframe[
        [
            "Keyword",
            "Frequency",
        ]
    ].copy()

    chart_data["Frequency"] = pd.to_numeric(
        chart_data["Frequency"],
        errors="coerce",
    )

    chart_data = (
        chart_data
        .dropna(subset=["Frequency"])
        .head(12)
        .sort_values(
            "Frequency",
            ascending=True,
        )
    )

    if chart_data.empty:
        st.info(
            "No valid research-topic values "
            "are available."
        )
        return

    figure = px.bar(
        chart_data,
        x="Frequency",
        y="Keyword",
        orientation="h",
        labels={
            "Frequency": "Mentions",
            "Keyword": "Research Topic",
        },
        text="Frequency",
    )

    figure.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>Topic:</b> %{y}<br>"
            "<b>Mentions:</b> %{x}"
            "<extra></extra>"
        ),
    )

    figure.update_layout(
        height=440,
        margin=dict(
            l=10,
            r=35,
            t=20,
            b=10,
        ),
        xaxis_title="Number of Mentions",
        yaxis_title="",
        showlegend=False,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        config={
            "displaylogo": False,
            "scrollZoom": False,
        },
    )

    with st.expander(
        "View complete topic table"
    ):
        st.dataframe(
            dataframe,
            use_container_width=True,
            hide_index=True,
        )


def display_gene_results(
    dataframe: pd.DataFrame,
) -> None:
    """Display genes mentioned in recent papers."""

    st.subheader("📚 Literature Gene Mentions")

    if dataframe.empty:
        st.info(
            "No genes from the current starter "
            "gene list were found in the recent papers."
        )
        return

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    required_columns = {
        "Gene",
        "Paper_Count",
    }

    if required_columns.issubset(
        dataframe.columns
    ):
        chart_data = dataframe[
            [
                "Gene",
                "Paper_Count",
            ]
        ].copy()

        chart_data["Paper_Count"] = pd.to_numeric(
            chart_data["Paper_Count"],
            errors="coerce",
        )

        chart_data = (
            chart_data
            .dropna(subset=["Paper_Count"])
            .sort_values(
                "Paper_Count",
                ascending=True,
            )
        )

        figure = px.bar(
            chart_data,
            x="Paper_Count",
            y="Gene",
            orientation="h",
            labels={
                "Paper_Count": "Paper Mentions",
                "Gene": "Gene",
            },
            text="Paper_Count",
        )

        figure.update_layout(
            height=300,
            margin=dict(
                l=10,
                r=30,
                t=20,
                b=10,
            ),
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={
                "displaylogo": False,
            },
        )


def display_gene_scores(
    dataframe: pd.DataFrame,
) -> None:
    """Display interactive ranked gene evidence scores."""

    st.subheader("⭐ Gene Evidence Ranking")

    if dataframe.empty:
        st.info(
            "Gene evidence scores are not available "
            "for this disease."
        )
        return

    preferred_columns = [
        "Rank",
        "Symbol",
        "Paper_Count",
        "Evidence_Score",
        "Chromosome",
    ]

    display_columns = [
        column
        for column in preferred_columns
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    required_columns = {
        "Symbol",
        "Evidence_Score",
    }

    if required_columns.issubset(
        dataframe.columns
    ):
        chart_data = dataframe.copy()

        if "Paper_Count" not in chart_data.columns:
            chart_data["Paper_Count"] = 0

        chart_data["Evidence_Score"] = pd.to_numeric(
            chart_data["Evidence_Score"],
            errors="coerce",
        )

        chart_data["Paper_Count"] = pd.to_numeric(
            chart_data["Paper_Count"],
            errors="coerce",
        ).fillna(0)

        chart_data = (
            chart_data
            .dropna(subset=["Evidence_Score"])
            .sort_values(
                "Evidence_Score",
                ascending=True,
            )
        )

        figure = px.bar(
            chart_data,
            x="Evidence_Score",
            y="Symbol",
            orientation="h",
            text="Evidence_Score",
            custom_data=[
                "Paper_Count",
            ],
            labels={
                "Evidence_Score": "Evidence Score",
                "Symbol": "Gene",
            },
        )

        figure.update_traces(
            textposition="outside",
            hovertemplate=(
                "<b>Gene:</b> %{y}<br>"
                "<b>Evidence score:</b> %{x}<br>"
                "<b>Recent paper mentions:</b> "
                "%{customdata[0]}"
                "<extra></extra>"
            ),
        )

        figure.update_layout(
            height=400,
            margin=dict(
                l=10,
                r=35,
                t=20,
                b=10,
            ),
            xaxis_title="Evidence Score",
            yaxis_title="",
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": False,
            },
        )

    st.caption(
        "The evidence score is a transparent "
        "research-prioritization signal based on official "
        "NCBI inclusion and recent literature mentions."
    )


def display_research_gaps(
    dataframe: pd.DataFrame,
) -> None:
    """Display potential research-gap signals."""

    st.subheader("🧠 Potential Research Gaps")

    if dataframe.empty:
        st.info(
            "Research-gap results are not available "
            "for this disease."
        )
        return

    preferred_columns = [
        "Rank",
        "Symbol",
        "Paper_Count",
        "Evidence_Score",
        "Gap_Status",
        "Gap_Priority",
    ]

    display_columns = [
        column
        for column in preferred_columns
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    required_columns = {
        "Symbol",
        "Gap_Priority",
        "Paper_Count",
    }

    if required_columns.issubset(
        dataframe.columns
    ):
        chart_data = dataframe.copy()

        if "Gap_Status" not in chart_data.columns:
            chart_data["Gap_Status"] = "Unknown"

        chart_data = chart_data[
            [
                "Symbol",
                "Gap_Priority",
                "Paper_Count",
                "Gap_Status",
            ]
        ].copy()

        chart_data["Gap_Priority"] = pd.to_numeric(
            chart_data["Gap_Priority"],
            errors="coerce",
        )

        chart_data["Paper_Count"] = pd.to_numeric(
            chart_data["Paper_Count"],
            errors="coerce",
        ).fillna(0)

        chart_data = (
            chart_data
            .dropna(subset=["Gap_Priority"])
            .sort_values(
                "Gap_Priority",
                ascending=True,
            )
        )

        figure = px.bar(
            chart_data,
            x="Gap_Priority",
            y="Symbol",
            orientation="h",
            text="Gap_Priority",
            custom_data=[
                "Paper_Count",
                "Gap_Status",
            ],
            labels={
                "Gap_Priority": "Gap Priority",
                "Symbol": "Gene",
            },
        )

        figure.update_traces(
            textposition="outside",
            hovertemplate=(
                "<b>Gene:</b> %{y}<br>"
                "<b>Gap priority:</b> %{x}<br>"
                "<b>Recent paper mentions:</b> "
                "%{customdata[0]}<br>"
                "<b>Status:</b> %{customdata[1]}"
                "<extra></extra>"
            ),
        )

        figure.update_layout(
            height=400,
            margin=dict(
                l=10,
                r=35,
                t=20,
                b=10,
            ),
            xaxis_title=(
                "Potential Research-Gap Priority"
            ),
            yaxis_title="",
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
            config={
                "displaylogo": False,
                "scrollZoom": False,
            },
        )

    if {
        "Gap_Status",
        "Symbol",
    }.issubset(dataframe.columns):
        top_gap_rows = dataframe[
            dataframe["Gap_Status"]
            == "Underrepresented in recent sample"
        ]

        if not top_gap_rows.empty:
            top_genes = ", ".join(
                top_gap_rows["Symbol"]
                .astype(str)
                .head(5)
                .tolist()
            )

            st.warning(
                "Potentially underrepresented genes "
                "in the current recent-paper sample: "
                f"{top_genes}"
            )

    st.caption(
        "Research-gap signals are exploratory and do "
        "not prove scientific neglect or clinical importance."
    )


def display_official_genes(
    dataframe: pd.DataFrame,
) -> None:
    """Display official NCBI Gene records."""

    st.subheader(
        "🧬 Official Disease-Associated Genes"
    )

    if (
        dataframe.empty
        or dataframe["Symbol"].dropna().empty
    ):
        st.info(
            "Official NCBI Gene results are not "
            "available for this disease yet."
        )
        return

    preferred_columns = [
        "Symbol",
        "Name",
        "Chromosome",
        "Map_Location",
    ]

    display_columns = [
        column
        for column in preferred_columns
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    gene_options = (
        dataframe["Symbol"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    gene_options = gene_options[
        gene_options != ""
    ].tolist()

    if not gene_options:
        return

    selected_gene = st.selectbox(
        "View official gene details",
        options=gene_options,
    )

    selected_rows = dataframe[
        dataframe["Symbol"].astype(str)
        == selected_gene
    ]

    if selected_rows.empty:
        return

    selected_record = selected_rows.iloc[0]

    gene_name = selected_record.get(
        "Name",
        "Unknown",
    )

    st.markdown(
        f"### {selected_gene} — {gene_name}"
    )

    detail_col1, detail_col2, detail_col3 = (
        st.columns(3)
    )

    detail_col1.metric(
        "NCBI Gene ID",
        selected_record.get(
            "Gene_ID",
            "Unknown",
        ),
    )

    detail_col2.metric(
        "Chromosome",
        selected_record.get(
            "Chromosome",
            "Unknown",
        ),
    )

    detail_col3.metric(
        "Map Location",
        selected_record.get(
            "Map_Location",
            "Unknown",
        ),
    )

    st.write("**Official NCBI summary**")

    summary_text = selected_record.get(
        "Summary",
        "No summary available.",
    )

    if pd.isna(summary_text) or not str(
        summary_text
    ).strip():
        summary_text = "No summary available."

    st.write(str(summary_text))


def display_article_explorer(
    articles: pd.DataFrame,
) -> None:
    """Display a searchable article explorer."""

    st.subheader("📚 Research Paper Explorer")

    search_term = st.text_input(
        "Search article titles or abstracts",
        placeholder=(
            "Example: biomarker, microbiome, "
            "cognitive decline"
        ),
    )

    filtered_articles = articles.copy()

    if search_term:
        title_matches = (
            filtered_articles["Title"]
            .fillna("")
            .astype(str)
            .str.contains(
                search_term,
                case=False,
                na=False,
            )
        )

        abstract_matches = (
            filtered_articles["Abstract"]
            .fillna("")
            .astype(str)
            .str.contains(
                search_term,
                case=False,
                na=False,
            )
        )

        filtered_articles = filtered_articles[
            title_matches | abstract_matches
        ]

    display_columns = [
        column
        for column in [
            "PMID",
            "Title",
            "Journal",
            "Year",
            "Authors",
        ]
        if column in filtered_articles.columns
    ]

    st.write(
        f"Showing {len(filtered_articles)} "
        f"of {len(articles)} papers"
    )

    st.dataframe(
        filtered_articles[display_columns],
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    st.download_button(
        label="⬇ Download displayed papers",
        data=filtered_articles.to_csv(
            index=False
        ),
        file_name="genesis_research_papers.csv",
        mime="text/csv",
    )


def main() -> None:
    """Run the Project GENESIS dashboard."""

    st.markdown(
        CUSTOM_CSS,
        unsafe_allow_html=True,
    )

    display_header()

    diseases = get_available_diseases()

    if not diseases:
        st.warning(
            "No disease datasets were found. "
            "Run the GENESIS pipeline first."
        )
        return

    st.sidebar.title("Research Controls")

    selected_disease = st.sidebar.selectbox(
        "Select a disease",
        options=list(diseases.keys()),
    )

    article_file = diseases[
        selected_disease
    ]

    disease_id = article_file.stem.replace(
        "_recent_articles",
        "",
    )

    processed_directory = (
        PROCESSED_DATA_DIR
        / disease_id
    )

    articles = load_csv(
        article_file
    )

    publication_trends = load_csv(
        processed_directory
        / "publication_trends.csv"
    )

    top_journals = load_csv(
        processed_directory
        / "top_journals.csv"
    )

    top_keywords = load_csv(
        processed_directory
        / "top_keywords.csv"
    )

    gene_summary = load_csv(
        processed_directory
        / "gene_summary.csv"
    )

    ncbi_genes = ensure_gene_columns(
        load_csv(
            processed_directory
            / "ncbi_gene_results.csv"
        )
    )

    gene_scores = load_csv(
        processed_directory
        / "gene_scores.csv"
    )

    research_gaps = load_csv(
        processed_directory
        / "research_gaps.csv"
    )

    st.sidebar.success(
        f"Dataset loaded: {selected_disease}"
    )

    st.sidebar.markdown("---")

    st.sidebar.caption(
        "Project GENESIS combines recent PubMed "
        "literature, official NCBI Gene records, "
        "transparent evidence scoring, and "
        "research-gap analysis."
    )

    if articles.empty:
        st.error(
            "The selected article dataset "
            "could not be loaded."
        )
        return

    st.header(
        f"{selected_disease} Research Profile"
    )

    summary = calculate_summary(
        articles=articles,
        journals=top_journals,
        keywords=top_keywords,
        official_genes=ncbi_genes,
    )

    display_metrics(summary)

    try:
        ai_summary = generate_summary(
            disease=selected_disease,
            articles=articles,
            journals=top_journals,
            keywords=top_keywords,
            genes=ncbi_genes,
        )

    except Exception:
        ai_summary = (
            "Executive Summary\n\n"
            f"Project GENESIS analyzed "
            f"{len(articles)} recent "
            f"{selected_disease} publications. "
            "Official gene information is not yet "
            "available for this dataset.\n\n"
            "The displayed outputs are exploratory "
            "research signals and do not establish "
            "scientific novelty, disease causality, "
            "or clinical importance."
        )

    display_ai_summary(ai_summary)

    st.divider()

    left_column, right_column = st.columns(
        [1.2, 1]
    )

    with left_column:
        display_publication_trends(
            publication_trends
        )

    with right_column:
        display_top_journals(
            top_journals
        )

    st.divider()

    left_column, right_column = st.columns(
        [1.4, 1]
    )

    with left_column:
        display_top_keywords(
            top_keywords
        )

    with right_column:
        display_gene_results(
            gene_summary
        )

    st.divider()

    display_gene_scores(
        gene_scores
    )

    st.divider()

    display_research_gaps(
        research_gaps
    )

    st.divider()

    display_official_genes(
        ncbi_genes
    )

    st.divider()

    display_article_explorer(
        articles
    )

    st.divider()

    st.caption(
        "Project GENESIS is an educational biomedical "
        "research exploration tool. Its summaries, "
        "rankings, and gap signals are computational "
        "outputs based on limited public data. They do "
        "not establish disease causality, scientific "
        "novelty, clinical importance, diagnosis, or "
        "treatment recommendations."
    )


if __name__ == "__main__":
    main()