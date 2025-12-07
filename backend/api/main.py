from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.models.schemas import QueryRequest, QueryResponse, StatusResponse, ProductInfo, RetrievedDocument
from backend.services.rag_pipeline import get_rag_pipeline
from backend.config.settings import CORS_ORIGINS, API_HOST, API_PORT
import uvicorn


# Initialize FastAPI app
app = FastAPI(
    title="shopRAG API",
    description="Retail RAG Chatbot API for Amazon Cell Phones & Accessories",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline (lazy loading)
rag_pipeline = None


def get_pipeline():
    """Get or initialize the RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = get_rag_pipeline()
    return rag_pipeline


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("Starting shopRAG API...")
    try:
        get_pipeline()
        print("RAG Pipeline loaded successfully!")
    except Exception as e:
        print(f"Warning: Could not initialize RAG pipeline: {e}")
        print("Pipeline will be initialized on first query.")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "shopRAG API - Retail RAG Chatbot",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "status": "/api/status",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status."""
    try:
        pipeline = get_pipeline()
        status = pipeline.get_pipeline_status()

        return StatusResponse(
            status=status['status'],
            num_products=status['num_products'],
            embedding_dimension=status['embedding_dimension'],
            vector_db_count=status['vector_db']['count'],
            llm_model=status['llm_model']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the RAG system.

    Args:
        request: Query request containing the user's question

    Returns:
        Query response with answer and supporting documents
    """
    try:
        pipeline = get_pipeline()

        # Process query through RAG pipeline
        result = pipeline.query(
            request.query,
            top_k=request.top_k,
            product_asin=request.product_asin
        )

        # Format product info
        product_info = None
        if result.get('product_metadata'):
            pm = result['product_metadata']
            product_info = ProductInfo(
                title=pm.get('title', 'Unknown Product'),
                category=pm.get('main_category', ''),
                average_rating=pm.get('average_rating'),
                rating_number=pm.get('rating_number', 0),
                price=str(pm.get('price', 'N/A')),
                features=pm.get('features', []),
                description=pm.get('description', '')
            )

        # Format retrieved documents
        retrieved_docs = [
            RetrievedDocument(
                text=doc['text'],
                metadata=doc['metadata'],
                distance=doc.get('distance')
            )
            for doc in result['retrieved_documents']
        ]

        return QueryResponse(
            query=result['query'],
            response=result['response'],
            product_info=product_info,
            num_documents_used=result['num_documents_used'],
            retrieved_documents=retrieved_docs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
