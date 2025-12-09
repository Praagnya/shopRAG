import time
import json
import logging
import os
from typing import Dict, Any

from backend.services.prom_metrics import (
    llm_prompt_chars_total,
    llm_response_chars_total,
    llm_latency_ms,
    llm_tokens_used_total,
    llm_errors_total,
    llm_calls_total,
    llm_prompt_tokens_total,
    llm_completion_tokens_total,
    llm_cost_usd_total,
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

COST_PER_1K_IN = 0.00015
COST_PER_1K_OUT = 0.00060

def monitor_llm_call(model, prompt, fn):
    """
    Wraps every LLM call with:
    - latency measure
    - token/char counting
    - cost tracking
    - logging
    """
    start = time.time()
    try:
        response = fn()
        latency = (time.time() - start) * 1000

        usage = response.usage
        prompt_tokens = usage.prompt_tokens or 0
        completion_tokens = usage.completion_tokens or 0
        total_tokens = usage.total_tokens or 0

        prompt_chars = len(prompt)
        response_text = response.choices[0].message.content
        response_chars = len(response_text)

        # Update metrics
        llm_latency_ms.observe(latency)
        llm_prompt_chars_total.inc(prompt_chars)
        llm_response_chars_total.inc(response_chars)
        llm_tokens_used_total.inc(total_tokens)

        llm_calls_total.inc()
        llm_prompt_tokens_total.inc(prompt_tokens)
        llm_completion_tokens_total.inc(completion_tokens)

        # Cost calculation
        cost = (prompt_tokens / 1000) * COST_PER_1K_IN + \
               (completion_tokens / 1000) * COST_PER_1K_OUT
        llm_cost_usd_total.inc(cost)

        # Logging
        log_llm_event({
            "timestamp": time.time(),
            "model": model,
            "prompt_chars": prompt_chars,
            "response_chars": response_chars,
            "latency_ms": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "error": None
        })

        response.llm_latency_ms = latency
        return response

    except Exception as e:
        llm_errors_total.inc()

        log_llm_event({
            "timestamp": time.time(),
            "model": model,
            "error": str(e),
        })
        raise
