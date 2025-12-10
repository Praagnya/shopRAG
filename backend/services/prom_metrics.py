# ---------------------------------------------------------
# prom_metrics.py  (FINAL FIXED VERSION)
# ---------------------------------------------------------

from prometheus_client import Counter, Histogram, Gauge

# ------------------------
# API / RAG PIPELINE METRICS
# ------------------------

rag_queries_total = Counter(
    "rag_queries_total",
    "Total number of queries received by the RAG pipeline"
)

rag_llm_calls_total = Counter(
    "rag_llm_calls_total",
    "Total number of LLM calls performed by the RAG pipeline"
)

rag_errors_total = Counter(
    "rag_errors_total",
    "Total number of errors raised anywhere in RAG pipeline"
)

rag_guardrail_failures = Counter(
    "rag_guardrail_failures_total",
    "Number of queries rejected by guardrails"
)

# Latency histograms
rag_pipeline_latency = Histogram(
    "rag_pipeline_latency_ms",
    "End-to-end RAG pipeline latency (ms)",
    buckets=[50, 100, 200, 400, 800, 1500, 3000, 6000, 10000]
)

rag_embedding_latency = Histogram(
    "rag_embedding_latency_ms",
    "Embedding generation latency (ms)"
)

rag_retrieval_latency = Histogram(
    "rag_retrieval_latency_ms",
    "Retriever database latency (ms)"
)

rag_llm_latency = Histogram(
    "rag_llm_latency_ms",
    "LLM latency inside RAG pipeline (ms)"
)

rag_active_requests = Gauge(
    "rag_active_requests",
    "Number of in-flight RAG pipeline requests"
)

rag_products_loaded = Gauge(
    "rag_products_loaded_total",
    "Loaded products in pipeline (Version B only)"
)

# ------------------------
# RAW LLM METRICS (shared by mock and full)
# ------------------------

llm_prompt_chars_total = Counter(
    "llm_prompt_chars_total",
    "Total prompt characters sent to LLM"
)

llm_response_chars_total = Counter(
    "llm_response_chars_total",
    "Total characters received from LLM"
)

llm_tokens_used_total = Counter(
    "llm_tokens_used_total",
    "Total tokens used (prompt + completion)"
)

llm_errors_total = Counter(
    "llm_errors_total",
    "Total number of LLM errors"
)

llm_latency_ms = Histogram(
    "llm_latency_ms",
    "Raw LLM latency (ms)",
    buckets=[50, 100, 200, 400, 800, 1500, 3000, 6000, 10000]
)
