from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import json
from pathlib import Path

app = FastAPI(title="GridFlex Compute v2 API")

MOCK = Path(__file__).resolve().parents[3] / "data" / "mock" / "gridflex_demo_response.json"

@app.get("/health")
def health():
    return {"status": "ok", "service": "gridflex-api"}

@app.get("/api/v1/demo")
def demo():
    return json.loads(MOCK.read_text())

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
