"""
Neural Glass AI Orchestrator — Operational Probes & Health Diagnostics
"""

import shutil
import sqlite3
import time
from typing import Dict, Any
from fastapi import APIRouter
import psutil

from core.config import settings
from core.metrics import metrics
from websocket.manager import manager

health_router = APIRouter(tags=["Health & Operational Probes"])


def _check_workspace_writable() -> bool:
    try:
        settings.workspace_dir.mkdir(parents=True, exist_ok=True)
        test_file = settings.workspace_dir / ".probe_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True
    except Exception:
        return False


def _check_sqlite_connection() -> bool:
    try:
        db_path = settings.workspace_dir / settings.sqlite_db_name
        conn = sqlite3.connect(str(db_path), timeout=2.0)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        conn.close()
        return True
    except Exception:
        return False


def _check_docker_available() -> bool:
    if not settings.docker_enabled:
        return False
    return shutil.which("docker") is not None


def livez_probe() -> Dict[str, Any]:
    """Liveness probe: verifies application process is active."""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "app_name": settings.app_name,
        "version": settings.app_version
    }


def readyz_probe() -> Dict[str, Any]:
    """Readiness probe: checks backend dependencies and workspace access."""
    workspace_ok = _check_workspace_writable()
    sqlite_ok = _check_sqlite_connection()
    is_ready = workspace_ok and sqlite_ok

    return {
        "status": "ready" if is_ready else "unready",
        "timestamp": time.time(),
        "checks": {
            "workspace_writable": workspace_ok,
            "sqlite_db_healthy": sqlite_ok,
            "gemini_configured": bool(settings.gemini_api_key),
            "groq_configured": bool(settings.groq_api_key),
            "docker_available": _check_docker_available(),
            "github_configured": bool(settings.github_token),
            "active_websockets": len(manager.active_connections)
        }
    }


def healthz_probe() -> Dict[str, Any]:
    """Health status probe: returns system resource stats and operational metrics."""
    disk = shutil.disk_usage(str(settings.workspace_dir.parent))
    mem = psutil.virtual_memory()

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
        "system_metrics": {
            "disk_total_bytes": disk.total,
            "disk_free_bytes": disk.free,
            "disk_used_percent": round((disk.used / disk.total) * 100, 2),
            "ram_total_mb": round(mem.total / (1024 * 1024), 2),
            "ram_available_mb": round(mem.available / (1024 * 1024), 2),
            "ram_used_percent": mem.percent
        },
        "llm_providers": {
            "gemini_active": bool(settings.gemini_api_key),
            "groq_active": bool(settings.groq_api_key)
        },
        "operational_telemetry": metrics.get_summary()
    }


# Router Endpoints for FastAPI inclusion
@health_router.get("/livez")
async def liveness_endpoint():
    return livez_probe()


@health_router.get("/readyz")
async def readiness_endpoint():
    return readyz_probe()


@health_router.get("/healthz")
async def health_endpoint():
    return healthz_probe()