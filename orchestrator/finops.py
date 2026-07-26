"""
Neural Glass AI Orchestrator — FinOps Token & Cost Tracker
"""

import time
from typing import Dict, Any


class FinOpsTracker:

    PROMPT_COST_PER_1K = 0.00015
    COMPLETION_COST_PER_1K = 0.00060

    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    def calculate_step(self, prompt_add: int, completion_add: int, start_time: float, model: str) -> Dict[str, Any]:
        self.total_prompt_tokens += prompt_add
        self.total_completion_tokens += completion_add

        step_cost = ((prompt_add / 1000) * self.PROMPT_COST_PER_1K) + ((completion_add / 1000) * self.COMPLETION_COST_PER_1K)
        self.total_cost_usd += step_cost
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "prompt_tokens": prompt_add,
            "completion_tokens": completion_add,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "step_cost_usd": round(step_cost, 6),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "latency_ms": latency_ms,
            "model_route": model
        }