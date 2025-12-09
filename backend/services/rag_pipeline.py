import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

from backend.services.embedder import get_embedder
from backend.services.metrics import metrics, Timer
from backend.services.llm_client import get_llm_client
from backend.services.guardrails import get_guardrails
from backend.config.settings import DATA_DIR, RETRIEVER_MODE

from backend.services.prom_metrics import (
    rag_queries_total,
    rag_llm_calls_total,
    rag_errors_total,
    rag_pipeline_latency,
    rag_embedding_latency,
    rag_retrieval_latency,
    rag_llm_latency,
    rag_active_requests,
    rag_guardrail_failures,
    rag_products_loaded,
)


class RAGPipeline:
    """
    Unified RAG Pipeline supporting Version A (MOCK) and Version B (FULL).
    """

    def __init__(self):
        self.mode = os.getenv("RAG_MODE", "FULL").upper().strip()
        print(f"Initializing RAG Pipeline in mode: {self.mode}")

        self.guardrails = get_guardrails()
        self.llm_client = get_llm_client()

        if self.mode == "MOCK":
            self._init_mock_mode()
        else:
            self._init_full_mode()

    # ----------------------------------------------------------------------
    # FULL MODE (Version B)
    # ----------------------------------------------------------------------
    def _init_full_mode(self):
        print("Loading FULL RAG Pipeline (Version B)...")

        cache_filepath = DATA_DIR / "product_cache.json"
        self.product_cache = {}

        if cache_filepath.exists():
            with open(cache_filepath, "r") as f:
                self.product_cache = json.load(f)
            print(f"Loaded product cache with {len(self.product_cache)} products")
            rag_products_loaded.set(len(self.product_cache))
        else:
            print(f" Warning: Product cache missing at {cache_filepath}")
            print("   Continuing with EMPTY product cache")

        self.embedder = get_embedder()

        print(f"Retriever mode selected: {RETRIEVER_MODE}")
        if RETRIEVER_MODE == "postgres":
            from backend.services.retriever_postgres import get_postgres_retriever
            self.retriever = get_postgres_retriever()
            print("🔗 Using PostgreSQL retriever (Production).")
        elif RETRIEVER_MODE == "chroma":
            from backend.services.retriever import VectorRetriever
            self.retriever = VectorRetriever()
            print("🔗 Using ChromaDB retriever.")
        else:
            raise ValueError(f"Invalid RETRIEVER_MODE: {RETRIEVER_MODE}")

        print("FULL RAG Pipeline ready! (Version B)")

    # ----------------------------------------------------------------------
    # MOCK MODE (Version A)
    # ----------------------------------------------------------------------
    def _init_mock_mode(self):
        print("Loading MOCK RAG Pipeline (Version A)...")

        self.product_cache = {}
        self.embedder = None
        self.retriever = None

        print("MOCK RAG Pipeline ready! (Version A)")

    # ----------------------------------------------------------------------
    # PUBLIC QUERY ROUTER
    # ----------------------------------------------------------------------
    def query(self, user_query: str, top_k: int = 5, product_asin: Optional[str] = None):
        metrics.increment_query()
        rag_queries_total.inc()

        if self.mode == "MOCK":
            return self._query_mock(user_query, top_k, product_asin)
        return self._query_full(user_query, top_k, product_asin)

    # ----------------------------------------------------------------------
    # FULL PIPELINE EXECUTION (Version B)
    # ----------------------------------------------------------------------
    def _query_full(self, user_query: str, top_k: int, product_asin: Optional[str]):

        pipeline_timer = Timer()
        rag_active_requests.inc()

        try:
            print(f"\n[RAG] Processing query: {user_query}")

            # Step 0 — Guardrails
            print("[RAG] Step 0: Guardrail validation...")
            is_valid, error_msg = self.guardrails.validate_query(user_query)
            if not is_valid:
                rag_guardrail_failures.inc()
                raise ValueError(f"Invalid query: {error_msg}")

            # Step 1 — Embedding
            print("[RAG] Step 1: Embedding query...")
            embed_timer = Timer()
            query_embedding = self.embedder.embed_text(user_query)
            embed_timer.stop()
            rag_embedding_latency.observe(embed_timer.elapsed_ms)
            metrics.record_embedding_time(embed_timer.elapsed_ms)

            # Step 2 — Retrieval
            print("[RAG] Step 2: Retrieving documents...")
            retrieval_timer = Timer()

            retrieval_results = self.retriever.retrieve(
                query_embedding,
                top_k=top_k,
                filter_by_asin=product_asin,
            )

            retrieval_timer.stop()
            rag_retrieval_latency.observe(retrieval_timer.elapsed_ms)
            metrics.record_retrieval_time(retrieval_timer.elapsed_ms)

            documents = retrieval_results["documents"]
            print(f"[RAG] Retrieved {len(documents)} documents")

            # Step 3 — Product metadata
            print("[RAG] Step 3: Loading metadata...")
            metadata_timer = Timer()

            if product_asin:
                primary_asin = product_asin
            else:
                asins = {doc["metadata"].get("asin") for doc in documents}
                primary_asin = next(iter(asins), None)

            if primary_asin and primary_asin in self.product_cache:
                product_metadata = self.product_cache[primary_asin]
            else:
                # fallback construction
                if documents:
                    m = documents[0]["metadata"]
                    product_metadata = {
                        "title": m.get("product_name", "Unknown Product"),
                        "main_category": m.get("category", ""),
                        "average_rating": m.get("product_avg_rating", 0),
                        "rating_number": 0,
                        "price": "N/A",
                        "features": [],
                        "description": "",
                    }
                else:
                    product_metadata = {}

            metadata_timer.stop()
            metrics.record_metadata_time(metadata_timer.elapsed_ms)

            # Step 4 — LLM call
            print("[RAG] Step 4: Calling LLM...")
            rag_llm_calls_total.inc()
            llm_timer = Timer()

            response = self.llm_client.generate_response(
                user_query, product_metadata, documents
            )

            llm_timer.stop()
            rag_llm_latency.observe(llm_timer.elapsed_ms)
            metrics.record_llm_time(llm_timer.elapsed_ms)

            # Pipeline complete
            pipeline_timer.stop()
            rag_pipeline_latency.observe(pipeline_timer.elapsed_ms)
            metrics.record_pipeline_time(pipeline_timer.elapsed_ms)

            return {
                "query": user_query,
                "response": response,
                "product_metadata": product_metadata,
                "retrieved_documents": documents,
                "num_documents_used": len(documents),
            }

        except Exception as e:
            rag_errors_total.inc()
            raise e

        finally:
            rag_active_requests.dec()

    # ----------------------------------------------------------------------
    # MOCK PIPELINE EXECUTION (Version A)
    # ----------------------------------------------------------------------
    def _query_mock(self, user_query: str, top_k: int, product_asin: Optional[str]):

        pipeline_timer = Timer()

        print(f"\n[MOCK RAG] Processing query: {user_query}")

        is_valid, error_msg = self.guardrails.validate_query(user_query)
        if not is_valid:
            metrics.increment_guardrail_failure()
            raise ValueError(f"Invalid query: {error_msg}")

        mock_documents = [
            {
                "text": "This is a mock review describing product quality and durability.",
                "metadata": {"asin": product_asin or "MOCK-ASIN", "review_rating": 5},
                "distance": 0.1,
            },
            {
                "text": "Customers appreciated the battery life and price point.",
                "metadata": {"asin": product_asin or "MOCK-ASIN", "review_rating": 4},
                "distance": 0.2,
            },
        ][:top_k]

        mock_metadata = {
            "title": "Mock Product - Version A",
            "main_category": "Cell Phones & Accessories",
            "average_rating": 4.5,
            "rating_number": 100,
            "price": "19.99",
            "features": ["Lightweight", "Durable", "Budget-friendly"],
            "description": "This is a mock product used for monitoring demo.",
        }

        response = self.llm_client.generate_response(
            user_query, mock_metadata, mock_documents
        )

        pipeline_timer.stop()
        metrics.record_pipeline_time(pipeline_timer.elapsed_ms)

        return {
            "query": user_query,
            "response": response,
            "product_metadata": mock_metadata,
            "retrieved_documents": mock_documents,
            "num_documents_used": len(mock_documents),
        }

    # ----------------------------------------------------------------------
    # STATUS ENDPOINT
    # ----------------------------------------------------------------------
    def get_pipeline_status(self):
        if self.mode == "FULL":
            stats = self.retriever.get_collection_stats()
            embed_dim = self.embedder.get_embedding_dimension()
            num_products = len(self.product_cache)
        else:
            stats = {"count": 0, "index_type": "mock", "details": "No vector DB in MOCK mode"}
            embed_dim = 0
            num_products = 0

        return {
            "status": "ready",
            "mode": self.mode,
            "num_products": num_products,
            "embedding_dimension": embed_dim,
            "vector_db": stats,
            "llm_model": self.llm_client.model,
        }


# Singleton
_rag_pipeline_instance = None

def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = RAGPipeline()
    return _rag_pipeline_instance
