import time
import json
import logging
import os
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge


# ============================================================
# Ensure logs directory exists (JSON logs)
# ============================================================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "api_logs.json")

logger = logging.getLogger("api_monitor")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(LOG_FILE)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


# ============================================================
# PROMETHEUS METRICS (NEW)
# ============================================================

# Count total API requests
api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests received",
    ["path", "method"]
)

# Count requests that result in errors
api_errors_total = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["path", "method"]
)

# Track API request latency
api_latency_ms = Histogram(
    "api_latency_ms",
    "API request latency in milliseconds",
    ["path", "method"]
)

# Track number of active API requests
api_active_requests = Gauge(
    "api_active_requests",
    "Current number of active API requests"
)


# ============================================================
# API MONITORING MIDDLEWARE
# ============================================================
class APIMonitorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        """Middleware that captures:
        - Latency
        - Errors
        - Active requests
        - JSON logs
        - Prometheus metrics
        """

        path = request.url.path
        method = request.method

        start_time = time.time()
        api_active_requests.inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
            error_message = None

        except Exception as e:
            status_code = 500
            error_message = str(e)

            # Prometheus: count error
            api_errors_total.labels(path=path, method=method).inc()

            raise e

        finally:
            api_active_requests.dec()

        # Compute latency
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Prometheus: record metrics
        api_requests_total.labels(path=path, method=method).inc()
        api_latency_ms.labels(path=path, method=method).observe(latency_ms)

        # JSON Log Entry
        log_entry = {
            "path": path,
            "method": method,
            "timestamp": time.time(),
            "latency_ms": latency_ms,
            "status_code": status_code,
            "client_host": request.client.host,
            "error": error_message,
        }

        logger.info(json.dumps(log_entry))

        return response
