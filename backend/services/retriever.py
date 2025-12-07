import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from backend.config.settings import CHROMA_DB_PATH, COLLECTION_NAME, TOP_K_RESULTS


class VectorRetriever:
    """Service for retrieving relevant documents from ChromaDB."""

    def __init__(self, collection_name: str = COLLECTION_NAME):
        """Initialize ChromaDB client and collection.

        Args:
            collection_name: Name of the ChromaDB collection
        """
        print(f"Initializing ChromaDB client at {CHROMA_DB_PATH}")
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Connected to existing collection: {collection_name}")
            print(f"Collection contains {self.collection.count()} documents")
        except Exception as e:
            print(f"Collection '{collection_name}' not found. Create it first by running the ingestion pipeline.")
            raise e

    def retrieve(self, query_embedding: List[float], top_k: int = TOP_K_RESULTS,
                 filter_by_asin: str = None) -> Dict[str, Any]:
        """Retrieve most similar documents for a query embedding.

        Args:
            query_embedding: Query vector embedding
            top_k: Number of results to return
            filter_by_asin: Optional ASIN to filter results to a specific product

        Returns:
            Dictionary containing retrieved documents and metadata
        """
        # Build where clause for filtering
        where_clause = None
        if filter_by_asin:
            where_clause = {"asin": filter_by_asin}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )

        # Format results
        documents = []
        for i in range(len(results['documents'][0])):
            doc = {
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i] if results['distances'] else None,
                'id': results['ids'][0][i]
            }
            documents.append(doc)

        return {
            'documents': documents,
            'count': len(documents)
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        return {
            'name': self.collection.name,
            'count': self.collection.count(),
        }


# Singleton instance
_retriever_instance = None


def get_retriever() -> VectorRetriever:
    """Get or create the singleton retriever instance.

    Returns:
        VectorRetriever instance
    """
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = VectorRetriever()
    return _retriever_instance
