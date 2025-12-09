from prometheus_client import Counter, Histogram, Gauge

# ------------------------
# Counters
# ------------------------
rag_queries_total = Counter(
    "rag_queries_total",
    "Total number of queries received by the RAG pipeline"
)

rag_llm_calls_total = Counter(
    "rag_llm_calls_total",
    "Total number of LLM calls performed"
)

rag_errors_total = Counter(
    "rag_errors_total",
    "Total number of errors raised in RAG pipeline"
)

rag_guardrail_failures = Counter(
    "rag_guardrail_failures_total",
    "Number of queries rejected by guardrails"
)

# ------------------------
# Histograms (latency)
# ------------------------
rag_pipeline_latency = Histogram(
    "rag_pipeline_latency_ms",
    "RAG end-to-end pipeline latency in milliseconds",
    buckets=[50, 100, 200, 400, 800, 1500, 3000, 6000, 10000]
)

rag_embedding_latency = Histogram(
    "rag_embedding_latency_ms",
    "Embedding generation latency (ms)"
)

rag_retrieval_latency = Histogram(
    "rag_retrieval_latency_ms",
    "Retriever vector DB latency (ms)"
)

rag_llm_latency = Histogram(
    "rag_llm_latency_ms",
    "LLM response time latency (ms)"
)

# ------------------------
# Gauges
# ------------------------
rag_active_requests = Gauge(
    "rag_active_requests",
    "Current number of in-flight pipeline requests"
)

rag_products_loaded = Gauge(
    "rag_products_loaded_total",
    "Number of products loaded into pipeline (Version B only)"
)

