"""
Neural Glass AI Orchestrator — Sandbox Execution Runner
"""

import asyncio
from pathlib import Path
from typing import Tuple
from core.logger import log_event

SANDBOX_DIR = Path("workspace_sandbox")


async def run_sandbox_command(
    command: str,
    cwd: Path = SANDBOX_DIR,
    timeout_seconds: int = 15
) -> Tuple[int, str, str]:
    """
    Executes a shell command within the workspace sandbox under a enforced timeout limit.
    Returns (returncode, stdout, stderr).
    """
    if not cwd.exists():
        cwd.mkdir(parents=True, exist_ok=True)

    log_event("executing_sandbox_command", cmd=command, timeout=timeout_seconds)

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds
            )
            returncode = proc.returncode if proc.returncode is not None else 0
            stdout = stdout_bytes.decode(errors="replace")
            stderr = stderr_bytes.decode(errors="replace")
            return returncode, stdout, stderr

        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            log_event("sandbox_command_timeout", cmd=command, level="warning")
            return 124, "", f"Execution timed out after {timeout_seconds} seconds."

    except Exception as e:
        log_event("sandbox_command_error", cmd=command, error=str(e), level="error")
        return 1, "", str(e)