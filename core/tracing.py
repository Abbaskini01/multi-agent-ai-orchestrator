"""
Neural Glass AI Orchestrator — Contextvar-Based Request Tracing
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# Thread and async-safe context variable for Request ID propagation
_REQUEST_ID_CTX_VAR: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    """Generates a unique 12-character hexadecimal request identifier."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_request_id() -> str:
    """Retrieves current request ID from context, or returns a fallback default."""
    return _REQUEST_ID_CTX_VAR.get() or "req_system_internal"


def set_request_id(request_id: Optional[str] = None) -> str:
    """Sets the active request ID in context. Generates one if not provided."""
    req_id = request_id or generate_request_id()
    _REQUEST_ID_CTX_VAR.set(req_id)
    return req_id


def reset_request_id() -> None:
    """Resets the context variable to default."""
    _REQUEST_ID_CTX_VAR.set(None)