from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry data
DATA_PATH = os.path.join(os.path.dirname(__file__), "latency_data.json")
with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)


class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.options("/api/latency")
async def options_latency():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.post("/api/latency")
def latency_metrics(req: LatencyRequest):
    filtered = [r for r in TELEMETRY if r["region"] in req.regions]

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

    return JSONResponse(
        content=result,
        headers={"Access-Control-Allow-Origin": "*"},
    )
