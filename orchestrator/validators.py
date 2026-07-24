import sys
import json
import subprocess
import tempfile
from pathlib import Path
from orchestrator.config import invoke_llm_with_fallback
from orchestrator.state import OrchestratorState
from orchestrator.utils import clean_extracted_code


def is_docker_available() -> bool:
    """Checks if Docker CLI is installed and the Docker daemon is actively running."""
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=3)
        return res.returncode == 0
    except Exception:
        return False


def run_code_in_sandbox(temp_dir: str, cmd_list: list[str], timeout: int = 25, input_text: str = None) -> subprocess.CompletedProcess:
    """Runs commands inside an ephemeral python:3.11-slim Docker container or local subprocess fallback."""
    if is_docker_available():
        print("   [+] Engine: Docker Sandbox Container (python:3.11-slim)")
        docker_cmd = [
            "docker", "run", "--rm", "-i",
            "-v", f"{temp_dir}:/app",
            "-w", "/app",
            "python:3.11-slim"
        ] + cmd_list

        return subprocess.run(
            docker_cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    else:
        print("   [!] Docker daemon offline/unavailable. Falling back to Local Subprocess.")
        return subprocess.run(
            cmd_list,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=temp_dir
        )


def syntax_tester_node(state: OrchestratorState) -> dict:
    """Gate 1: Static AST Syntax Verification across all generated repository files."""
    print("\n[Node Activating] ---> Per-File Syntax Tester Node")
    tasks = state.get("tasks", [])
    current_retries = state.get("retry_count", 0)

    for task in tasks:
        filename = task["filename"]
        code = clean_extracted_code(task.get("generated_code", ""))
        
        # Skip empty unwritten files or non-python config files (like .gitignore, README.md)
        if not code or not filename.endswith(".py"):
            continue

        try:
            compile(code, filename=filename, mode="exec")
        except SyntaxError as syntax_err:
            error_context = f"SyntaxError in '{filename}' line {syntax_err.lineno}: {syntax_err.msg}"
            return {"error_message": error_context, "retry_count": current_retries + 1}

    print("-> Success: All Python modules compiled with zero syntax errors!")
    return {"error_message": "", "retry_count": current_retries}


def runtime_tester_node(state: OrchestratorState) -> dict:
    """Gate 2: Isolated Workspace Execution with Deep Directory Creation."""
    print("\n[Node Activating] ---> Multi-File Workspace Runtime Tester Node")
    tasks = state.get("tasks", [])
    current_retries = state.get("retry_count", 0)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Write files with nested directory creation safety
        for task in tasks:
            code = clean_extracted_code(task.get("generated_code", ""))
            if code:
                file_path = temp_path / task["filename"]
                file_path.parent.mkdir(parents=True, exist_ok=True)  # <-- FIXES FileNotFoundError
                file_path.write_text(code, encoding="utf-8")

        filenames = [t["filename"] for t in tasks if t.get("generated_code")]
        
        # Find entry point dynamically across subdirectories
        entry_candidates = ["src/main.py", "main.py", "src/app.py", "app.py"]
        entry_point = None
        for cand in entry_candidates:
            if cand in filenames:
                entry_point = cand
                break
        if not entry_point and filenames:
            py_files = [f for f in filenames if f.endswith(".py")]
            entry_point = py_files[0] if py_files else filenames[0]

        if not entry_point:
            print("-> Notice: No executable entry point found yet. Skipping runtime runner.")
            return {"error_message": "", "retry_count": current_retries}

        try:
            comprehensive_input = "1\nTest Expense\n10.50\n2\n3\n4\n-q\nquit\nexit\n"
            cmd = ["python", "-u", entry_point]
            result = run_code_in_sandbox(temp_dir, cmd, timeout=25, input_text=comprehensive_input)

            if result.returncode != 0:
                runtime_error = f"RuntimeError in '{entry_point}' (Exit Code {result.returncode}):\n{result.stderr}"
                return {"error_message": runtime_error, "retry_count": current_retries + 1}

            print("-> Success: Workspace runtime integration test passed cleanly!")
            return {"error_message": "", "retry_count": current_retries}

        except subprocess.TimeoutExpired:
            return {"error_message": "TimeoutError: Execution exceeded safety limit.", "retry_count": current_retries + 1}


def functional_tester_node(state: OrchestratorState) -> dict:
    """Gate 3: Dynamic Unittest Assertion Engine across subdirectories."""
    print("\n[Node Activating] ---> Functional Tester Node (Assertion Suite)")
    tasks = state.get("tasks", [])
    criteria = state.get("acceptance_criteria", [])
    current_retries = state.get("retry_count", 0)

    codebase_context = ""
    for t in tasks:
        if t.get("generated_code"):
            codebase_context += f"\nFile: {t['filename']}\n```python\n{t['generated_code']}\n```\n"

    test_gen_prompt = (
        "You are a QA automation engineer generating an executable `unittest` script named `tests/test_suite.py`.\n\n"
        "STRICT UNITTEST GENERATION RULES:\n"
        "1. PATH IMPORTS: Ensure `sys.path.insert(0, 'src')` or `sys.path.insert(0, '.')` is at the top of `test_suite.py` "
        "so imports like `from database import Database` or `from services import ExpenseService` resolve cleanly from subfolders!\n"
        "2. NO INTERACTIVE LOOPS: NEVER import or execute driver loops or main functions triggering `input()`. Test class methods and services in isolation.\n"
        "3. STANDARD IMPORTS: Include standard modules (e.g., `import sqlite3`, `import unittest`, `import sys`) at the top of `test_suite.py`.\n"
        "4. NO STDOUT MATCHING: Test object state and methods directly.\n"
        "5. ISOLATED DB INSTANCES: Instantiate database classes directly using `:memory:` or temp files.\n\n"
        "Return ONLY raw Python code for `tests/test_suite.py` without markdown wraps.\n\n"
        f"Acceptance Criteria:\n{json.dumps(criteria, indent=2)}\n\n"
        f"Codebase Context:\n{codebase_context}"
    )

    response = invoke_llm_with_fallback(test_gen_prompt)
    test_suite_code = clean_extracted_code(response.content)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for task in tasks:
            code = clean_extracted_code(task.get("generated_code", ""))
            if code:
                fp = temp_path / task["filename"]
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(code, encoding="utf-8")

        test_fp = temp_path / "tests" / "test_suite.py"
        test_fp.parent.mkdir(parents=True, exist_ok=True)
        test_fp.write_text(test_suite_code, encoding="utf-8")

        try:
            cmd = ["python", "-u", "-m", "unittest", "tests/test_suite.py"]
            result = run_code_in_sandbox(temp_dir, cmd, timeout=25)

            if result.returncode != 0:
                test_error_log = f"FunctionalValidationError (Exit Code {result.returncode}):\nStderr: {result.stderr}\nStdout: {result.stdout}"
                return {"error_message": test_error_log, "retry_count": current_retries + 1}

            print("-> Success: All dynamic functional tests passed cleanly!")
            return {"error_message": "", "retry_count": current_retries}

        except subprocess.TimeoutExpired:
            return {"error_message": "TimeoutError: Functional test execution timed out.", "retry_count": current_retries + 1}