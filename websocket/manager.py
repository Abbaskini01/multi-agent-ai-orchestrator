"""
Neural Glass AI Orchestrator — WebSocket Manager with Telemetry Emitter & Graceful Shutdown
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
from core.logger import log_event
from core.metrics import metrics


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        metrics.set_active_ws_connections(len(self.active_connections))
        log_event("ws_connection_accepted", active_count=len(self.active_connections), connection_id=connection_id)

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            metrics.set_active_ws_connections(len(self.active_connections))
            log_event("ws_connection_closed", active_count=len(self.active_connections), connection_id=connection_id)

    async def broadcast_json(self, data: Dict[str, Any]):
        disconnected = []
        for conn_id, connection in self.active_connections.items():
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(conn_id)

        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def emit_event(
        self, 
        websocket: WebSocket, 
        event_type: str, 
        data: Optional[Dict[str, Any]] = None,
        title: str = "", 
        description: str = "", 
        finops: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ):
        """Flexible telemetry emitter accepting 'data' payload kwarg from orchestrator/telemetry.py."""
        payload_data = data if data is not None else kwargs.get("payload", {})
        event_payload = {
            "type": event_type,
            "event": event_type,
            "data": payload_data,
            "title": title,
            "description": description,
            "finops": finops or {}
        }
        try:
            await websocket.send_json(event_payload)
        except Exception as e:
            log_event("ws_emit_error", error=str(e), level="warning")

    async def graceful_disconnect_all(self):
        """Sends close frames to all active sockets during application shutdown."""
        log_event("ws_graceful_shutdown_start", connection_count=len(self.active_connections))
        connections = list(self.active_connections.items())
        for conn_id, websocket in connections:
            try:
                await websocket.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
            self.disconnect(conn_id)
        log_event("ws_graceful_shutdown_complete")


manager = ConnectionManager()
telemetry_mgr = manager  # Backward compatibility alias