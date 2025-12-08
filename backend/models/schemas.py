from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    query: str = Field(..., description="User's question about products", min_length=1, max_length=500)
    top_k: Optional[int] = Field(5, description="Number of reviews to retrieve", ge=1, le=20)
    product_asin: Optional[str] = Field(None, description="Optional product ASIN to filter reviews to a specific product")


class ProductInfo(BaseModel):
    """Product information model."""
    title: str
    category: str
    average_rating: Optional[float]
    rating_number: int
    price: Optional[str]
    features: List[str]
    description: str


class RetrievedDocument(BaseModel):
    """Retrieved document model."""
    text: str
    metadata: Dict[str, Any]
    distance: Optional[float]


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    query: str
    response: str
    product_info: Optional[ProductInfo]
    num_documents_used: int
    retrieved_documents: Optional[List[RetrievedDocument]] = None


class StatusResponse(BaseModel):
    """System status response."""
    status: str
    num_products: int
    embedding_dimension: int
    vector_db_count: int
    llm_model: str
