"""
Neural Glass AI Orchestrator — AI Commit Message Generator Agent
"""

import asyncio

from core.git import get_unified_diff, create_commit, init_sandbox_repo
from llm.gemini import gemini_client
from core.config import settings
from core.logger import log_event


def _generate_commit_msg_sync(prompt: str) -> str:
    """Blocking Gemini SDK call for commit message generation (runs in a worker thread)."""
    completion = gemini_client.models.generate_content(
        contents=prompt,
        model=settings.default_gemini_model,
    )
    return (completion.text or "").strip()


async def generate_ai_commit(requirement: str) -> str:
    """Generates a Conventional Commit message using LLM based on git diff analysis."""
    init_sandbox_repo()
    diff = get_unified_diff()

    if not diff:
        fallback_msg = f"feat: scaffold codebase for {requirement[:50]}"
        create_commit(fallback_msg)
        return fallback_msg

    prompt = (
        f"Generate a concise Conventional Commit message (e.g. feat: add SQLite storage module) "
        f"for this requirement: '{requirement}'.\n"
        f"Diff preview:\n{diff[:1500]}\n\n"
        f"Return ONLY the single commit message line. Do not use quotes or backticks."
    )

    commit_msg = ""
    if gemini_client:
        try:
            # SDK call is synchronous; run it off the event loop. Per-attempt HTTP
            # timeout is bounded by the shared Gemini client HttpOptions. No outer
            # asyncio.wait_for is used (worker threads cannot be forcibly cancelled).
            commit_msg = await asyncio.to_thread(_generate_commit_msg_sync, prompt)
        except Exception as e:
            log_event(
                "ai_commit_gen_failed",
                error=str(e) or type(e).__name__,
                error_type=type(e).__name__,
                level="warning",
            )

    if not commit_msg:
        commit_msg = f"feat: auto-generated implementation for {requirement[:40]}"

    commit_hash = create_commit(commit_msg)
    log_event("ai_commit_completed", hash=commit_hash, msg=commit_msg)
    return commit_msg