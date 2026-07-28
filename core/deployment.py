"""
Neural Glass AI Orchestrator — Deployment Health & Verification Engine
"""

import httpx
from typing import Dict, Any
from core.logger import log_event


async def verify_deployment_health(target_url: str) -> Dict[str, Any]:
    """
    Executes automated smoke testing against deployed endpoints.
    If 5xx errors or connection failures occur, triggers an automated rollback recommendation.
    """
    log_event("smoke_test_started", target_url=target_url)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(target_url)
            
            status_code = response.status_code
            latency_ms = response.elapsed.total_seconds() * 1000

            passed = (200 <= status_code < 400)
            
            log_event(
                "smoke_test_completed",
                status_code=status_code,
                latency_ms=round(latency_ms, 2),
                passed=passed
            )

            return {
                "target_url": target_url,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "healthy": passed,
                "action": "maintain" if passed else "trigger_rollback",
                "notes": "Deployment healthy" if passed else f"Target returned status code {status_code}"
            }

    except Exception as e:
        log_event("smoke_test_failed", error=str(e), level="error")
        return {
            "target_url": target_url,
            "status_code": 0,
            "latency_ms": 0,
            "healthy": False,
            "action": "trigger_rollback",
            "notes": f"Connection/Network error during smoke test: {str(e)}"
        }