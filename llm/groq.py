"""
Neural Glass AI Orchestrator — Groq SDK Integration Adapter
"""

import asyncio
from core.config import settings
from core.logger import log_event
from llm.retry import create_llm_retry_decorator

groq_client = None
if settings.groq_api_key:
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.groq_api_key)
        log_event("groq_sdk_initialized", key_len=len(settings.groq_api_key))
    except Exception as e:
        log_event("groq_sdk_init_failed", error=str(e), level="warning")


@create_llm_retry_decorator("groq")
def _exec_groq_intent_sync(prompt: str) -> str:
    completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a software architect assistant. Summarize the technical user requirement into a concise 1-sentence architectural intent."},
            {"role": "user", "content": prompt}
        ],
        model=settings.default_groq_model
    )
    return completion.choices[0].message.content.strip()


async def call_groq_intent(prompt: str) -> str:
    if not groq_client:
        log_event("groq_client_unconfigured", level="warning")
        return f"Parsed Intent: {prompt}"

    try:
        res = await asyncio.wait_for(
            asyncio.to_thread(_exec_groq_intent_sync, prompt),
            timeout=settings.request_timeout_seconds
        )
        log_event("groq_intent_success", intent=res)
        return res
    except Exception as e:
        log_event("groq_intent_failed", error=str(e), level="error")
        return prompt