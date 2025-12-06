# MIS 547 – Group 4 Retail RAG Chatbot Project (Mid-Semester Update)

## Team Members

- Esai Flores
- Kyle deGuzman
- Kyler Nats
- Pragnya Narasimha
- Sharanya Neelam

---

## Getting Started

### Prerequisites

**Option 1: Using uv (Recommended)**
- [uv](https://github.com/astral-sh/uv) package manager
- Python 3.10+ will be automatically installed by uv if not present

**Option 2: Using pip**
- Python 3.10 or higher must be manually installed
- pip (usually comes with Python)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Praagnya/shopRAG.git
cd shopRAG
```

2. Install dependencies:

**Using uv (Recommended - No Python install required):**
```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# Or: pip install uv

# uv will automatically download Python 3.10 if needed and set up everything
uv sync
```

**Using pip (Requires Python 3.10+ already installed):**
```bash
# Create a virtual environment
python3.10 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

3. Verify installation:
```bash
python --version  # Should show Python 3.10.x
```

---

## Project Overview

Retail companies face increasing challenges in meeting customer expectations for fast, accurate, and personalized assistance. Traditional support systems (email, call centers, and manual review analysis) struggle to scale with e-commerce growth, resulting in delayed responses and higher costs.

This project proposes an AI-powered **Retail Chatbot using Retrieval-Augmented Generation (RAG)** to:

- Answer customer product questions in real time.
- Summarize customer reviews.
- Identify product trends and common issues.
- Provide reliable responses grounded directly in verified customer feedback.

The chatbot uses **Large Language Models (LLMs)** combined with **retrieval from a Vector Database** to ensure responses remain factual, up-to-date, and cost-efficient.

---

## Dataset

The project uses the **Amazon Reviews 2023 dataset (McAuley Lab)**, which contains millions of reviews across **33 product categories** from **1996–2023**.

Each entry includes:

- Customer-written reviews and ratings.
- Helpful vote counts.
- Product metadata such as title, category, price, features, and vendor.
- Product relationships and bundled purchase data.

This dataset enables:

- Semantic search over customer feedback.
- Trend analysis over time.
- Reliable question-answering grounded in real data.

---

## Data Schema

### 1. User Reviews

Each review record includes:

| Field                  | Description                                   |
| ---------------------- | --------------------------------------------- |
| `rating`               | Numeric satisfaction score (1.0 – 5.0)        |
| `title`                | Review headline                               |
| `text`                 | Full review body                              |
| `images`               | Optional uploaded images                      |
| `user_id`              | Anonymized reviewer ID                        |
| `verified_purchase`    | Whether the product was purchased by reviewer |
| `asin` / `parent_asin` | Product and product-group identifiers         |
| `timestamp`            | Unix posting time                             |
| `helpful_vote`         | Number of users marking the review helpful    |

---

### 2. Item Metadata

Product catalog records include:

| Field               | Description                                               |
| ------------------- | --------------------------------------------------------- |
| `title`             | Product name                                              |
| `main_category`     | Top-level category                                        |
| `price`             | Listed price                                              |
| `store`             | Brand/vendor                                              |
| `features`          | Key bullet-point specs                                    |
| `description`       | Long description text                                     |
| `details`           | Structured attributes (material, brand, dimensions, etc.) |
| `images` / `videos` | Product media                                             |
| `bought_together`   | Cross-sell relationships                                  |
| `average_rating`    | Mean rating from all reviews                              |
| `rating_number`     | Count of contributing reviews                             |
| `categories`        | Hierarchical sub-categories                               |
| `parent_asin`       | Parent product group ID                                   |

---

## Database Design

The project uses a **Vector Database (ChromaDB)** as the primary backend to enable **semantic search** across reviews and product descriptions.

### Why ChromaDB?

- Fast similarity search using dense embeddings.
- Easy ingestion and maintenance.
- Direct integration with Python pipelines.
- Supports **RAG workflows** without large infrastructure overhead.

Future extension:

- **PostgreSQL** for structured analytics and dashboard queries (aggregations, filters).

---

## Data Preprocessing Pipeline

Steps:

1. **Text Cleaning** – Remove HTML, URLs, symbols while preserving meaning.
2. **Deduplication** – Remove highly similar reviews.
3. **Missing Values** – Fill defaults or remove incomplete entries.
4. **Quality Filtering** – Remove overly short or excessively long reviews.
5. **Feature Engineering** – Create a `combined_text` field from title + body + rating.
6. **Standardization** – Normalize timestamps, numerics, strings, and booleans.

---

## RAG System Architecture

We use **Retrieval-Augmented Generation (RAG)** to avoid costly full-model fine-tuning and to ensure factual accuracy.

### Advantages of RAG

- ✅ **Lower cost & rapid updates** — Only the vector database must be refreshed as new reviews arrive.
- ✅ **Reduced hallucinations** — The model answers using retrieved real reviews.
- ✅ **Smaller model footprint** — No massive GPU training required.
- ✅ **Trusted results** — Every response is grounded in customer feedback.

---

## RAG Components

### 1. Embedding Model (Retrieval)

Converts questions and reviews into vectors for semantic search.

Options:

- `BAAI/bge-small-en-v1.5`
- `sentence-transformers/all-MiniLM-L6-v2`

Design goals:

- Fast embedding generation.
- Low compute consumption.
- High semantic similarity quality.

---

### 2. Language Model (Generation)

Summarizes retrieved review segments into natural language responses.

Candidate models:

- **Mistral 7B**
- **Llama 3 8B**

Deployment:

- Hosted on **DigitalOcean Droplets**.
- Optional style tuning using **LoRA** for conversational tone only (no full retraining).

---

## MLOps Roadmap & Next Steps

Target Internal Completion: **December 5, 2025**  
Final Review & Presentation Window: **December 6–8, 2025**  
Final Presentation: **December 9, 2025**

Planned activities:

- Containerized pipeline setup.
- GPU/CPU inference monitoring.
- Database ingestion scheduling (batch processing per month).
- Performance benchmarking.
- Cost optimization and logging.

---

## Guidance Requested from Instruction Team

We seek insights on:

1. Scaling containerized ML services between **DigitalOcean and AWS** (although final hosting remains on DigitalOcean).
2. Monitoring **GPU utilization and inference workloads**.
3. Best practices for testing vs training workflows in **RAG-based systems**.

---

## Risks & Mitigation

| Risk                | Description                       | Mitigation                                               |
| ------------------- | --------------------------------- | -------------------------------------------------------- |
| Compute constraints | Limited GPU for inference testing | Use CPU-optimized embedders and AWS/DigitalOcean credits |
| Latency             | High retrieval/API delay          | Implement vector caching and pre-indexed embeddings      |
| Data imbalance      | Category overrepresentation       | Stratified sampling during embedding generation          |
| Security threats    | API misuse or injection           | Enforce HTTPS, rotate API keys, run validation tests     |

---

## Task Assignments

### Data & Pipeline

- Preprocessing & code setup – **Pragnya & Kyle**
- Google Colab notebook setup
- Dataset conversion to vector DB

### RAG Development

- LLM API connection – **Esai**
- Guardrails implementation – **Esai**
- Querying vector DB – **Esai**
- Reranking vs similarity performance research – **Esai**

### Infrastructure

- Cloud research & security planning – **Sharanya & Kyler**
- Droplet setup and documentation
- VPC & firewall configuration

---

## References

- Stanford Teaching Commons – _Defining AI and Chatbots_
- Lewis et al., 2020 – _Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks_
- DigitalOcean – _ML Deployment Documentation_
- Cloudian – _Data Backup Best Practices_

---

## License

Academic project developed as part of **MIS 547 – University of Arizona** coursework.
