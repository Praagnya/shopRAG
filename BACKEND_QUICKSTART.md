# Backend Quick Start Guide

## Your Complete RAG Backend is Ready!

All code has been written. Follow these steps to get it running.

---

## Step 1: Install New Dependencies

```bash
cd /Users/praagnya/Desktop/MSDS/Fall\ 25/Cloud_computing/shopRAG
uv sync
```

This will install the new packages:
- fastapi
- uvicorn
- pydantic
- openai

---

## Step 2: Set OpenAI API Key

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
# or
code .env
```

Then add:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Load it in your shell:
```bash
export OPENAI_API_KEY='sk-your-actual-api-key-here'
```

---

## Step 3: Run Data Ingestion

This will:
1. Load product metadata (Cell Phones & Accessories)
2. Load reviews
3. Generate embeddings
4. Store in ChromaDB

```bash
python backend/scripts/ingest_reviews.py
```

Expected time: 10-15 minutes for 10,000 reviews

Output location:
- ChromaDB: `data/chroma_db/`
- Product cache: `data/product_cache.json`

---

## Step 4: Test the RAG Pipeline

Before starting the API, test that everything works:

```bash
python test_rag.py
```

This will:
- Initialize the RAG pipeline
- Run 3 test queries
- Show responses

If this works, you're ready for the API!

---

## Step 5: Start the API Server

```bash
python backend/api/main.py
```

Or with auto-reload:
```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000

---

## Test the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Status
```bash
curl http://localhost:8000/api/status
```

### Query
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What do customers say about battery life?", "top_k": 5}'
```

### Interactive API Docs
Open in browser: http://localhost:8000/docs

---

## Project Structure

```
backend/
├── api/
│   └── main.py              # FastAPI application
├── config/
│   └── settings.py          # Configuration
├── models/
│   └── schemas.py           # Pydantic models
├── scripts/
│   ├── eda_cellphones.py    # EDA script
│   └── ingest_reviews.py    # Data ingestion
├── services/
│   ├── embedder.py          # Embedding service
│   ├── retriever.py         # Vector DB retriever
│   ├── llm_client.py        # OpenAI client
│   └── rag_pipeline.py      # RAG orchestrator
└── utils/
    └── text_processor.py    # Text utilities
```

---

## API Endpoints

### GET /
- Root endpoint with API info

### GET /health
- Health check

### GET /api/status
- System status (num products, embeddings, etc.)

### POST /api/query
- Query the RAG system

Request:
```json
{
  "query": "What do customers say about the camera?",
  "top_k": 5
}
```

Response:
```json
{
  "query": "What do customers say about the camera?",
  "response": "Customers generally love the camera quality...",
  "product_info": {
    "title": "Samsung Galaxy S23",
    "category": "Cell Phones & Accessories",
    "average_rating": 4.3,
    "rating_number": 1234,
    "price": "$799",
    "features": ["50MP camera", "..."],
    "description": "..."
  },
  "num_documents_used": 5,
  "retrieved_documents": [...]
}
```

---

## Troubleshooting

### Import errors
Make sure you're in the project root and venv is activated:
```bash
cd /Users/praagnya/Desktop/MSDS/Fall\ 25/Cloud_computing/shopRAG
source .venv/bin/activate
```

### OpenAI API errors
Check your API key is set:
```bash
echo $OPENAI_API_KEY
```

### ChromaDB not found
Run ingestion first:
```bash
python backend/scripts/ingest_reviews.py
```

### Port already in use
Kill the process or use a different port:
```bash
uvicorn backend.api.main:app --reload --port 8001
```

---

## Next Steps

1. Build a frontend (React, Streamlit, or simple HTML)
2. Add more product categories
3. Implement caching for faster responses
4. Add authentication
5. Deploy to DigitalOcean

---

## Happy Coding! 🚀
