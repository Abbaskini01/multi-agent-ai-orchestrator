"""
Neural Glass AI Orchestrator — Sandbox Git Lifecycle Manager
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import log_event

SANDBOX_DIR = Path("workspace_sandbox")


def _run_git_cmd(args: List[str], cwd: Path = SANDBOX_DIR) -> str:
    """Executes a Git command inside the sandbox directory and returns stdout."""
    if not cwd.exists():
        cwd.mkdir(parents=True, exist_ok=True)

    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd.absolute()),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log_event("git_cmd_failed", cmd=args, stderr=e.stderr.strip(), level="warning")
        return ""


def init_sandbox_repo() -> bool:
    """Ensures workspace_sandbox is a valid Git repository."""
    git_dir = SANDBOX_DIR / ".git"
    if not git_dir.exists():
        _run_git_cmd(["init"])
        _run_git_cmd(["config", "user.name", "Neural Glass AI"])
        _run_git_cmd(["config", "user.email", "ai-orchestrator@neuralglass.local"])
        log_event("git_repo_initialized", path=str(SANDBOX_DIR))
        return True
    return False


def get_git_status() -> Dict[str, List[str]]:
    """Returns modified, untracked, and staged files in the sandbox repository."""
    init_sandbox_repo()
    stdout = _run_git_cmd(["status", "--porcelain"])
    
    modified, untracked, staged = [], [], []
    for line in stdout.splitlines():
        if not line:
            continue
        status_code = line[:2]
        filename = line[3:].strip()
        if "??" in status_code:
            untracked.append(filename)
        elif "M" in status_code:
            modified.append(filename)
        elif "A" in status_code or "M " in status_code:
            staged.append(filename)

    return {"modified": modified, "untracked": untracked, "staged": staged}


def get_unified_diff() -> str:
    """Generates a unified diff for all current changes in the sandbox."""
    init_sandbox_repo()
    _run_git_cmd(["add", "-N", "."])  # Stage untracked files intent-to-add
    diff = _run_git_cmd(["diff", "HEAD"])
    if not diff:
        diff = _run_git_cmd(["diff"])
    return diff


def create_commit(message: str) -> Optional[str]:
    """Stages all workspace changes and creates a Git commit."""
    init_sandbox_repo()
    _run_git_cmd(["add", "."])
    status = _run_git_cmd(["status", "--porcelain"])
    if not status:
        return None  # Nothing to commit

    _run_git_cmd(["commit", "-m", message])
    commit_hash = _run_git_cmd(["rev-parse", "--short", "HEAD"])
    log_event("git_commit_created", hash=commit_hash, message=message)
    return commit_hash


def get_commit_history(limit: int = 10) -> List[Dict[str, str]]:
    """Returns recent commit log entries."""
    init_sandbox_repo()
    stdout = _run_git_cmd(["log", f"-n{limit}", "--pretty=format:%h|%s|%cr"])
    commits = []
    for line in stdout.splitlines():
        if not line:
            continue
        parts = line.split("|")
        if len(parts) == 3:
            commits.append({"hash": parts[0], "message": parts[1], "relative_time": parts[2]})
    return commits


def rollback_to_commit(commit_hash: str) -> bool:
    """Hard resets the workspace sandbox to a specified commit hash."""
    init_sandbox_repo()
    result = _run_git_cmd(["reset", "--hard", commit_hash])
    _run_git_cmd(["clean", "-fd"])
    log_event("git_rollback_executed", target_hash=commit_hash)
    return bool(result)