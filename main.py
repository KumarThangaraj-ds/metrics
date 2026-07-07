import uuid
import time

from fastapi import FastAPI, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from fastapi.responses import Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import List, Dict, Any

app = FastAPI(title="Metrics")

start_time = time.time()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["path", "method", "status"]
)

logs: List[Dict[str, Any]] = []

@app.middleware("http")
async def observe_requests(request: Request, call_next):
    # Middleware runs before and after every request
    request_id = str(uuid.uuid4())
    path = request.url.path
    method = request.method
    ts = time.time()
    
    try:
        response = await call_next(request)
        return response
    finally:

        endpoint = request.url.path
        method = request.method
        status_code = getattr(locals().get("response", None), "status_code", 500)

        REQUEST_COUNT.labels(
            path=path,
            method=method,
            status=str(response.status_code),
        ).inc()

        logs.append({
            "level": "info",
            "ts": ts,
            "path": path,
            "request_id": request_id,
        })

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Do not use ["*"] for real apps with login/cookies
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/metrics")
def metrics():
    # Prometheus scrapes this endpoint
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health():
    return {"status": "ok", "uptime_s": time.time() - start_time}

@app.get("/work")
def work(n: str):
    if n:
        return {"email":"23ds", "done": n}
    return {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/logs/tail")
async def logs_tail(limit: int = Query(10, ge=1)):
    return JSONResponse(content=logs[-limit:])
