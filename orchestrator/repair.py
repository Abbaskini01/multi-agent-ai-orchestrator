"""
Neural Glass AI Orchestrator — Reflection & Self-Repair Engine with Persistent Memory Context
"""

import re
import asyncio
from typing import Dict, Any, List, Tuple
from orchestrator.state import OrchestratorState
from llm.groq import groq_client
from core.config import settings
from core.logger import log_event
from core.memory import get_relevant_repairs, save_repair_memory


def classify_error_trace(lint_out: str, type_out: str, test_out: str) -> Tuple[str, str, str]:
    """
    Parses verification outputs to identify (target_file, error_category, error_details).
    Evaluates Lint -> Type Check -> Unit Tests in order of priority.
    """
    # 1. Check Flake8 / Syntax Errors
    if lint_out and ("F" in lint_out or "E" in lint_out or "W" in lint_out) and "No lint issues found" not in lint_out:
        match = re.search(r"(\.[\\/][^:]+|[^:\s]+\.py):(\d+):(\d+):\s*(.*)", lint_out)
        if match:
            file_path = match.group(1).replace(".\\", "").replace("./", "").replace("\\", "/")
            return file_path, "LINT_OR_SYNTAX", match.group(0)

    # 2. Check Mypy Type Errors
    if type_out and "error:" in type_out:
        match = re.search(r"([^:\s]+\.py):(\d+):\s*error:\s*(.*)", type_out)
        if match:
            file_path = match.group(1).replace("\\", "/")
            return file_path, "TYPE_ERROR", match.group(0)
        return "src/main.py", "TYPE_ERROR", type_out[:1000]

    # 3. Check Pytest Failures / Stack Traces
    if test_out and ("FAILED" in test_out or "ERROR" in test_out or "error" in test_out.lower()):
        file_match = re.search(r"FAILED\s+([^:]+\.py)", test_out)
        file_path = file_match.group(1).replace("\\", "/") if file_match else "src/main.py"
        return file_path, "TEST_FAILURE", test_out[:1000]

    return "", "NONE", ""


async def run_repair_agent(
    state: OrchestratorState,
    target_file: str,
    error_category: str,
    error_details: str
) -> Dict[str, str]:
    """
    Generates a fixed version of the target failing file using LLM context and persistent repair memory.
    """
    generated_files = state.get("generated_files", {})
    original_code = generated_files.get(target_file, "")
    
    # Query Persistent Memory for past repairs in this error category
    past_repairs = get_relevant_repairs(error_category, limit=2)
    memory_context = ""
    if past_repairs:
        memory_context = "\n\nHistorical Repair Context from Past Sessions:\n"
        for idx, repair in enumerate(past_repairs, 1):
            memory_context += f"Example {idx}: File {repair['file_name']} failed with '{repair['error_details']}' -> Fixed using solution: {repair['solution_summary']}\n"

    prompt = (
        f"You are a Senior Software Engineer repairing a broken file in a Python codebase.\n\n"
        f"File Name: {target_file}\n"
        f"Error Category: {error_category}\n"
        f"Error Stack Trace / Warning:\n{error_details}"
        f"{memory_context}\n\n"
        f"Original Source Code:\n```python\n{original_code}\n```\n\n"
        f"Task: Fix the error in the source code. Follow PEP8 style guidelines strictly "
        f"(remove unused imports, ensure proper indentation, and leave 2 blank lines before top-level functions/classes). "
        f"Return ONLY the complete, corrected Python code without any markdown explanation or wrapping blocks."
    )

    fixed_code = original_code
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=settings.default_groq_model,
                temperature=0.2,
                max_tokens=2500
            )
            raw = completion.choices[0].message.content.strip()
            
            # Clean possible markdown block formatting
            if raw.startswith("```python"):
                raw = raw.replace("```python", "", 1)
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            elif raw.startswith("```"):
                raw = raw.replace("```", "", 1)
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            
            if raw:
                fixed_code = raw
                # Save successful repair pattern to Persistent Memory
                save_repair_memory(
                    file_name=target_file,
                    category=error_category,
                    details=error_details,
                    solution=f"Fixed {error_category} issue in {target_file}"
                )
        except Exception as e:
            log_event("repair_agent_failed", error=str(e), level="error")

    log_event("repair_code_generated", file=target_file, category=error_category)
    return {target_file: fixed_code}