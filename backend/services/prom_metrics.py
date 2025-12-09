# prom_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# ------------------------
# RAG Pipeline Metrics
# ------------------------
rag_queries_total = Counter(
    "rag_queries_total", "Total number of queries received by the RAG pipeline"
)

rag_llm_calls_total = Counter(
    "rag_llm_calls_total", "Total number of LLM calls performed"
)

rag_errors_total = Counter(
    "rag_errors_total", "Total number of errors raised in RAG pipeline"
)

rag_guardrail_failures = Counter(
    "rag_guardrail_failures_total", "Total guardrail validation failures"
)

rag_pipeline_latency = Histogram(
    "rag_pipeline_latency_ms",
    "RAG end-to-end pipeline latency (ms)",
    buckets=[50,100,200,400,800,1500,3000,6000,10000],
)

rag_embedding_latency = Histogram(
    "rag_embedding_latency_ms",
    "Embedding generation latency (ms)",
)

rag_retrieval_latency = Histogram(
    "rag_retrieval_latency_ms",
    "Retriever DB latency (ms)",
)

rag_llm_latency = Histogram(
    "rag_llm_latency_ms",
    "LLM latency within RAG pipeline (ms)",
)

rag_active_requests = Gauge(
    "rag_active_requests", "Current number of in-flight RAG requests"
)

rag_products_loaded = Gauge(
    "rag_products_loaded_total", "Number of products loaded in product cache"
)

# ------------------------
# LLM Metrics (Shared)
# ------------------------
llm_prompt_chars_total = Counter(
    "llm_prompt_chars_total", "Total number of prompt characters sent to LLM"
)

llm_response_chars_total = Counter(
    "llm_response_chars_total", "Total number of response characters returned by LLM"
)

llm_tokens_used_total = Counter(
    "llm_tokens_used_total", "Total number of tokens used (prompt + completion)"
)

llm_latency_ms = Histogram(
    "llm_latency_ms", "LLM latency (ms)",
    buckets=[50,100,200,400,800,1500,3000,6000,10000],
)

llm_errors_total = Counter(
    "llm_errors_total", "Total number of LLM call failures"
)

# ------------------------
# Version B Only: Cost & Token Breakdown
# ------------------------
llm_calls_total = Counter(
    "llm_calls_total", "Total number of raw LLM API calls"
)

llm_prompt_tokens_total = Counter(
    "llm_prompt_tokens_total", "Total number of prompt tokens used"
)

llm_completion_tokens_total = Counter(
    "llm_completion_tokens_total", "Total number of completion tokens used"
)

llm_cost_usd_total = Counter(
    "llm_cost_usd_total", "Estimated USD cost of LLM usage"
)
