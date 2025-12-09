import json
import os
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ----------------------------
# Paths
# ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_LOG_PATH = os.path.join(BASE_DIR, "logs", "api_logs.json")
LLM_LOG_PATH = os.path.join(BASE_DIR, "logs", "llm_logs.json")
DASHBOARD_HTML = os.path.join(BASE_DIR, "dashboard.html")

# ----------------------------
# Helpers
# ----------------------------

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r") as f:
        for line in f:
            try:
                rows.append(json.loads(line.strip()))
            except:
                continue
    return rows

# ----------------------------
# Load logs
# ----------------------------

api_logs = load_jsonl(API_LOG_PATH)
llm_logs = load_jsonl(LLM_LOG_PATH)

df_api = pd.DataFrame(api_logs)
df_llm = pd.DataFrame(llm_logs)

print(f"API LOG COUNT = {len(df_api)}")
print(f"LLM LOG COUNT = {len(df_llm)}")

# ----------------------------
# MOCK LLM DATA if none
# ----------------------------

if df_llm.empty:
    df_llm = pd.DataFrame([
        {"latency_ms": 900, "prompt_chars": 640, "response_chars": 300},
        {"latency_ms": 700, "prompt_chars": 520, "response_chars": 180},
        {"latency_ms": 1100, "prompt_chars": 800, "response_chars": 360},
    ])

# ----------------------------
# Normalize LLM metrics
# ----------------------------

df_llm["prompt_chars"] = pd.to_numeric(df_llm.get("prompt_chars", 0), errors="coerce").fillna(0)
df_llm["response_chars"] = pd.to_numeric(df_llm.get("response_chars", 0), errors="coerce").fillna(0)
df_llm["latency_ms"] = pd.to_numeric(df_llm.get("latency_ms", 0), errors="coerce").fillna(0)

df_llm["prompt_tokens"] = (df_llm["prompt_chars"] // 4).astype(int)
df_llm["completion_tokens"] = (df_llm["response_chars"] // 4).astype(int)
df_llm["total_tokens"] = df_llm["prompt_tokens"] + df_llm["completion_tokens"]
avg_total_tokens = df_llm["total_tokens"].mean()

df_llm = df_llm.reset_index().rename(columns={"index": "call_id"})
df_llm["call_id"] = df_llm["call_id"] + 1

# ----------------------------
# API Metrics
# ----------------------------

if not df_api.empty:
    df_api["is_error"] = df_api["status_code"] >= 400
    overall_avg_latency = df_api["latency_ms"].mean()
    overall_p95_latency = np.percentile(df_api["latency_ms"], 95)
    overall_success_rate = (1 - df_api["is_error"].mean()) * 100
else:
    overall_avg_latency = 0
    overall_p95_latency = 0
    overall_success_rate = 100

# ----------------------------
# KPI Color Function
# ----------------------------

def kpi_color(metric, good, warn):
    if metric <= good:
        return "#27ae60"
    elif metric <= warn:
        return "#f1c40f"
    return "#e74c3c"

# ----------------------------
# Plotly Graphs (with JS bundled)
# ----------------------------

latency_html = px.bar(
    df_api.groupby("path")["latency_ms"].mean(),
    title="Average API Latency (ms)"
).to_html(full_html=False, include_plotlyjs=True)

error_html = px.bar(
    df_api.groupby("path")["is_error"].mean() * 100,
    title="Error Rate (%) by Endpoint"
).to_html(full_html=False, include_plotlyjs=False)

tokens_html = go.Figure([
    go.Scatter(x=df_llm["call_id"], y=df_llm["prompt_tokens"], mode="lines+markers", name="Prompt Tokens"),
    go.Scatter(x=df_llm["call_id"], y=df_llm["completion_tokens"], mode="lines+markers", name="Completion Tokens")
]).to_html(full_html=False, include_plotlyjs=False)

llm_latency_html = px.line(
    df_llm, x="call_id", y="latency_ms", title="LLM Latency per Call (ms)"
).to_html(full_html=False, include_plotlyjs=False)

# ----------------------------
# Build HTML
# ----------------------------

html = f"""
<html>
<head>
<title>shopRAG Dashboard</title>

<style>
body {{
    font-family: Arial;
    background: #ffffff;
    padding: 20px;
}}
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}}
.kpi {{
    padding: 20px;
    background: #f5f5f5;
    border-radius: 10px;
    text-align: center;
}}
.chart {{
    background: #f5f5f5;
    margin-top: 20px;
    padding: 20px;
    border-radius: 10px;
}}
</style>

</head>
<body>

<h1>📊 shopRAG Monitoring Dashboard</h1>

<div class="kpi-grid">
    <div class="kpi" style="border-left: 6px solid {kpi_color(overall_avg_latency, 100, 300)}">
        <h3>Average Latency</h3>
        <p>{overall_avg_latency:.2f} ms</p>
    </div>

    <div class="kpi" style="border-left: 6px solid {kpi_color(overall_p95_latency, 200, 500)}">
        <h3>P95 Latency</h3>
        <p>{overall_p95_latency:.2f} ms</p>
    </div>

    <div class="kpi" style="border-left: 6px solid {kpi_color(100-overall_success_rate, 5, 20)}">
        <h3>Success Rate</h3>
        <p>{overall_success_rate:.1f}%</p>
    </div>

    <div class="kpi" style="border-left: 6px solid {kpi_color(avg_total_tokens, 200, 500)}">
        <h3>Avg Tokens</h3>
        <p>{avg_total_tokens:.1f}</p>
    </div>
</div>

<div class="chart">{latency_html}</div>
<div class="chart">{error_html}</div>
<div class="chart">{tokens_html}</div>
<div class="chart">{llm_latency_html}</div>

</body>
</html>
"""

with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard generated → {DASHBOARD_HTML}")
