from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data (bundled with the deployment)
DATA_PATH = os.path.join(os.path.dirname(__file__), "latency_data.json")
with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)


class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.post("/api/latency")
def latency_metrics(req: LatencyRequest):
    # Filter records by requested regions
    filtered = [r for r in TELEMETRY if r["region"] in req.regions]

    # Group by region
    by_region: dict[str, list] = {}
    for r in filtered:
        by_region.setdefault(r["region"], []).append(r)

    result = {}
    for region, records in by_region.items():
        latencies = sorted([r["latency_ms"] for r in records])
        uptimes = [r["uptime_pct"] for r in records]
        n = len(latencies)

        result[region] = {
            "avg_latency": round(sum(latencies) / n, 4),
            "p95_latency": round(latencies[int(n * 0.95)], 4),
            "avg_uptime": round(sum(uptimes) / n, 4),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        }

    return result
