"""
Neural Glass AI Orchestrator — Server Composition Root
"""

import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.health import health_router, livez_probe, readyz_probe, healthz_probe
from core.tracing import set_request_id, reset_request_id
from websocket.manager import manager
from orchestrator.pipeline import safe_run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Validation ---
    try:
        log_event("app_startup_begin", version=settings.app_version, environment=settings.app_env)
        settings.validate_startup_credentials()
        log_event("startup_validation_passed")
    except Exception as e:
        log_event("startup_validation_failed", error=str(e), level="critical")
        sys.exit(1)

    yield

    # --- Graceful Shutdown ---
    log_event("app_shutdown_begin")
    await manager.graceful_disconnect_all()
    await asyncio.sleep(0.1)
    log_event("app_shutdown_complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Operational Probes Router
app.include_router(health_router)

# Mount Static Files (if directory exists)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.middleware("http")
async def request_tracing_and_metrics_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID")
    active_req_id = set_request_id(req_id)
    metrics.increment_requests()

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = active_req_id
        return response
    finally:
        reset_request_id()


@app.get("/")
async def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({
        "status": "live",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "message": "Neural Glass AI Orchestrator API is running. Mount static/index.html to render UI at root."
    })


@app.websocket("/ws/orchestrate")
async def websocket_orchestrate(websocket: WebSocket):
    conn_id = set_request_id()
    await manager.connect(conn_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt", "")
            if prompt:
                await safe_run_pipeline(websocket, prompt)
    except WebSocketDisconnect:
        manager.disconnect(conn_id)
    except Exception as e:
        log_event("ws_error", error=str(e), level="error")
        manager.disconnect(conn_id)
    finally:
        reset_request_id()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=settings.host, port=settings.port, reload=False)