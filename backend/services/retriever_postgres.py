"""
PostgreSQL + pgvector retriever for semantic search.
"""

import os
import psycopg2
from typing import List, Dict, Any
from dotenv import load_dotenv
from backend.config.settings import TOP_K_RESULTS

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


class PostgresVectorRetriever:
    """Service for retrieving relevant documents from PostgreSQL + pgvector."""

    def __init__(self):
        """Initialize PostgreSQL connection."""
        print(f"Connecting to PostgreSQL vector database...")
        self.database_url = DATABASE_URL
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        # Test connection
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        print(f"Connected to PostgreSQL")
        print(f"Database contains {count} reviews with embeddings")

    def retrieve(self, query_embedding: List[float], top_k: int = TOP_K_RESULTS,
                 filter_by_asin: str = None) -> Dict[str, Any]:
        """Retrieve most similar documents for a query embedding.

        Args:
            query_embedding: Query vector embedding (384 dimensions)
            top_k: Number of results to return
            filter_by_asin: Optional ASIN to filter results to a specific product

        Returns:
            Dictionary containing retrieved documents and metadata
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        # Build query with optional ASIN filter and quality guardrails
        if filter_by_asin:
            query = """
                SELECT
                    id,
                    review_text,
                    asin,
                    product_name,
                    category,
                    product_avg_rating,
                    review_rating,
                    verified_purchase,
                    helpful_vote,
                    timestamp,
                    embedding <=> %s::vector AS distance
                FROM reviews
                WHERE asin = %s
                  AND embedding <=> %s::vector < 0.65
                  AND LENGTH(review_text) >= 30
                  AND review_rating > 0
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cursor.execute(query, (query_embedding, filter_by_asin, query_embedding, query_embedding, top_k))
        else:
            query = """
                SELECT
                    id,
                    review_text,
                    asin,
                    product_name,
                    category,
                    product_avg_rating,
                    review_rating,
                    verified_purchase,
                    helpful_vote,
                    timestamp,
                    embedding <=> %s::vector AS distance
                FROM reviews
                WHERE embedding <=> %s::vector < 0.65
                  AND LENGTH(review_text) >= 30
                  AND review_rating > 0
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """
            cursor.execute(query, (query_embedding, query_embedding, query_embedding, top_k))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Format results
        documents = []
        for row in results:
            doc = {
                'id': str(row[0]),
                'text': row[1],
                'metadata': {
                    'asin': row[2],
                    'product_name': row[3],
                    'category': row[4],
                    'product_avg_rating': float(row[5]) if row[5] is not None else 0.0,
                    'review_rating': float(row[6]) if row[6] is not None else 0.0,
                    'verified_purchase': bool(row[7]),
                    'helpful_vote': int(row[8]) if row[8] is not None else 0,
                    'timestamp': int(row[9]) if row[9] is not None else 0
                },
                'distance': float(row[10])
            }
            documents.append(doc)

        return {
            'documents': documents,
            'count': len(documents)
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the database.

        Returns:
            Dictionary with database statistics
        """
        conn = psycopg2.connect(self.database_url)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM reviews")
        review_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            'name': 'postgres_pgvector',
            'count': review_count,
            'product_count': product_count
        }


# Singleton instance
_retriever_instance = None


def get_postgres_retriever() -> PostgresVectorRetriever:
    """Get or create the singleton retriever instance.

    Returns:
        PostgresVectorRetriever instance
    """
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = PostgresVectorRetriever()
    return _retriever_instance
