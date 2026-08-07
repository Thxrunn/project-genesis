# 🧬 Project GENESIS

### Biomedical Research Intelligence Platform

Project GENESIS is an automated biomedical research intelligence platform built with Python and Streamlit. It integrates scientific literature from PubMed with official gene information from NCBI Gene to help explore disease research trends, gene evidence, and potentially underrepresented areas of research.

The current version supports **Alzheimer disease** and **Parkinson disease** and provides an interactive dashboard for exploring biomedical literature and gene-related evidence.

> **Project Status:** v1.0 — Complete  
> **Current Diseases:** Alzheimer Disease & Parkinson Disease

---

## 🎯 Why I Built This

Biomedical research is spread across thousands of scientific publications and biological databases, making it difficult to quickly understand how research activity, disease-associated genes, and scientific literature connect.

I built Project GENESIS to explore how software engineering and data analysis can automate part of this research-discovery process.

The platform creates a pipeline that:

1. Collects recent biomedical literature.
2. Organizes publications across multiple years.
3. Analyzes research topics and journals.
4. Retrieves official disease-related gene information.
5. Detects gene mentions within scientific literature.
6. Generates evidence-based gene rankings.
7. Highlights potentially underrepresented genes in the analyzed literature.
8. Presents the results through an interactive dashboard.

---

## ✨ Key Features

### 📚 Automated PubMed Literature Collection

Project GENESIS retrieves biomedical publications using the NCBI Entrez API.

The collection pipeline uses year-based sampling across a five-year research window instead of simply retrieving the newest papers. This provides broader temporal coverage for publication analysis.

---

### 📈 Research Trend Analysis

The platform automatically analyzes:

- Publications by year
- Leading journals
- Frequently occurring research terms
- Dataset coverage
- Missing abstracts

This helps provide a high-level view of the research landscape for each disease.

---

### 🧬 NCBI Gene Integration

Project GENESIS retrieves official human gene records associated with the selected disease from NCBI Gene.

Gene information includes:

- Gene symbol
- NCBI Gene ID
- Gene name
- Chromosome
- Map location
- NCBI summary

---

### 🔎 Literature Gene Detection

The system compares official disease-associated gene symbols against titles and abstracts in the collected PubMed literature.

For every detected gene, GENESIS records the papers in which the gene appears and calculates its literature coverage within the analyzed sample.

---

### 📊 Gene Evidence Ranking

GENESIS combines official NCBI gene records with observed literature mentions to generate an exploratory evidence score.

This allows users to compare which official genes are more frequently represented in the current research sample.

These scores are intended for **research exploration only** and are not measures of biological importance or clinical significance.

---

### 🔬 Potential Research Gap Analysis

Genes with official disease associations but relatively low representation in the analyzed literature are surfaced as potential research gaps.

This feature is designed to identify areas that may deserve further investigation rather than claim scientific novelty.

---

### 🧠 Automated Research Summary

The dashboard automatically generates a concise summary of:

- Literature coverage
- Research topics
- Gene evidence
- Potential research gaps

The current summary system is rule-based and does not use a generative AI model.

---

### 📄 Interactive Paper Explorer

Users can:

- Search publication titles
- Search abstracts
- Filter the collected research
- Inspect publication metadata
- Read abstracts
- Download the analyzed paper dataset as CSV

---

## 🖥️ Dashboard

The Streamlit dashboard provides a single interface for exploring the complete research pipeline.

### Current Dashboard Sections

- Disease selector
- Research overview
- Automated research summary
- Publication trends
- Leading journals
- Research topics
- Literature gene mentions
- Gene evidence ranking
- Potential research gaps
- Official NCBI genes
- Gene detail explorer
- Research paper explorer
- CSV export

---

## 🦠 Currently Supported Diseases

| Disease | Literature Analysis | NCBI Genes | Gene Ranking | Research Gaps |
|---|---|---|---|---|
| Alzheimer Disease | ✅ | ✅ | ✅ | ✅ |
| Parkinson Disease | ✅ | ✅ | ✅ | ✅ |

The architecture is designed so additional diseases can be incorporated into future versions.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and data pipeline |
| pandas | Data cleaning, processing, and analysis |
| Biopython | NCBI Entrez API integration |
| PubMed | Biomedical research literature |
| NCBI Gene | Official gene information |
| Streamlit | Interactive web dashboard |
| Plotly | Interactive data visualization |
| Git | Version control |
| GitHub | Source-code hosting |

---

## 🏗️ System Architecture

```text
                ┌──────────────────────┐
                │   Disease Selection  │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │     PubMed / NCBI    │
                │      Entrez API      │
                └──────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ PubMed Literature│      │    NCBI Gene     │
    │    Collection    │      │    Collection    │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         │
    ┌──────────────────┐               │
    │ Research Analysis│               │
    │ Topics / Journals│               │
    │ Publication Years│               │
    └────────┬─────────┘               │
             │                         │
             └────────────┬────────────┘
                          ▼
                ┌──────────────────┐
                │ Gene Extraction  │
                │ & Literature     │
                │ Matching         │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Gene Evidence    │
                │     Scoring      │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Research Gap     │
                │    Analysis      │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │    Streamlit     │
                │    Dashboard     │
                └──────────────────┘
```

---

## 📁 Project Structure

```text
project-genesis/
│
├── app/
│   └── dashboard.py
│
├── data/
│   ├── raw/
│   │   ├── alzheimer_recent_articles.csv
│   │   └── parkinson_recent_articles.csv
│   │
│   └── processed/
│       ├── alzheimer/
│       │   ├── gene_mentions.csv
│       │   ├── gene_scores.csv
│       │   ├── gene_summary.csv
│       │   ├── ncbi_gene_results.csv
│       │   ├── publication_trends.csv
│       │   ├── research_gaps.csv
│       │   ├── top_journals.csv
│       │   └── top_keywords.csv
│       │
│       └── parkinson/
│           ├── gene_mentions.csv
│           ├── gene_scores.csv
│           ├── gene_summary.csv
│           ├── ncbi_gene_results.csv
│           ├── publication_trends.csv
│           ├── research_gaps.csv
│           ├── top_journals.csv
│           └── top_keywords.csv
│
├── src/
│   ├── ai/
│   │   └── research_summary.py
│   │
│   ├── analysis/
│   │   ├── disease_profile.py
│   │   ├── gene_extractor.py
│   │   ├── gene_scoring.py
│   │   ├── research_explorer.py
│   │   └── research_gap.py
│   │
│   ├── collectors/
│   │   ├── ncbi_gene_collector.py
│   │   └── pubmed_collector.py
│   │
│   ├── config.py
│   └── main.py
│
├── .streamlit/
│   └── config.toml
│
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Thxrunn/project-genesis.git
cd project-genesis
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

#### Windows

```bash
.venv\Scripts\activate
```

#### macOS/Linux

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Dashboard

Start the Streamlit application with:

```bash
streamlit run app/dashboard.py
```

Streamlit will provide a local URL, typically:

```text
http://localhost:8501
```

---

## 🔄 Running the Research Pipeline

To regenerate the research datasets:

```bash
python -m src.main
```

The pipeline prompts for:

- Disease
- Number of years to analyze
- Maximum number of publications

It then runs the collection and analysis workflow automatically.

---

## 📊 Current v1.0 Dataset

Project GENESIS v1.0 contains research samples for:

**Alzheimer Disease**
- Research window: 2022–2026
- PubMed literature
- Official NCBI gene records
- Literature gene detection
- Evidence ranking
- Research-gap analysis

**Parkinson Disease**
- Research window: 2022–2026
- PubMed literature
- Official NCBI gene records
- Literature gene detection
- Evidence ranking
- Research-gap analysis

The included datasets represent research samples collected for exploration and demonstration rather than exhaustive systematic reviews of the biomedical literature.

---

## ⚠️ Important Limitations

Project GENESIS is an exploratory research and software-engineering project.

The platform:

- Does not provide medical advice.
- Does not diagnose disease.
- Does not establish gene-disease causality.
- Does not prove scientific novelty.
- Does not replace systematic literature reviews.
- Does not measure the biological importance of a gene.
- Does not provide clinical recommendations.

Research-gap results indicate **underrepresentation within the analyzed literature sample only**.

Gene evidence scores are heuristic research-exploration metrics rather than validated biomedical scores.

---

## 🔮 Future Improvements

Potential future versions could include:

- Additional neurological diseases
- Larger literature datasets
- Semantic search across paper abstracts
- NLP-based research-theme clustering
- Biomedical text embeddings
- Citation-network analysis
- Gene interaction networks
- ML-based literature classification
- Automated scheduled literature updates
- More advanced research comparison tools

These improvements are intentionally outside the scope of v1.0.

---

## 💡 What I Learned

Building Project GENESIS gave me hands-on experience with:

- Designing an end-to-end data pipeline
- Working with external scientific APIs
- Processing real-world biomedical data
- Building reusable Python modules
- Designing rule-based evidence-scoring systems
- Handling incomplete and inconsistent scientific metadata
- Building interactive Plotly visualizations
- Developing Streamlit applications
- Structuring a multi-module Python project
- Debugging data pipelines across multiple data sources
- Using Git and GitHub for version control

One of the biggest challenges was ensuring that publication-year analysis remained meaningful when PubMed records contained different date representations. I redesigned the collection process to sample publications by year and preserve the year used during retrieval for consistent longitudinal analysis.

---

## 📜 Data Sources

Project GENESIS uses publicly available biomedical information from:

- **PubMed / NCBI Entrez**
- **NCBI Gene**

The included data should be interpreted according to the terms and guidance of the original data providers.

---

## 👨‍💻 Author

**Tharun Kumar Malla Dinakaran**

Computer Science  
California State University San Marcos

---

## 📄 License

This project is available under the license included in the repository.

---

### 🧬 Project GENESIS

**Turning biomedical literature into structured research intelligence.**
