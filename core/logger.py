"""
Neural Glass AI Orchestrator — Context-Aware Structured Logging
"""

import sys
import json
import logging
from datetime import datetime, timezone
from core.config import settings
from core.tracing import get_request_id


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": get_request_id(),
            "message": record.getMessage(),
            "environment": settings.app_env,
        }
        if hasattr(record, "event_data") and isinstance(record.event_data, dict):
            log_payload.update(record.event_data)

        return json.dumps(log_payload)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("neural_glass")
    logger.setLevel(settings.log_level.upper())
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logger()


def log_event(event_name: str, level: str = "info", **kwargs):
    extra = {"event_data": {"event": event_name, **kwargs}}
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{event_name}]", extra=extra)