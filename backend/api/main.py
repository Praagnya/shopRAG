from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

# Import schemas + pipeline
from backend.models.schemas import QueryRequest, QueryResponse, StatusResponse, ProductInfo, RetrievedDocument
from backend.services.rag_pipeline import get_rag_pipeline
from backend.config.settings import CORS_ORIGINS, API_HOST, API_PORT

# Monitoring middleware
from backend.api.monitoring import APIMonitorMiddleware

# Prometheus endpoint support
import backend.services.prom_metrics  # <-- IMPORTANT: registers metrics
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

import uvicorn


# ------------------------------------------------------
# Initialize FastAPI Application
# ------------------------------------------------------
app = FastAPI(
    title="shopRAG API",
    description="Retail RAG Chatbot API for Amazon Cell Phones & Accessories",
    version="1.0.0",
)

# Monitoring middleware
app.add_middleware(APIMonitorMiddleware)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lazy-loaded RAG pipeline
rag_pipeline = None


def get_pipeline():
    """Lazy initialization of RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = get_rag_pipeline()
    return rag_pipeline


# ------------------------------------------------------
# Startup
# ------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    print("Starting shopRAG API...")
    try:
        get_pipeline()
        print("RAG Pipeline loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not initialize RAG pipeline: {e}")
        print("Pipeline will initialize on first query.")


# ------------------------------------------------------
# Basic Health Endpoints
# ------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "shopRAG API - Retail RAG Chatbot",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "status": "/api/status",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ------------------------------------------------------
# Status Endpoint
# ------------------------------------------------------
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    try:
        pipeline = get_pipeline()
        status = pipeline.get_pipeline_status()

        return StatusResponse(
            status=status.get("status", "unknown"),
            num_products=status.get("num_products", 0),
            embedding_dimension=status.get("embedding_dimension", 0),
            vector_db_count=status.get("vector_db", {}).get("count", 0),
            llm_model=status.get("llm_model", "unknown"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


# ------------------------------------------------------
# Query Endpoint (Main RAG endpoint)
# ------------------------------------------------------
@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        pipeline = get_pipeline()

        result = pipeline.query(
            request.query,
            top_k=request.top_k,
            product_asin=request.product_asin
        )

        # Product info formatting
        pm = result.get("product_metadata", {})
        product_info = ProductInfo(
            title=pm.get("title", "Unknown Product"),
            category=pm.get("main_category", ""),
            average_rating=pm.get("average_rating"),
            rating_number=pm.get("rating_number", 0),
            price=str(pm.get("price", "N/A")),
            features=pm.get("features", []),
            description=pm.get("description", "")
        )

        # Retrieved docs formatting
        retrieved_docs = [
            RetrievedDocument(
                text=doc["text"],
                metadata=doc["metadata"],
                distance=doc.get("distance")
            )
            for doc in result.get("retrieved_documents", [])
        ]

        return QueryResponse(
            query=result["query"],
            response=result["response"],
            product_info=product_info,
            num_documents_used=result.get("num_documents_used", len(retrieved_docs)),
            retrieved_documents=retrieved_docs,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# ------------------------------------------------------
# Prometheus Metrics Endpoint
# ------------------------------------------------------
@app.get("/metrics")
async def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ------------------------------------------------------
# Uvicorn Run
# ------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
