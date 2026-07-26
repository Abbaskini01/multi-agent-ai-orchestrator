"""
Neural Glass AI Orchestrator — Thread-Safe Operational Metrics Collector
"""

import time
import threading
from typing import Dict, Any


class MetricsCollector:
    """In-memory thread-safe metrics storage for operational monitoring."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_requests = 0
        self._active_ws_connections = 0
        self._pipeline_runs = 0
        self._pipeline_errors = 0
        self._total_pipeline_duration_seconds = 0.0
        self._retry_counts = 0
        self._llm_calls = 0
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._llm_latencies: Dict[str, float] = {}

    def increment_requests(self) -> None:
        with self._lock:
            self._total_requests += 1

    def set_active_ws_connections(self, count: int) -> None:
        with self._lock:
            self._active_ws_connections = max(0, count)

    def record_pipeline_run(self, duration_seconds: float, success: bool = True) -> None:
        with self._lock:
            self._pipeline_runs += 1
            self._total_pipeline_duration_seconds += duration_seconds
            if not success:
                self._pipeline_errors += 1

    def record_retry(self) -> None:
        with self._lock:
            self._retry_counts += 1

    def record_llm_usage(self, provider: str, duration_seconds: float, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        with self._lock:
            self._llm_calls += 1
            self._total_prompt_tokens += prompt_tokens
            self._total_completion_tokens += completion_tokens
            prev_total = self._llm_latencies.get(provider, 0.0)
            self._llm_latencies[provider] = prev_total + duration_seconds

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            avg_pipeline_duration = (
                self._total_pipeline_duration_seconds / self._pipeline_runs
                if self._pipeline_runs > 0 else 0.0
            )
            return {
                "total_http_requests": self._total_requests,
                "active_ws_connections": self._active_ws_connections,
                "pipeline_execution": {
                    "total_runs": self._pipeline_runs,
                    "errors": self._pipeline_errors,
                    "avg_duration_seconds": round(avg_pipeline_duration, 4),
                },
                "llm_telemetry": {
                    "total_calls": self._llm_calls,
                    "total_retries": self._retry_counts,
                    "prompt_tokens": self._total_prompt_tokens,
                    "completion_tokens": self._total_completion_tokens,
                    "cumulative_latencies_seconds": {
                        k: round(v, 4) for k, v in self._llm_latencies.items()
                    }
                }
            }


metrics = MetricsCollector()