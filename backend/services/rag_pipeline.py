import json
from typing import Dict, Any
from pathlib import Path
from backend.services.embedder import get_embedder
from backend.services.retriever_postgres import get_postgres_retriever
from backend.services.llm_client import get_llm_client
from backend.config.settings import DATA_DIR


class RAGPipeline:
    """Main RAG pipeline orchestrator."""

    def __init__(self):
        """Initialize RAG pipeline with all required services."""
        print("Initializing RAG Pipeline...")

        # Load product cache
        cache_filepath = DATA_DIR / "product_cache.json"
        if not cache_filepath.exists():
            raise FileNotFoundError(f"Product cache not found at {cache_filepath}. Run ingestion pipeline first.")

        with open(cache_filepath, 'r') as f:
            self.product_cache = json.load(f)
        print(f"Loaded product cache with {len(self.product_cache)} products")

        # Initialize services
        self.embedder = get_embedder()
        self.retriever = get_postgres_retriever()
        self.llm_client = get_llm_client()
        print("RAG Pipeline ready!")

    def query(self, user_query: str, top_k: int = 5, product_asin: str = None) -> Dict[str, Any]:
        """Process a user query through the RAG pipeline.

        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            product_asin: Optional product ASIN to filter reviews to a specific product

        Returns:
            Dictionary containing response and metadata
        """
        print(f"\n[RAG] Processing query: {user_query}")
        if product_asin:
            print(f"[RAG] Filtering to product ASIN: {product_asin}")

        # Step 1: Embed the query
        print("[RAG] Step 1: Embedding query...")
        query_embedding = self.embedder.embed_text(user_query)

        # Step 2: Retrieve relevant documents
        print(f"[RAG] Step 2: Retrieving top {top_k} documents...")
        retrieval_results = self.retriever.retrieve(
            query_embedding,
            top_k=top_k,
            filter_by_asin=product_asin
        )
        documents = retrieval_results['documents']
        print(f"[RAG] Retrieved {len(documents)} documents")

        # Step 3: Get product metadata
        print("[RAG] Step 3: Loading product metadata...")

        # Determine which ASIN to use for product metadata
        if product_asin:
            # Use the specified product ASIN
            primary_asin = product_asin
        else:
            # Get unique ASINs from retrieved docs and use the first one
            asins = set(doc['metadata'].get('asin') for doc in documents if doc['metadata'].get('asin'))
            primary_asin = list(asins)[0] if asins else None

        product_metadata = {}

        if primary_asin and primary_asin in self.product_cache:
            product_metadata = self.product_cache[primary_asin]
        else:
            # Fallback: create minimal metadata from review metadata
            if documents:
                first_doc_meta = documents[0]['metadata']
                product_metadata = {
                    'title': first_doc_meta.get('product_name', 'Unknown Product'),
                    'main_category': first_doc_meta.get('category', ''),
                    'average_rating': first_doc_meta.get('product_avg_rating', 0),
                    'rating_number': 0,
                    'price': 'N/A',
                    'features': [],
                    'description': ''
                }
            elif primary_asin:
                # No documents but ASIN provided - product has no reviews
                product_metadata = {
                    'title': f'Product {primary_asin}',
                    'main_category': 'Unknown',
                    'average_rating': 0,
                    'rating_number': 0,
                    'price': 'N/A',
                    'features': [],
                    'description': 'No reviews available for this product.'
                }

        # Step 4: Generate response using LLM with product metadata + reviews
        print("[RAG] Step 4: Generating response with LLM...")
        response = self.llm_client.generate_response(user_query, product_metadata, documents)
        print("[RAG] Response generated successfully!")

        # Return complete result
        return {
            'query': user_query,
            'response': response,
            'product_metadata': product_metadata,
            'retrieved_documents': documents,
            'num_documents_used': len(documents)
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of the RAG pipeline components.

        Returns:
            Dictionary with status information
        """
        collection_stats = self.retriever.get_collection_stats()

        return {
            'status': 'ready',
            'num_products': len(self.product_cache),
            'embedding_dimension': self.embedder.get_embedding_dimension(),
            'vector_db': collection_stats,
            'llm_model': self.llm_client.model
        }


# Singleton instance
_rag_pipeline_instance = None


def get_rag_pipeline() -> RAGPipeline:
    """Get or create the singleton RAG pipeline instance.

    Returns:
        RAGPipeline instance
    """
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = RAGPipeline()
    return _rag_pipeline_instance
