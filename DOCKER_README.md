# shopRAG Docker Setup Guide

This guide explains how to run the shopRAG application using Docker containers.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Digital Ocean PostgreSQL database (already provisioned)
- OpenAI API key
- At least 8GB RAM allocated to Docker
- ~20GB disk space for images and data

## Quick Start

### 1. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.docker .env
```

Edit `.env` and set:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: Your Digital Ocean PostgreSQL connection string

### 2. Build and Start Services

Using Make (recommended):
```bash
make build  # Build all images
make up     # Start all services
```

Or using Docker Compose directly:
```bash
docker-compose build
docker-compose up -d
```

### 3. Access Applications

- **Frontend (Gradio UI)**: http://localhost:7860
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (username: `admin`, password: `admin`)

## Data Ingestion

Run data ingestion to populate the PostgreSQL database:

```bash
make ingest
```

Or:
```bash
docker-compose --profile ingest run --rm ingest
```

This will:
1. Download Amazon product metadata (~10-20GB)
2. Generate embeddings using sentence-transformers
3. Store vectors in PostgreSQL with pgvector
4. Save product cache to `data/product_cache.json`

## Service Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Gradio    │────▶│   FastAPI   │────▶│   Digital    │
│  Frontend   │     │   Backend   │     │  Ocean PG    │
│   :7860     │     │    :8000    │     │  (external)  │
└─────────────┘     └──────┬──────┘     └──────────────┘
                           │
                           │ /metrics
                           │
                    ┌──────▼──────┐
                    │ Prometheus  │
                    │    :9090    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Grafana   │
                    │    :3000    │
                    └─────────────┘
```

## Development Workflow

### Hot Reload (Development Mode)

The `docker-compose.override.yml` file enables hot-reloading:
- Backend: Changes to Python files automatically restart the server
- Frontend: Gradio watches for file changes

### View Logs

```bash
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
```

Or:
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

```bash
make restart
```

Or:
```bash
docker-compose restart
```

### Access Container Shell

```bash
make shell-backend     # Backend container
make shell-frontend    # Frontend container
```

### Health Checks

```bash
make health
```

Or manually:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/status
```

## Monitoring

### Prometheus Metrics

Access Prometheus at http://localhost:9090

Available metrics:
- `rag_queries_total`: Total RAG queries
- `rag_llm_calls_total`: Total LLM API calls
- `rag_pipeline_latency_ms`: RAG pipeline latency
- `rag_embedding_latency_ms`: Embedding latency
- `rag_retrieval_latency_ms`: Retrieval latency
- `rag_llm_latency_ms`: LLM latency
- `rag_errors_total`: Total errors
- `rag_guardrail_failures_total`: Guardrail rejections
- `rag_active_requests`: Active requests
- `rag_products_loaded_total`: Products loaded
- `llm_tokens_used_total`: Token usage

### Grafana Dashboards

1. Access Grafana at http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to "shopRAG Overview Dashboard"

Dashboard shows:
- Request rate and latency
- LLM call rate and errors
- Active requests and products loaded
- Embedding and retrieval performance
- Component-level latency breakdown

## Troubleshooting

### Backend fails to start

Check database connectivity:
```bash
docker-compose logs backend
```

Verify `DATABASE_URL` in `.env` is correct.

### Frontend can't reach backend

Ensure backend is healthy:
```bash
docker-compose ps
curl http://localhost:8000/health
```

Services use Docker networking (`shoprag-network`).

### Out of memory

Increase Docker Desktop memory allocation:
- Docker Desktop → Settings → Resources → Memory
- Recommended: 8GB minimum

### Data ingestion fails

Check disk space and memory:
```bash
df -h
docker stats
```

Ingestion requires ~20GB free space for dataset caching.

### Permission errors with volumes

Ensure proper permissions on mounted directories:
```bash
chmod -R 755 data/ logs/ monitoring/
```

## Production Deployment

For production:

1. **Remove development overrides**:
   - Delete or rename `docker-compose.override.yml`

2. **Secure environment variables**:
   - Use Docker secrets or external secret management
   - Never commit `.env` to version control

3. **Adjust resource limits**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

4. **Enable HTTPS**:
   - Add Nginx reverse proxy with SSL certificates

5. **Configure Grafana**:
   - Change default admin password
   - Set `GF_SECURITY_ADMIN_PASSWORD` in docker-compose

## Cleanup

Remove containers and volumes:
```bash
make clean
```

Remove everything including images:
```bash
make clean-all
```

## Common Commands

| Command | Description |
|---------|-------------|
| `make build` | Build all Docker images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View logs |
| `make ingest` | Run data ingestion |
| `make health` | Check service health |
| `make clean` | Remove containers/volumes |
| `make ps` | Show running containers |
| `make stats` | Show resource usage |

## Alternative: Using the Helper Script

You can also use the bash script:

```bash
./scripts/docker-dev.sh start      # Start services
./scripts/docker-dev.sh stop       # Stop services
./scripts/docker-dev.sh logs       # View logs
./scripts/docker-dev.sh build      # Build images
./scripts/docker-dev.sh ingest     # Run ingestion
./scripts/docker-dev.sh clean      # Clean up
```

## Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string

Optional:
- `RAG_MODE` - FULL or MOCK (default: FULL)
- `RETRIEVER_MODE` - postgres or chroma (default: postgres)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `EMBEDDING_MODEL_NAME` - Embedding model (default: BAAI/bge-small-en-v1.5)
- `TOP_K_RESULTS` - Number of results (default: 5)
- `BATCH_SIZE` - Batch size for ingestion (default: 512)

## Service Details

### Backend (Port 8000)
- FastAPI REST API
- Handles RAG queries
- Exposes Prometheus metrics at `/metrics`
- Health check at `/health`

### Frontend (Port 7860)
- Gradio web interface
- Interactive chat UI
- Product selection and query input

### Prometheus (Port 9090)
- Metrics collection
- 15-day data retention
- Scrapes backend every 10 seconds

### Grafana (Port 3000)
- Visualization dashboards
- Pre-configured with Prometheus datasource
- Auto-loaded shopRAG dashboard

### Data Ingestion (On-Demand)
- Downloads product data from HuggingFace
- Generates embeddings
- Populates PostgreSQL database
- Only runs when explicitly called

## Support

For issues or questions, refer to the main README.md or open an issue.
