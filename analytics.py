import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

BASE = os.path.dirname(os.path.abspath(__file__))


# --- Load API Logs ---
def load_logs(path):
    logs = []
    try:
        with open(path, "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
    except FileNotFoundError:
        print(f"[WARN] Log file not found: {path}")
    return logs

api_logs = load_logs(os.path.join(BASE, "logs", "api_logs.json"))
llm_logs = load_logs(os.path.join(BASE, "logs", "llm_logs.json"))

#api_logs = load_logs("logs/api_logs.json")
#llm_logs = load_logs("logs/llm_logs.json")

df_api = pd.DataFrame(api_logs)
df_llm = pd.DataFrame(llm_logs)

print("API LOG COUNT:", len(df_api))
print(df_api)

print("=== API LOG SUMMARY ===")
print(df_api.head())

# -------------------------
# 1️ API LATENCY METRICS
# -------------------------
if df_api.empty:
    print("No API logs found — nothing to analyze.")
    exit()

api_latency = df_api.groupby("path")["latency_ms"].agg(
    avg_latency="mean",
    p95_latency=lambda x: np.percentile(x, 95),
    max_latency="max",
    calls="count"
)

print("\n=== LATENCY METRICS PER ENDPOINT ===")
print(api_latency)

# -------------------------
# 2️ API ERROR RATE
# -------------------------

df_api["is_error"] = df_api["status_code"] >= 400

error_rate = df_api.groupby("path")["is_error"].mean() * 100

print("\n=== ERROR RATE (%) PER ENDPOINT ===")
print(error_rate)

# -------------------------
# 3️ LLM METRICS
# -------------------------

if len(df_llm) > 0 and "latency_ms" in df_llm.columns:
    llm_summary = {
        "avg_llm_latency_ms": df_llm["latency_ms"].mean(),
        "max_llm_latency_ms": df_llm["latency_ms"].max(),
        "avg_prompt_tokens": df_llm.get("prompt_tokens", pd.Series([0])).mean(),
        "avg_completion_tokens": df_llm.get("completion_tokens", pd.Series([0])).mean(),
        "total_llm_calls": len(df_llm),
    }

    print("\n=== LLM METRICS ===")
    print(llm_summary)
else:
    print("\n=== NO LLM METRICS YET — llm_logs.json IS EMPTY OR INCOMPLETE ===")

# -------------------------
# 4️ MOST EXPENSIVE ENDPOINTS (by latency)
# -------------------------

top_endpoints = api_latency.sort_values("avg_latency", ascending=False).head(5)

print("\n=== MOST EXPENSIVE ENDPOINTS (Avg Latency) ===")
print(top_endpoints)

# -------------------------
# 5️ VISUALIZATIONS
# -------------------------

plt.figure(figsize=(10,5))
api_latency["avg_latency"].plot(kind="bar", title="Avg Latency per Endpoint (ms)")
plt.ylabel("Latency (ms)")
plt.tight_layout()
plt.savefig("latency_per_endpoint.png")
print("\nSaved: latency_per_endpoint.png")

plt.figure(figsize=(10,5))
error_rate.plot(kind="bar", color="red", title="Error Rate per Endpoint (%)")
plt.ylabel("Error %")
plt.tight_layout()
plt.savefig("error_rate_per_endpoint.png")
print("Saved: error_rate_per_endpoint.png")

print("\n=== ANALYTICS COMPLETE ===")

summary = {
    "latency": api_latency.to_dict(),
    "error_rate": error_rate.to_dict(),
    "llm": llm_summary if len(df_llm) else {},
}

with open("analytics_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("Saved: analytics_summary.json")
