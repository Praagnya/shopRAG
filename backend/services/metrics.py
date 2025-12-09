"""
Central metrics registry for RAG Pipeline (Version B).
These metrics can be consumed by:
- Prometheus (Step 2)
- Internal logging dashboards
- Airflow / batch reporting
"""

import time
from dataclasses import dataclass, field


# ===============================
# LOW-LEVEL TIMER UTILITY
# ===============================

@dataclass
class Timer:
    start_time: float = field(default_factory=time.time)
    end_time: float = None

    def stop(self):
        self.end_time = time.time()

    @property
    def elapsed_ms(self) -> float:
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000


# ===============================
# CENTRAL METRICS STORE
# (Used by RAG pipeline & LLM)
# ===============================

class MetricsStore:
    """In-memory metrics store for Version B instrumentation."""

    def __init__(self):
        # Timings
        self.embedding_times = []
        self.retrieval_times = []
        self.product_metadata_times = []
        self.llm_times = []
        self.pipeline_times = []

        # Counters
        self.guardrail_failures = 0
        self.total_queries = 0

    # --- Recording helpers ---
    def record_embedding_time(self, ms):
        self.embedding_times.append(ms)

    def record_retrieval_time(self, ms):
        self.retrieval_times.append(ms)

    def record_metadata_time(self, ms):
        self.product_metadata_times.append(ms)

    def record_llm_time(self, ms):
        self.llm_times.append(ms)

    def record_pipeline_time(self, ms):
        self.pipeline_times.append(ms)

    def increment_guardrail_failure(self):
        self.guardrail_failures += 1

    def increment_query(self):
        self.total_queries += 1

    # --- Snapshot for dashboards or Prometheus ---
    def snapshot(self):
        """Returns a full metrics snapshot for dashboards."""
        return {
            "total_queries": self.total_queries,
            "guardrail_failures": self.guardrail_failures,
            "avg_embedding_ms": self._avg(self.embedding_times),
            "avg_retrieval_ms": self._avg(self.retrieval_times),
            "avg_metadata_ms": self._avg(self.product_metadata_times),
            "avg_llm_ms": self._avg(self.llm_times),
            "avg_pipeline_ms": self._avg(self.pipeline_times),
        }

    @staticmethod
    def _avg(arr):
        return sum(arr) / len(arr) if arr else 0.0


# ===============================
# GLOBAL METRICS INSTANCE
# ===============================

metrics = MetricsStore()

