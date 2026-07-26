"""
Neural Glass AI Orchestrator — Server Composition Root
"""

import sys
import asyncio
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.health import health_router, livez_probe, readyz_probe, healthz_probe
from core.tracing import set_request_id, reset_request_id
from core.git import get_git_status, get_unified_diff, get_commit_history, rollback_to_commit
from orchestrator.indexer import index_workspace
from orchestrator.dep_graph import get_dependency_graph
from orchestrator.state import OrchestratorState
from websocket.manager import manager
from orchestrator.pipeline import safe_run_pipeline

# Global state reference for runtime state inspection
latest_orchestrator_state: Optional[OrchestratorState] = None


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


# --- Phase V5.1: Git Intelligence API Endpoints ---

@app.get("/api/git/status")
async def api_git_status():
    """Returns modified, untracked, and staged files in the workspace sandbox."""
    return get_git_status()


@app.get("/api/git/diff")
async def api_git_diff():
    """Generates and returns the current unified diff for the workspace."""
    return {"diff": get_unified_diff()}


@app.get("/api/git/commits")
async def api_git_commits():
    """Returns the recent git commit history for the workspace sandbox."""
    return {"commits": get_commit_history()}


@app.post("/api/git/rollback")
async def api_git_rollback(payload: dict):
    """Hard resets the workspace sandbox to a target commit hash."""
    target_hash = payload.get("hash")
    if not target_hash:
        raise HTTPException(status_code=400, detail="Commit hash required for rollback")
    success = rollback_to_commit(target_hash)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to rollback to commit {target_hash}")
    return {"status": "success", "hash": target_hash}


# --- Phase V5.2: Codebase Intelligence API Endpoints ---

@app.get("/api/codebase/symbols")
async def api_codebase_symbols():
    """Returns all extracted classes, functions, and symbols across the workspace."""
    return index_workspace()


@app.get("/api/codebase/graph")
async def api_codebase_graph():
    """Returns the module dependency graph nodes and edges for the workspace."""
    return get_dependency_graph()


# --- Phase V5.3: Specialized Agent Multi-Mesh State Endpoint ---

@app.get("/api/agents/state")
async def api_agents_state():
    """Returns the latest multi-agent execution state snapshot."""
    if latest_orchestrator_state:
        return {
            "requirement": latest_orchestrator_state.get("user_requirement", ""),
            "clean_requirement": latest_orchestrator_state.get("clean_requirement", ""),
            "parsed_intent": latest_orchestrator_state.get("parsed_intent", ""),
            "plan_steps": latest_orchestrator_state.get("plan_steps", []),
            "security_findings": latest_orchestrator_state.get("security_findings", []),
            "code_review_notes": latest_orchestrator_state.get("code_review_notes", []),
            "has_readme": bool(latest_orchestrator_state.get("documentation_markdown", "")),
            "files_count": len(latest_orchestrator_state.get("generated_files", {}))
        }
    return {"status": "idle", "message": "No pipeline runs executed yet."}


# --- WebSocket Orchestration Route ---

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