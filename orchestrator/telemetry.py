"""
Neural Glass AI Orchestrator — Pipeline Telemetry Emitter
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
from websocket.manager import telemetry_mgr


async def emit_pipeline_telemetry(
    websocket: WebSocket,
    event_type: str,
    data: Dict[str, Any],
    concept_title: str,
    concept_explanation: str,
    finops_data: Optional[Dict[str, Any]] = None
):
    """Encapsulates telemetry payload formatting for graph node events."""
    concept = {"title": concept_title, "explanation": concept_explanation}
    await telemetry_mgr.emit_event(
        websocket,
        event_type=event_type,
        data=data,
        concept=concept,
        finops=finops_data
    )