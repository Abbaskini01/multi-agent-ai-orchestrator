"""
Neural Glass AI Orchestrator — Local Subprocess Workspace Sandbox & Persistence
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict

from core.config import settings
from core.logger import log_event


def execute_shell_sync(cmd_str: str, cwd_path: Path) -> str:
    """Executes shell commands cleanly in an isolated UTF-8 subprocess environment."""
    exec_cmd = cmd_str
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    py_dir = str(Path(sys.executable).parent)
    if py_dir not in env.get("PATH", ""):
        env["PATH"] = py_dir + os.pathsep + env.get("PATH", "")

    if os.name == 'nt':
        if exec_cmd == "ls":
            exec_cmd = "dir /b"
        elif exec_cmd.startswith("ls "):
            target_path = exec_cmd.replace("ls ", "", 1).strip().replace('/', '\\')
            exec_cmd = f"dir /b {target_path}"
        elif exec_cmd.startswith("cat "):
            target_path = exec_cmd.replace("cat ", "", 1).strip().replace('/', '\\')
            exec_cmd = f"type {target_path}"

    res = subprocess.run(
        exec_cmd,
        shell=True,
        cwd=str(cwd_path),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    output = ""
    if res.stdout:
        output += res.stdout.replace("\r\n", "\n").replace("\n", "\r\n")
    if res.stderr:
        formatted_err = res.stderr.replace("\r\n", "\n").replace("\n", "\r\n")
        output += f"\x1b[31m{formatted_err}\x1b[0m"

    return output or "\r\n"


def write_generated_files_to_sandbox(generated_files: Dict[str, str]) -> None:
    """Cleans previous workspace contents and writes freshly synthesized codebase."""
    workspace = settings.workspace_dir
    workspace.mkdir(parents=True, exist_ok=True)

    # Purge old workspace files and directories
    for root, dirs, files in os.walk(workspace, topdown=False):
        for name in files:
            try:
                os.remove(Path(root) / name)
            except Exception:
                pass
        for name in dirs:
            try:
                os.rmdir(Path(root) / name)
            except Exception:
                pass

    # Persist newly generated files
    for rel_path, content in generated_files.items():
        file_path = workspace / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    log_event("files_persisted_to_sandbox", count=len(generated_files))