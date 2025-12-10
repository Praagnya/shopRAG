# ---------------------------------------------------------
# llm_monitoring.py  (FINAL FIXED VERSION)
# ---------------------------------------------------------

import time
import json
import logging
import os
from typing import Any, Dict

# ---- Import ALL metrics from prom_metrics (not redefining) ----
from backend.services.prom_metrics import (
    llm_prompt_chars_total,
    llm_response_chars_total,
    llm_latency_ms,
    llm_tokens_used_total,
    llm_errors_total,
)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "llm_logs.json")

logger = logging.getLogger("llm_monitor")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

def log_llm_event(event: Dict[str, Any]):
    logger.info(json.dumps(event))

def monitor_llm_call(model, prompt, fn):

    start = time.time()

    try:
        response = fn()
        elapsed = (time.time() - start) * 1000  # ms

        # Record metrics
        prompt_chars = len(prompt)
        response_chars = len(response.choices[0].message.content)

        llm_prompt_chars_total.inc(prompt_chars)
        llm_response_chars_total.inc(response_chars)

        if hasattr(response.usage, "total_tokens"):
            llm_tokens_used_total.inc(response.usage.total_tokens)

        llm_latency_ms.observe(elapsed)

        # Attach latency for downstream use
        response.llm_latency_ms = elapsed

        # Log JSON
        log_llm_event({
            "timestamp": time.time(),
            "model": model,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "latency_ms": elapsed,
            "tokens_used": getattr(response.usage, "total_tokens", 0),
        })

        return response

    except Exception:
        llm_errors_total.inc()
        raise
