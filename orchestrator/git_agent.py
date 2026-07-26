"""
Neural Glass AI Orchestrator — AI Commit Message Generator Agent
"""

from core.git import get_unified_diff, create_commit, init_sandbox_repo
from llm.groq import groq_client
from core.config import settings
from core.logger import log_event


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
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=settings.default_groq_model,
                max_tokens=60
            )
            commit_msg = completion.choices[0].message.content.strip()
        except Exception as e:
            log_event("ai_commit_gen_failed", error=str(e), level="warning")

    if not commit_msg:
        commit_msg = f"feat: auto-generated implementation for {requirement[:40]}"

    commit_hash = create_commit(commit_msg)
    log_event("ai_commit_completed", hash=commit_hash, msg=commit_msg)
    return commit_msg