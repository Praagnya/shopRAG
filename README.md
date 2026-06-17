# shopRAG: Product Review Chatbot

---

## Project Overview

ShopRAG is an AI-powered chatbot that helps customers make informed purchasing decisions by answering questions about products based on real customer reviews. Using Retrieval-Augmented Generation (RAG), the system provides accurate, grounded responses without hallucinating information.

### Key Features

- **Real-time Q&A** - Answer product questions instantly using customer reviews
- **Semantic Search** - Find relevant reviews using vector embeddings
- **Guardrails** - Input validation, PII removal, and hallucination detection
- **Scalable** - PostgreSQL + pgvector for production-grade vector search
- **Interactive UI** - Gradio-based chat interface with product filtering
- **Containerized** - Full Docker setup with monitoring (Prometheus + Grafana)
- **Production-Ready** - FastAPI backend with health checks and metrics

---

## Live Demo

**Deployed on Digital Ocean**

- **UI**: Gradio Share Link (generated on startup)
- **Database**: 30,000 products with 191,849 reviews
- **Category**: Cell Phones & Accessories (Amazon Reviews 2023)

---

## Architecture

### Docker Containerized Setup

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Network: shoprag                     │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐            │
│  │ Gradio   │───>│ FastAPI  │───>│ Digital   │ (external) │
│  │ Frontend │    │ Backend  │    │ Ocean PG  │            │
│  │  :7860   │    │  :8000   │    │           │            │
│  └──────────┘    └────┬─────┘    └───────────┘            │
│                       │ /metrics                            │
│                  ┌────▼──────┐                              │
│                  │Prometheus │                              │
│                  │  :9090    │                              │
│                  └────┬──────┘                              │
│                  ┌────▼──────┐                              │
│                  │ Grafana   │                              │
│                  │  :3000    │                              │
│                  └───────────┘                              │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │ Data Ingestion       │ (on-demand)                       │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### System Components

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   Gradio UI (Port 7860)         │
│   - Chat interface              │
│   - Product selection           │
│   - Review count slider         │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   RAG Pipeline                  │
│   ┌───────────────────────┐    │
│   │ Input Guardrails      │    │
│   │ - Length validation   │    │
│   │ - Prompt injection    │    │
│   │ - Rate limiting       │    │
│   └───────────┬───────────┘    │
│               ▼                 │
│   ┌───────────────────────┐    │
│   │ Embedder              │    │
│   │ BAAI/bge-small-en-v1.5│    │
│   │ 384-dim vectors       │    │
│   └───────────┬───────────┘    │
│               ▼                 │
│   ┌───────────────────────┐    │
│   │ Retriever (pgvector)  │    │
│   │ - Cosine similarity   │    │
│   │ - Quality filters     │    │
│   │ - Top-k results       │    │
│   └───────────┬───────────┘    │
│               ▼                 │
│   ┌───────────────────────┐    │
│   │ LLM Client            │    │
│   │ - PII removal         │    │
│   │ - Response generation │    │
│   │ - Hallucination check │    │
│   └───────────────────────┘    │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   PostgreSQL + pgvector         │
│   (Digital Ocean Managed DB)    │
│   - products table (30k)        │
│   - reviews table (191k+)       │
│   - Vector similarity index     │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   OpenAI API                    │
│   Model: gpt-4o-mini            │
│   - Natural language generation │
└─────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **Python 3.10** - Core application
- **PostgreSQL + pgvector** - Vector database for semantic search
- **psycopg2** - Database adapter
- **sentence-transformers** - Embedding generation
- **OpenAI API** - LLM for response generation

### Frontend
- **Gradio** - Interactive web UI
- **Markdown** - Response formatting

### Infrastructure
- **Docker & Docker Compose** - Containerized deployment
- **Digital Ocean Droplet** - Application hosting
- **Digital Ocean Managed PostgreSQL** - Database hosting
- **Prometheus & Grafana** - Monitoring and metrics
- **uv** - Fast Python package manager

### MLOps
- **Git/GitHub** - Version control
- **Datasets (HuggingFace)** - Data loading
- **dotenv** - Environment management

---

## Dataset

**Amazon Reviews 2023** (McAuley Lab)

- **Subset**: Cell Phones and Accessories
- **Products**: 30,000 (most recent products)
- **Reviews**: 191,849 with embeddings
- **Timespan**: 1996–2023
- **Source**: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023

### Data Schema

**Products Table:**
```sql
- asin (TEXT PRIMARY KEY)
- title (TEXT)
- main_category (VARCHAR(255))
- average_rating (REAL)
- rating_number (INTEGER)
- price (TEXT)
- features (TEXT)  -- JSON array
- description (TEXT)
- store (VARCHAR(255))
```

**Reviews Table:**
```sql
- id (SERIAL PRIMARY KEY)
- asin (TEXT)  -- Foreign key to products
- product_name (TEXT)
- category (TEXT)
- review_rating (REAL)
- verified_purchase (BOOLEAN)
- helpful_vote (INTEGER)
- timestamp (BIGINT)
- review_text (TEXT)
- embedding (VECTOR(384))  -- pgvector
```

---

## Data Pipeline

### 1. Ingestion
```bash
uv run python backend/scripts/ingest_reviews_postgres.py
```

**Process:**
1. Load product metadata from HuggingFace
2. Filter to last 30k products (most recent)
3. Load reviews for those products
4. Filter low-quality reviews (length < 10 chars)
5. Combine review with product context
6. Generate embeddings (batch size: 512)
7. Store in PostgreSQL with pgvector

**Performance:**
- Products/hour: ~15,000
- Reviews/hour: ~80,000
- Embedding batch: 512 reviews at once

### 2. Preprocessing

**Quality Filters:**
- Minimum review length: 30 characters
- Valid ratings only (rating > 0)
- Remove duplicate reviews

**Text Processing:**
```python
combined_text = f"""
Product: {product_name}
Category: {category}
Rating: {rating}/5

Review: {review_text}
"""
```

**PII Removal:**
- Emails → `[EMAIL]`
- Phone numbers → `[PHONE]`
- URLs → `[URL]`
- Credit cards → `[CARD]`
- SSNs → `[SSN]`

---

## RAG System

### Retrieval-Augmented Generation (RAG)

**Why RAG?**
- Grounded in real customer reviews
- No model fine-tuning required
- Easy to update with new data
- Reduced hallucinations
- Cost-effective (no GPU training)

### Query Flow

1. **Input Validation**
   - Check query length (3-500 chars)
   - Detect prompt injection attempts
   - Rate limit: 20 requests/minute

2. **Embedding**
   - Convert query to 384-dim vector
   - Model: `BAAI/bge-small-en-v1.5`

3. **Retrieval**
   - Search PostgreSQL using cosine similarity
   - Apply quality filters
   - Return top-k reviews (default: 5)

4. **Generation**
   - Build context from product + reviews
   - Remove PII from review text
   - Generate response using OpenAI GPT-4o-mini
   - Check for hallucinations (word overlap)

5. **Response**
   - Return concise answer (2-3 sentences)
   - Show number of reviews used
   - Display product information

---

## Guardrails

### 1. Input Guardrails
```python
- Length: 3-500 characters
- Prompt injection detection
- Rate limiting (20/min per user)
```

### 2. Retrieval Quality
```sql
WHERE LENGTH(review_text) >= 30
ORDER BY embedding <=> query_vector
LIMIT 5
```

### 3. PII Removal
All review text is sanitized before sending to LLM.

### 4. Hallucination Detection
```python
# Lightweight word overlap check
overlap_ratio = len(response_words ∩ review_words) / len(response_words)

if overlap_ratio < 0.3:
    log("[HALLUCINATION WARNING]")
```

### 5. System Prompt Engineering
```
CRITICAL RULES:
1. ONLY use information directly stated in the provided context
2. DO NOT make assumptions or add information not in the reviews
3. Keep responses short (2-3 sentences maximum)
```

---

## Installation

**Recommended**: Use [Docker deployment](#docker-deployment-recommended) for the quickest setup with monitoring included.

For local development without Docker, follow the steps below.

### Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- OpenAI API key
- uv package manager (recommended)

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/Praagnya/shopRAG.git
cd shopRAG

# 2. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Create .env file
cp .env.example .env
nano .env  # Add your API keys

# 5. Run data ingestion (optional - data already in DB)
uv run python backend/scripts/ingest_reviews_postgres.py

# 6. Start the UI
uv run python frontend/gradio_app.py
```

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:pass@host:port/dbname
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

---

## Usage

### Start the Application

```bash
cd shopRAG
uv run python frontend/gradio_app.py
```

Access at: `http://localhost:7860` or the Gradio share link.

### Example Queries

**Product-Specific (with ASIN):**
```
ASIN: B07SKQZSN6
Query: "Is it durable?"
```

**Global Search (no ASIN):**
```
ASIN: [blank]
Query: "What are the best iPhone cases under $20?"
```

### API Usage (Optional)

If FastAPI layer is added:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How is the battery life?",
    "product_asin": "B07SKQZSN6",
    "top_k": 5
  }'
```

---

## Project Structure

```
shopRAG/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   └── routes/
│   │       └── rag.py           # RAG endpoints
│   ├── config/
│   │   └── settings.py          # Configuration
│   ├── scripts/
│   │   └── ingest_reviews_postgres.py  # Data ingestion
│   ├── services/
│   │   ├── embedder.py          # Embedding generation
│   │   ├── retriever_postgres.py # Vector search
│   │   ├── llm_client.py        # OpenAI integration
│   │   ├── rag_pipeline.py      # RAG orchestration
│   │   └── guardrails.py        # Input validation
│   └── utils/
│       └── text_processor.py    # Text utilities
├── frontend/
│   └── gradio_app.py            # Gradio UI
├── data/
│   └── product_cache.json       # Product metadata
├── monitoring/
│   ├── prometheus.yml           # Prometheus config
│   └── grafana/
│       ├── provisioning/        # Grafana datasources
│       └── dashboards/          # Pre-built dashboards
├── scripts/
│   └── docker-dev.sh            # Docker helper script
├── Dockerfile.backend           # Backend container
├── Dockerfile.frontend          # Frontend container
├── Dockerfile.ingest            # Ingestion container
├── docker-compose.yml           # Service orchestration
├── docker-compose.override.yml  # Development overrides
├── Makefile                     # Quick commands
├── .dockerignore                # Docker build exclusions
├── .env.docker                  # Environment template
├── .env                         # Environment variables
├── pyproject.toml               # Dependencies
├── uv.lock                      # Lock file
├── README.md                    # This file
└── DOCKER_README.md             # Docker setup guide
```

---

## Deployment

### Digital Ocean Droplet

**Current Setup:**
- **Droplet**: 4 GB RAM, 2 vCPUs
- **Database**: Managed PostgreSQL with pgvector
- **Access**: SSH + Gradio share link

**Deploy Steps:**
```bash
# 1. SSH to droplet
ssh root@<droplet-ip>

# 2. Clone and setup
cd /root
git clone https://github.com/Praagnya/shopRAG.git
cd shopRAG

# 3. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 4. Configure environment
cp .env.example .env
nano .env  # Add DATABASE_URL and OPENAI_API_KEY

# 5. Run application
uv run python frontend/gradio_app.py
```

### Docker Deployment (Recommended)

**Full containerized setup with monitoring stack**

#### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)
- Digital Ocean PostgreSQL database
- OpenAI API key
- At least 8GB RAM allocated to Docker

#### Quick Start

```bash
# 1. Configure environment
cp .env.docker .env
nano .env  # Add OPENAI_API_KEY and DATABASE_URL

# 2. Build and start all services
make build
make up

# 3. Access applications
# - Frontend (Gradio UI): http://localhost:7860
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)

# 4. Run data ingestion (optional)
make ingest
```

#### Docker Services

The Docker Compose setup includes:
- **Backend** (FastAPI) - Port 8000
- **Frontend** (Gradio) - Port 7860
- **Prometheus** - Metrics collection on port 9090
- **Grafana** - Dashboards on port 3000
- **Ingest** - On-demand data ingestion job

#### Common Commands

```bash
make build       # Build all Docker images
make up          # Start all services
make down        # Stop all services
make logs        # View all logs
make health      # Check service health
make restart     # Restart all services
make clean       # Remove containers and volumes
```

#### Alternative: Using Docker Compose Directly

```bash
# Build and start
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Run data ingestion
docker-compose --profile ingest run --rm ingest
```

For detailed Docker setup instructions, see [DOCKER_README.md](DOCKER_README.md).

---

## Performance Metrics

### Current Stats
- **Total Products**: 30,000
- **Total Reviews**: 191,849
- **Embedding Dimension**: 384
- **Average Query Time**: ~2-3 seconds
- **Database Size**: ~500 MB

### Query Performance
```
Embedding: ~50ms
Retrieval: ~100-200ms
LLM Generation: ~1-2s
Total: ~2-3s per query
```

---

## Monitoring

### Prometheus Metrics (Docker Setup)

Access Prometheus at http://localhost:9090

Available metrics:
- `rag_queries_total` - Total RAG queries
- `rag_llm_calls_total` - Total LLM API calls
- `rag_pipeline_latency_ms` - RAG pipeline latency
- `rag_embedding_latency_ms` - Embedding latency
- `rag_retrieval_latency_ms` - Retrieval latency
- `rag_llm_latency_ms` - LLM latency
- `rag_errors_total` - Total errors
- `rag_guardrail_failures_total` - Guardrail rejections
- `rag_active_requests` - Active requests
- `llm_tokens_used_total` - Token usage

### Grafana Dashboards (Docker Setup)

1. Access Grafana at http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to "shopRAG Overview Dashboard"

Dashboard shows:
- Request rate and latency trends
- LLM call rate and error rate
- Active requests and products loaded
- Component-level latency breakdown
- Token usage tracking

### Application Logs

**Docker Deployment:**
```bash
# View all logs
make logs

# Backend logs only
make logs-backend

# Frontend logs only
make logs-frontend

# Follow logs in real-time
docker-compose logs -f
```

**Local Deployment:**
```bash
# Application logs
tail -f /var/log/gradio.log

# Ingestion logs
tail -f /var/log/shoprag_ingest.log

# System logs
grep CRON /var/log/syslog
```

### Database Stats
```sql
-- Review count
SELECT COUNT(*) FROM reviews;

-- Products with reviews
SELECT COUNT(DISTINCT asin) FROM reviews;

-- Average reviews per product
SELECT AVG(review_count) FROM (
    SELECT COUNT(*) as review_count
    FROM reviews
    GROUP BY asin
) subq;
```

---

## Automation

### Cron Jobs (Weekly Updates)

```bash
# Add to crontab
crontab -e

# Run ingestion every Sunday at 2 AM
0 2 * * 0 /root/shopRAG/scripts/auto_ingest.sh
```

### Ingestion Script
```bash
#!/bin/bash
cd /root/shopRAG
git pull
uv run python backend/scripts/ingest_reviews_postgres.py
pkill -f gradio_app.py
nohup uv run python frontend/gradio_app.py > /var/log/gradio.log 2>&1 &
```

---

## Testing

### Run Tests
```bash
# Unit tests
uv run pytest tests/

# Integration tests
uv run pytest tests/integration/

# Test specific component
uv run pytest tests/test_retriever.py
```

### Manual Testing
```python
# Test RAG pipeline
from backend.services.rag_pipeline import get_rag_pipeline

rag = get_rag_pipeline()
result = rag.query("Is it durable?", product_asin="B07SKQZSN6")
print(result['response'])
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Timeout**
```bash
# Add droplet IP to PostgreSQL trusted sources
# Digital Ocean → Databases → Settings → Trusted Sources
```

**2. Empty Responses**
```bash
# Check OpenAI model name
cat backend/config/settings.py | grep OPENAI_MODEL
# Should be: gpt-4o-mini (not gpt-5-mini)
```

**3. No Reviews Retrieved**
```bash
# Check if reviews exist for ASIN
uv run python -c "
import psycopg2, os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM reviews WHERE asin=%s', ('B07SKQZSN6',))
print(f'Reviews: {cur.fetchone()[0]}')
"
```

**4. Port Already in Use**
```bash
# Kill existing Gradio process
lsof -ti:7860 | xargs kill -9
```

---

## Future Enhancements

### Completed ✓
- [x] Docker containerization with monitoring
- [x] Prometheus metrics collection
- [x] Grafana dashboards
- [x] FastAPI backend with health checks
- [x] Production-ready deployment setup

### Planned Features
- [ ] Conversation history/memory
- [ ] Multi-turn dialogue support
- [ ] User authentication
- [ ] Product recommendations
- [ ] Sentiment analysis dashboard
- [ ] A/B testing for prompts
- [ ] Elasticsearch for hybrid search
- [ ] Real-time review streaming

### Scaling
- [ ] Horizontal scaling with load balancer
- [ ] Redis caching for frequent queries
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline with automated testing
- [ ] Auto-scaling based on metrics

---

## Contributing

This is an academic project. For questions or collaboration:

1. Create an issue on GitHub
2. Submit a pull request
3. Contact team members

---

## References

- **Dataset**: McAuley-Lab. (2023). *Amazon Reviews 2023*. HuggingFace.
- **RAG**: Lewis et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. arXiv.
- **pgvector**: Ankane. *pgvector: Open-source vector similarity search for Postgres*.
- **Embeddings**: BAAI. *BGE: BAAI General Embedding*.

---

## License

Academic project developed as part of **MIS 547 – University of Arizona** coursework.

---

## Contact

**Team Members:**
- Esai Flores
- Kyle deGuzman
- Kyler Nats
- Pragnya Narasimha
- Sharanya Neelam

**Course**: MIS 547 – Cloud Computing
**Institution**: University of Arizona
**Semester**: Fall 2024

---

**Last Updated**: December 2025
