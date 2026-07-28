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

from core.knowledge_graph import build_enterprise_knowledge_graph, analyze_impact_radius
from core.pm_engine import decompose_requirement_into_milestones, get_current_roadmap
from core.security import scan_workspace_security, generate_compliance_report
from core.deployment_intel import get_deployment_targets, configure_canary_release
from core.collaboration import get_team_presence, add_inline_comment
from core.ide_integration import generate_inline_completion, get_ide_diagnostics
from core.analytics import generate_platform_analytics
from core.cicd_engine import scaffold_cicd_pipelines
from core.deployment import verify_deployment_health
from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.health import health_router, livez_probe, readyz_probe, healthz_probe
from core.tracing import set_request_id, reset_request_id
from core.git import get_git_status, get_unified_diff, get_commit_history, rollback_to_commit
from core.memory import get_memory_history, init_memory_db
from core.plugins import plugin_registry
from core.multi_repo import discover_workspace_projects, build_cross_repo_dependency_map
from core.k8s_runner import k8s_runner
from orchestrator.indexer import index_workspace
from orchestrator.dep_graph import get_dependency_graph
from orchestrator.state import OrchestratorState
from orchestrator.runner import run_sandbox_command
from websocket.manager import manager
from orchestrator.pipeline import safe_run_pipeline

# Global references for runtime state inspection and HITL synchronization
latest_orchestrator_state: Optional[OrchestratorState] = None
current_approval_event: Optional[asyncio.Event] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Validation ---
    try:
        log_event("app_startup_begin", version=settings.app_version, environment=settings.app_env)
        settings.validate_startup_credentials()
        
        # Initialize Persistent Memory Engine SQLite Database
        init_memory_db()

        # Phase V6.6: Discover and load dynamic extensions
        plugin_registry.discover_and_load()

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
            "files_count": len(latest_orchestrator_state.get("generated_files", {})),
            "lint_results": latest_orchestrator_state.get("lint_results", {}),
            "type_check_results": latest_orchestrator_state.get("type_check_results", {}),
            "test_results": latest_orchestrator_state.get("test_results", {})
        }
    return {"status": "idle", "message": "No pipeline runs executed yet."}


# --- Phase V6.1: Interactive Sandbox Execution Endpoints ---

@app.post("/api/execution/run")
async def api_execution_run(payload: dict):
    """Executes an arbitrary shell command safely inside the workspace_sandbox directory."""
    command = payload.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="Command field is required")
    timeout = payload.get("timeout", 15)
    
    code, stdout, stderr = await run_sandbox_command(command, timeout_seconds=timeout)
    return {
        "command": command,
        "exit_code": code,
        "stdout": stdout,
        "stderr": stderr
    }


@app.get("/api/execution/test-report")
async def api_execution_test_report():
    """Returns the latest automated verification, linting, and unit testing report."""
    if latest_orchestrator_state:
        return {
            "lint": latest_orchestrator_state.get("lint_results", {}),
            "type_check": latest_orchestrator_state.get("type_check_results", {}),
            "pytest": latest_orchestrator_state.get("test_results", {})
        }
    return {"status": "idle", "message": "No test reports available yet."}


# --- Phase V6.2: Reflection & Self-Repair Endpoint ---

@app.get("/api/execution/reflection")
async def api_execution_reflection():
    """Returns the reflection audit log and multi-round self-repair history."""
    if latest_orchestrator_state:
        return {
            "repair_attempts": latest_orchestrator_state.get("repair_attempts", 0),
            "is_repaired": latest_orchestrator_state.get("is_repaired", False),
            "repair_history": latest_orchestrator_state.get("repair_history", []),
            "final_lint_passed": latest_orchestrator_state.get("lint_results", {}).get("passed", False),
            "final_test_passed": latest_orchestrator_state.get("test_results", {}).get("passed", False)
        }
    return {"status": "idle", "message": "No reflection history available."}


# --- Phase V6.3: Human-in-the-Loop Approval Endpoints ---

@app.post("/api/execution/approve")
async def api_execution_approve(payload: dict = None):
    """Resumes a paused pipeline execution following human approval."""
    global current_approval_event, latest_orchestrator_state
    if current_approval_event and latest_orchestrator_state:
        notes = payload.get("notes", "Approved by user") if payload else "Approved by user"
        latest_orchestrator_state["approval_status"] = "APPROVED"
        latest_orchestrator_state["human_notes"] = notes
        current_approval_event.set()
        log_event("hitl_approval_received", action="approved", notes=notes)
        return {"status": "success", "action": "approved"}
    raise HTTPException(status_code=400, detail="No pipeline currently waiting for approval.")


@app.post("/api/execution/reject")
async def api_execution_reject(payload: dict = None):
    """Halts a paused pipeline execution following human rejection."""
    global current_approval_event, latest_orchestrator_state
    if current_approval_event and latest_orchestrator_state:
        notes = payload.get("notes", "Rejected by user") if payload else "Rejected by user"
        latest_orchestrator_state["approval_status"] = "REJECTED"
        latest_orchestrator_state["human_notes"] = notes
        current_approval_event.set()
        log_event("hitl_approval_received", action="rejected", notes=notes)
        return {"status": "success", "action": "rejected"}
    raise HTTPException(status_code=400, detail="No pipeline currently waiting for approval.")


# --- Phase V6.5: Persistent Memory Endpoints ---

@app.get("/api/memory/history")
async def api_memory_history():
    """Returns persistent session history and self-repair solution patterns across runs."""
    return get_memory_history()


# --- Phase V6.6: Plugin Ecosystem Endpoints ---

@app.get("/api/plugins")
async def api_plugins():
    """Returns active plugins and extension hooks loaded in the orchestrator."""
    return {"plugins": plugin_registry.get_loaded_plugins()}


# --- Phase V7.1: Multi-Repository Intelligence API Endpoints ---

@app.get("/api/workspace/projects")
async def api_workspace_projects():
    """Returns a list of all detected sub-projects/repositories in the workspace."""
    return {"projects": discover_workspace_projects()}


@app.get("/api/workspace/cross-graph")
async def api_workspace_cross_graph():
    """Returns the cross-repository dependency topology graph."""
    return build_cross_repo_dependency_map()


# --- Phase V7.2: Cloud Sandbox & Kubernetes API Endpoint ---

@app.post("/api/k8s/execute")
async def api_k8s_execute(payload: dict):
    """Executes a command inside an ephemeral Kubernetes Cloud Sandbox container."""
    command = payload.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="Command required")
    
    exit_code, stdout, stderr = await k8s_runner.run_ephemeral_job(command)
    return {
        "k8s_available": k8s_runner.initialized,
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr
    }


# --- WebSocket Orchestration Route ---

@app.websocket("/ws/orchestrate")
async def websocket_orchestrate(websocket: WebSocket):
    conn_id = set_request_id()
    await manager.connect(conn_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Check for WebSocket-based approval responses
            action = data.get("action")
            if action in ["approve", "reject"]:
                global current_approval_event, latest_orchestrator_state
                if current_approval_event and latest_orchestrator_state:
                    latest_orchestrator_state["approval_status"] = "APPROVED" if action == "approve" else "REJECTED"
                    latest_orchestrator_state["human_notes"] = data.get("notes", f"{action.capitalize()}d via WebSocket")
                    current_approval_event.set()
                continue

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

# --- Phase V7.3: CI/CD Pipeline Automation & Deployment Endpoints ---

@app.post("/api/cicd/generate")
async def api_cicd_generate(payload: dict = None):
    """Scaffolds native CI/CD workflow pipelines for workspace projects."""
    provider = payload.get("provider", "github") if payload else "github"
    return scaffold_cicd_pipelines(provider=provider)


@app.post("/api/cicd/deploy-verify")
async def api_cicd_deploy_verify(payload: dict):
    """Triggers automated post-deployment smoke tests and rollback recommendations."""
    target_url = payload.get("target_url")
    if not target_url:
        raise HTTPException(status_code=400, detail="target_url is required")
    
    result = await verify_deployment_health(target_url)
    return result

    # --- Phase V7.4: Enterprise Knowledge Graph API Endpoints ---

@app.get("/api/knowledge/graph")
async def api_knowledge_graph():
    """Returns the synthesized Enterprise Knowledge Graph (Nodes & Edges)."""
    return build_enterprise_knowledge_graph()


@app.get("/api/knowledge/impact")
async def api_knowledge_impact(target: str):
    """Computes the blast radius impact analysis for a given target symbol or file path."""
    if not target:
        raise HTTPException(status_code=400, detail="target parameter is required")
    return analyze_impact_radius(target)

# --- Phase V7.5: AI Project Manager API Endpoints ---

@app.post("/api/pm/decompose")
async def api_pm_decompose(payload: dict):
    """Decomposes a requirement into a structured multi-phase project milestone plan."""
    requirement = payload.get("requirement")
    if not requirement:
        raise HTTPException(status_code=400, detail="requirement string is required")
    return decompose_requirement_into_milestones(requirement)


@app.get("/api/pm/milestones")
async def api_pm_milestones():
    """Returns the current project roadmap and milestone breakdown."""
    return get_current_roadmap()
# --- Phase V7.6: Security & Compliance API Endpoints ---

@app.post("/api/security/scan")
async def api_security_scan():
    """Executes SAST and secret scanning on the workspace sandbox."""
    return scan_workspace_security()


@app.get("/api/security/compliance")
async def api_security_compliance():
    """Generates SOC2 / ISO27001 compliance audit readiness report."""
    return generate_compliance_report()

# --- Phase V7.7: Deployment Intelligence API Endpoints ---

@app.get("/api/deploy/targets")
async def api_deploy_targets():
    """Returns active deployment targets, health statuses, and traffic weights."""
    return get_deployment_targets()


@app.post("/api/deploy/canary")
async def api_deploy_canary(payload: dict):
    """Configures canary deployment traffic weight distribution."""
    target = payload.get("target", "production-green")
    weight = payload.get("weight", 10)
    return configure_canary_release(canary_target=target, weight=weight)

# --- Phase V7.8: IDE Integrations API Endpoints ---

@app.post("/api/ide/completion")
async def api_ide_completion(payload: dict):
    """Provides inline code completions for IDE extensions (VS Code / JetBrains)."""
    file_path = payload.get("file_path", "main.py")
    line_number = payload.get("line_number", 1)
    prefix_code = payload.get("prefix_code", "")
    return generate_inline_completion(file_path, line_number, prefix_code)


@app.get("/api/ide/diagnostics")
async def api_ide_diagnostics():
    """Streams active LSP-compatible workspace diagnostics to connected IDE clients."""
    return get_ide_diagnostics()

# --- Phase V7.9: Team Collaboration API Endpoints ---

@app.get("/api/team/presence")
async def api_team_presence():
    """Returns real-time workspace team presence, active sessions, and thread counts."""
    return get_team_presence()


@app.post("/api/team/comment")
async def api_team_comment(payload: dict):
    """Attaches an inline comment thread to a workspace file location."""
    author = payload.get("author", "Anonymous")
    file_path = payload.get("file_path", "server.py")
    line = payload.get("line", 1)
    comment = payload.get("comment", "")
    
    if not comment:
        raise HTTPException(status_code=400, detail="comment text is required")
        
    return add_inline_comment(author=author, file_path=file_path, line=line, comment=comment)
    
# --- Phase V7.10: Platform Analytics API Endpoint ---

@app.get("/api/analytics/dashboard")
async def api_analytics_dashboard():
    """Returns platform-wide telemetry, token consumption, and execution analytics."""
    return generate_platform_analytics()