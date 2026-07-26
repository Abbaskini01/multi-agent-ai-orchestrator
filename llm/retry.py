"""
Neural Glass AI Orchestrator — LLM Call Retry & Telemetry Decorator
"""

import time
import functools
from core.config import settings
from core.logger import log_event
from core.metrics import metrics


def create_llm_retry_decorator(provider_name: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            delay = settings.retry_delay_seconds
            start_time = time.perf_counter()

            while attempts < settings.max_api_retries:
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    metrics.record_llm_usage(provider=provider_name, duration_seconds=elapsed)
                    return result
                except Exception as e:
                    attempts += 1
                    metrics.record_retry()
                    log_event(
                        f"{provider_name}_api_retry",
                        level="warning",
                        attempt=attempts,
                        error=str(e),
                        next_action="initiating_backoff" if attempts < settings.max_api_retries else "exhausted"
                    )
                    if attempts >= settings.max_api_retries:
                        elapsed = time.perf_counter() - start_time
                        metrics.record_llm_usage(provider=provider_name, duration_seconds=elapsed)
                        raise e
                    time.sleep(delay)
                    delay *= settings.retry_exponential_multiplier
        return wrapper
    return decorator