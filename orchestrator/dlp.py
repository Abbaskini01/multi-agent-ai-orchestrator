"""
Neural Glass AI Orchestrator — Data Loss Prevention (DLP) Guardrails
"""

import re
from typing import Tuple, List
from core.config import settings

DLP_PATTERNS = {
    "OpenAI API Key": r"sk-(?:proj-)?[a-zA-Z0-9_-]{20,}",
    "Anthropic API Key": r"sk-ant-[a-zA-Z0-9_-]{32,}",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Generic Private Key": r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----",
    "Email Address": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
}


def sanitize_prompt_dlp(prompt: str) -> Tuple[str, List[str]]:
    """Scans user prompts and redacts enterprise secrets before sending to models."""
    if not settings.dlp_enabled:
        return prompt, []

    sanitized = prompt
    detected_types = []

    for secret_type, pattern in DLP_PATTERNS.items():
        matches = re.findall(pattern, sanitized)
        if matches:
            detected_types.append(secret_type)
            placeholder = f"[REDACTED_{secret_type.upper().replace(' ', '_')}]"
            sanitized = re.sub(pattern, placeholder, sanitized)

    return sanitized, detected_types