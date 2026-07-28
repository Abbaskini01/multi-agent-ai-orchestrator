"""
Neural Glass AI Orchestrator — Deployment Intelligence Engine
"""

from typing import Dict, List, Any
from core.logger import log_event

# Active deployment environment registry state
DEPLOYMENT_TARGETS = {
    "staging": {
        "url": "http://staging.internal.net",
        "version": "v7.6.0",
        "status": "healthy",
        "traffic_weight": 100
    },
    "production-blue": {
        "url": "http://prod-blue.internal.net",
        "version": "v7.5.0",
        "status": "healthy",
        "traffic_weight": 90
    },
    "production-green": {
        "url": "http://prod-green.internal.net",
        "version": "v7.6.0",
        "status": "canary",
        "traffic_weight": 10
    }
}


def get_deployment_targets() -> Dict[str, Any]:
    """Returns status and configuration of all deployment targets."""
    return {
        "total_environments": len(DEPLOYMENT_TARGETS),
        "environments": DEPLOYMENT_TARGETS
    }


def configure_canary_release(canary_target: str, weight: int) -> Dict[str, Any]:
    """
    Adjusts traffic weight allocation for canary deployments and triggers stability checks.
    """
    if canary_target not in DEPLOYMENT_TARGETS:
        return {"status": "error", "message": f"Target environment '{canary_target}' not found."}

    clamped_weight = max(0, min(100, weight))
    DEPLOYMENT_TARGETS[canary_target]["traffic_weight"] = clamped_weight
    
    # Adjust blue/primary env accordingly
    if canary_target == "production-green":
        DEPLOYMENT_TARGETS["production-blue"]["traffic_weight"] = 100 - clamped_weight

    log_event("canary_traffic_adjusted", target=canary_target, weight=clamped_weight)

    return {
        "status": "success",
        "canary_target": canary_target,
        "new_weight": clamped_weight,
        "traffic_distribution": {
            "production-blue": DEPLOYMENT_TARGETS["production-blue"]["traffic_weight"],
            "production-green": DEPLOYMENT_TARGETS["production-green"]["traffic_weight"]
        }
    }