"""
Neural Glass AI Orchestrator — LLM Call Retry & Telemetry Decorator
"""

import time
import functools
from core.config import settings
from core.logger import log_event
from core.metrics import metrics


def _classify_retryable(exc: Exception):
    """Best-effort transient/permanent classification without inventing SDK APIs.

    Returns (is_retryable, reason). Transient: 429/500/502/503/504, timeouts,
    connection/network errors. Permanent: most 4xx client errors (except 408/429).
    Unknown errors default to retryable to preserve prior behavior.
    """
    # HTTP status on common SDK/http exceptions
    status = None
    for attr in ("status_code", "code"):
        try:
            v = getattr(exc, attr, None)
            if isinstance(v, int):
                status = v
                break
            if isinstance(v, str) and v.isdigit():
                status = int(v)
                break
        except Exception:
            pass
    try:
        resp = getattr(exc, "response", None)
        if resp is not None and status is None:
            sc = getattr(resp, "status_code", None)
            if isinstance(sc, int):
                status = sc
    except Exception:
        pass

    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    text = f"{name} {msg}"

    if status is not None:
        if status in (408, 429, 500, 502, 503, 504):
            return True, f"http_{status}"
        if 400 <= status < 500:
            return False, f"http_{status}_permanent"
        if 500 <= status < 600:
            return True, f"http_{status}"

    transient_markers = (
        "timeout", "timed out", "deadline", "unavailable", "503",
        "temporar", "overload", "high demand", "rate limit", "429",
        "connection", "connect", "network", "reset", "refused",
        "dns", "ssl", "eof", "remoteprotocol", "readerror",
        "writeerror", "server disconnected",
    )
    permanent_markers = (
        "invalid api key", "api key not valid", "permission denied",
        "unauthenticated", "unauthorized", "forbidden", "not found",
        "invalid argument", "failed_precondition",
    )
    if any(m in text for m in permanent_markers) and status not in (408, 429):
        return False, "permanent_client_error"
    if any(m in text for m in transient_markers):
        return True, "transient_error"
    return True, "unknown_default_retryable"


def create_llm_retry_decorator(provider_name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            delay = settings.retry_delay_seconds
            start_time = time.perf_counter()
            max_attempts = max(1, int(settings.max_api_retries))

            while attempts < max_attempts:
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    metrics.record_llm_usage(provider=provider_name, duration_seconds=elapsed)
                    if attempts > 0:
                        log_event(
                            f"{provider_name}_api_retry_success",
                            attempts=attempts + 1,
                            elapsed_seconds=round(elapsed, 3),
                        )
                    return result
                except Exception as e:
                    attempts += 1
                    elapsed = time.perf_counter() - start_time
                    metrics.record_retry()
                    retryable, reason = _classify_retryable(e)
                    err_text = str(e) or type(e).__name__
                    has_more = attempts < max_attempts and retryable
                    log_event(
                        f"{provider_name}_api_retry",
                        level="warning" if has_more else "error",
                        attempt=attempts,
                        max_attempts=max_attempts,
                        retryable=retryable,
                        reason=reason,
                        elapsed_seconds=round(elapsed, 3),
                        error=err_text,
                        error_type=type(e).__name__,
                        next_action=(
                            f"backoff_{round(delay, 3)}s" if has_more else "exhausted"
                        ),
                    )
                    if not retryable or attempts >= max_attempts:
                        metrics.record_llm_usage(provider=provider_name, duration_seconds=elapsed)
                        raise e
                    time.sleep(delay)
                    delay *= settings.retry_exponential_multiplier
        return wrapper
    return decorator
