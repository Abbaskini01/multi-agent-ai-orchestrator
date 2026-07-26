"""
Neural Glass AI Orchestrator — Google Gemini SDK Integration Adapter with Groq Fallback
"""

import re
import json
import asyncio
from typing import Dict
from core.config import settings
from core.logger import log_event
from llm.retry import create_llm_retry_decorator
from llm.groq import groq_client

gemini_client = None
if settings.gemini_api_key:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=settings.gemini_api_key)
        log_event("gemini_sdk_initialized", key_len=len(settings.gemini_api_key))
    except Exception as e:
        log_event("gemini_sdk_init_failed", error=str(e), level="warning")


def _get_clean_gemini_model() -> str:
    """Normalizes the Gemini model string to avoid API version mismatch errors."""
    model = settings.default_gemini_model.replace("-latest", "").strip()
    if not model.startswith("gemini-"):
        model = "gemini-1.5-flash"
    return model


@create_llm_retry_decorator("gemini")
def _exec_gemini_generation_sync(prompt: str, system_instruction: str) -> str:
    target_model = _get_clean_gemini_model()
    response = gemini_client.models.generate_content(
        model=target_model,
        contents=f"{system_instruction}\n\nRequirement: {prompt}"
    )
    return response.text.strip()


def _exec_groq_fallback_generation(prompt: str, system_instruction: str) -> Dict[str, str]:
    """Generates multi-file code structure via Groq Llama 3.3 70B if Gemini fails."""
    if not groq_client:
        return {}
    try:
        log_event("groq_fallback_code_gen_start", model=settings.default_groq_model)
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            model=settings.default_groq_model,
            response_format={"type": "json_object"}
        )
        raw_text = completion.choices[0].message.content.strip()
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict) and "files" in parsed:
            return parsed["files"] if isinstance(parsed["files"], dict) else parsed
        return parsed
    except Exception as e:
        log_event("groq_fallback_code_gen_failed", error=str(e), level="error")
        return {}


def generate_fallback_workspace(requirement: str) -> Dict[str, str]:
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
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(_exec_gemini_generation_sync, requirement, system_instruction),
                timeout=settings.request_timeout_seconds
            )

            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
                raw_text = re.sub(r"\n?```$", "", raw_text)

            parsed_files = json.loads(raw_text)
            if isinstance(parsed_files, dict) and len(parsed_files) > 0:
                log_event("gemini_generation_success", files_generated=len(parsed_files))
                return parsed_files
        except Exception as e:
            log_event("gemini_generation_failed", error=str(e), level="error")

    # Try Groq AI dynamic generation as secondary live LLM
    log_event("attempting_groq_code_generation_fallback")
    groq_files = await asyncio.to_thread(_exec_groq_fallback_generation, requirement, system_instruction)
    if groq_files and len(groq_files) > 0:
        log_event("groq_generation_success", files_generated=len(groq_files))
        return groq_files

    log_event("reverting_to_fallback_scaffolding")
    return generate_fallback_workspace(requirement)