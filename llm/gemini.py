"""
Neural Glass AI Orchestrator — Google Gemini SDK Integration Adapter
===================================================================

The Google GenAI SDK is synchronous, while the orchestrator is asyncio-based.
Async callers delegate synchronous Gemini SDK operations through
`asyncio.to_thread(...)` so the event loop remains responsive.

Timeout and retry behavior:
  * Per-attempt HTTP timeout is bounded by the shared Gemini client
    `HttpOptions(timeout=...)` configuration (milliseconds, derived from
    `settings.request_timeout_seconds`).
  * Retry behavior is controlled by the existing `create_llm_retry_decorator`
    implementation in `llm.retry` (bounded attempts/backoff, transient vs.
    permanent classification, observability). SDK-level retries are not enabled
    to avoid overlapping/duplicate retry behavior.
  * Worker threads cannot be forcibly cancelled by cancelling the awaiting
    coroutine. Callers therefore avoid wrapping retrying worker operations in an
    outer `asyncio.wait_for(...)` that could leave orphaned retry work running;
    bounded SDK timeouts and bounded retries provide the execution limit.

Two public entry points are used by the pipeline:
  * call_gemini_intent    -> one-sentence architectural intent
  * call_gemini_generator -> JSON object of {relative path: file contents}

If no API key is configured, or if generation fails, the module degrades to a
deterministic local scaffold so the rest of the pipeline can still run.
"""

import re
import json
import asyncio
from typing import Dict
from core.config import settings
from core.logger import log_event
from llm.retry import create_llm_retry_decorator

gemini_client = None
if settings.gemini_api_key:
    try:
        from google import genai
        from google.genai import types
        timeout_ms = int(max(1.0, settings.request_timeout_seconds) * 1000)
        gemini_client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )
        log_event("gemini_sdk_initialized", key_len=len(settings.gemini_api_key), http_timeout_ms=timeout_ms)
    except Exception as e:
        log_event("gemini_sdk_init_failed", error=str(e) or type(e).__name__, level="warning")


def _get_clean_gemini_model() -> str:
    """Respect the configured Gemini model without rewriting its ID."""
    return settings.default_gemini_model


@create_llm_retry_decorator("gemini")
def _exec_gemini_generation_sync(prompt: str, system_instruction: str) -> str:
    """Blocking generate_content call, executed in a worker thread."""
    target_model = _get_clean_gemini_model()
    response = gemini_client.models.generate_content(
        model=target_model,
        contents=f"{system_instruction}\n\nRequirement: {prompt}"
    )
    return (response.text or "").strip()


@create_llm_retry_decorator("gemini")
def _exec_gemini_intent_sync(prompt: str) -> str:
    """Blocking intent-summary call, executed in a worker thread."""
    response = gemini_client.models.generate_content(
        model=settings.default_gemini_model,
        contents=prompt,
        config={"system_instruction": "You are a software architect assistant. Summarize the technical user requirement into a concise 1-sentence architectural intent."}
    )
    return (response.text or "").strip()


async def call_gemini_intent(prompt: str) -> str:
    """Summarise the requirement into one architectural sentence.

    Never raises: on a missing client or a failed call it returns the raw
    prompt so the pipeline keeps its forward path.

    The sync SDK call (with retry/backoff) runs in a worker thread. Per-attempt
    HTTP timeout is bounded by the client HttpOptions; retries are bounded by
    settings.max_api_retries. We do NOT wrap this in asyncio.wait_for because
    wait_for cannot cancel the underlying worker thread and can leave
    orphaned/overlapping retry work running.
    """
    if not gemini_client:
        log_event("gemini_client_unconfigured", level="warning")
        return f"Parsed Intent: {prompt}"
    try:
        res = await asyncio.to_thread(_exec_gemini_intent_sync, prompt)
        log_event("gemini_intent_success", intent=res)
        return res
    except Exception as e:
        err = str(e) or type(e).__name__
        log_event("gemini_intent_failed", error=err, error_type=type(e).__name__, level="error")
        return prompt


def _exec_groq_fallback_generation(prompt: str, system_instruction: str) -> Dict[str, str]:
    """Legacy compatibility only; cross-provider fallback is disabled."""
    return {}


def generate_fallback_workspace(requirement: str) -> Dict[str, str]:
    """Deterministic scaffold used when the model is unavailable.

    Keyword matching picks between a FastAPI-style layout and a small CLI
    layout. This is a degradation path, not a second generation strategy.
    """
    req_lower = requirement.lower()
    if any(k in req_lower for k in ["url shortener", "api", "fastapi", "rest", "web service"]):
        return {
            "src/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'status': 'live'}\n",
            "src/database.py": "def init_db(): print('[OK] Database initialized')\n",
            "requirements.txt": "fastapi\nuvicorn\n",
            "README.md": f"# REST API for {requirement}\nRun: `python src/main.py`\n"
        }
    else:
        return {
            "src/main.py": f"def main():\n    print('[OK] Running app for: {requirement}')\n\nif __name__ == '__main__':\n    main()\n",
            "src/utils.py": "def helper(): return True\n",
            "tests/test_app.py": "import unittest\nclass TestApp(unittest.TestCase):\n    def test_run(self): self.assertTrue(True)\n",
            "requirements.txt": "pydantic\n",
            "README.md": f"# App: {requirement}\nRun entrypoint: `python src/main.py`\n"
        }


async def call_gemini_generator(requirement: str) -> Dict[str, str]:
    """Generate a whole multi-file project as {path: source}.

    The model is asked for raw JSON; stray markdown fences are stripped before
    json.loads. An empty or non-dict result falls back to the local scaffold,
    so callers can rely on receiving at least one file.

    The sync SDK call (with retry/backoff) runs in a worker thread. Per-attempt
    HTTP timeout is bounded by the client HttpOptions; retries are bounded by
    settings.max_api_retries. We do NOT wrap this in asyncio.wait_for because
    wait_for cannot cancel the underlying worker thread and can leave
    orphaned/overlapping retry work running.
    """
    system_instruction = (
        "You are a Principal Software Engineer. The user wants to build a software tool. "
        "Return a valid JSON object where keys are relative file paths (e.g. 'src/main.py', 'src/utils.py', 'requirements.txt', 'README.md') "
        "and values are the string source contents of those files. "
        "Do NOT wrap the JSON in markdown triple backticks. Return ONLY raw JSON."
    )

    if gemini_client:
        try:
            target_model = _get_clean_gemini_model()
            log_event("gemini_request_start", model=target_model)
            raw_text = await asyncio.to_thread(
                _exec_gemini_generation_sync, requirement, system_instruction
            )

            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            parsed_files = json.loads(raw_text)
            if isinstance(parsed_files, dict) and len(parsed_files) > 0:
                log_event("gemini_generation_success", files_generated=len(parsed_files))
                return parsed_files
        except Exception as e:
            err = str(e) or type(e).__name__
            log_event(
                "gemini_generation_failed",
                error=err,
                error_type=type(e).__name__,
                level="error",
            )

    log_event("reverting_to_fallback_scaffolding")
    return generate_fallback_workspace(requirement)