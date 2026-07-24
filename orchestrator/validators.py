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
    """
    Phase 8 Docker Sandboxing Runner:
    Runs commands inside an ephemeral python:3.11-slim Docker container.
    Falls back to local subprocess if Docker is unavailable.
    """
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
    """Gate 1: Static AST Syntax Verification."""
    print("\n[Node Activating] ---> Per-File Syntax Tester Node")
    tasks = state.get("tasks", [])
    current_retries = state.get("retry_count", 0)

    for task in tasks:
        filename = task["filename"]
        code = clean_extracted_code(task["generated_code"])
        try:
            compile(code, filename=filename, mode="exec")
        except SyntaxError as syntax_err:
            error_context = f"SyntaxError in '{filename}' line {syntax_err.lineno}: {syntax_err.msg}"
            return {"error_message": error_context, "retry_count": current_retries + 1}

    print("-> Success: All files compiled with zero syntax errors!")
    return {"error_message": "", "retry_count": current_retries}


def runtime_tester_node(state: OrchestratorState) -> dict:
    """Gate 2: Isolated Workspace Execution (Phase 8 Docker Support)."""
    print("\n[Node Activating] ---> Multi-File Workspace Runtime Tester Node")
    tasks = state.get("tasks", [])
    current_retries = state.get("retry_count", 0)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for task in tasks:
            (temp_path / task["filename"]).write_text(clean_extracted_code(task["generated_code"]), encoding="utf-8")

        filenames = [t["filename"] for t in tasks]
        entry_point = "app.py" if "app.py" in filenames else filenames[0]

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
    """Gate 3: Dynamic Unittest Assertion Engine (Phase 8 Docker Support)."""
    print("\n[Node Activating] ---> Functional Tester Node (Assertion Suite)")
    tasks = state.get("tasks", [])
    criteria = state.get("acceptance_criteria", [])
    current_retries = state.get("retry_count", 0)

    codebase_context = ""
    for t in tasks:
        codebase_context += f"\nFile: {t['filename']}\n```python\n{t['generated_code']}\n```\n"

    test_gen_prompt = (
        "You are a QA automation engineer generating an executable `unittest` script named `test_suite.py`.\n\n"
        "STRICT UNITTEST GENERATION RULES:\n"
        "1. EXPLICIT FUNCTION/CLASS IMPORTS: Always explicitly import classes AND top-level functions from their modules "
        "(e.g., `from database import Database` and `from app import parse_args`). NEVER call a function without importing it first!\n"
        "2. NO INTERACTIVE LOOPS: NEVER import or execute `main()`, driver loops, or functions that trigger `input()`. "
        "Test ONLY class methods, helper functions, return values, and data mutations in isolation.\n"
        "3. MATCH DEFINED ARGPARSE FLAGS: Inspect `app.py` before generating tests for `parse_args()`. "
        "ONLY pass CLI argument strings (e.g., `parse_args(['--db', 'test.db'])`) IF those flags are explicitly registered with `parser.add_argument()` in `app.py`. Otherwise, test `parse_args([])` with an empty list!\n"
        "4. NO CUSTOM EXCEPTION ASSERTS: Do NOT assert that methods raise custom exception types unless explicitly raised in source.\n"
        "5. STANDARD IMPORTS: Always include required standard library modules (e.g., `import sqlite3`) at the top of `test_suite.py` if testing or asserting standard exceptions.\n"
        "6. NO STDOUT MATCHING: Test object state and methods directly. Do NOT use stdout mocks or string prints.\n"
        "7. ISOLATED DB INSTANCES: Instantiate database classes directly using custom temp filenames or `:memory:`.\n"
        "8. CLI EXITS: Wrap invalid argparse CLI calls in `with self.assertRaises(SystemExit):`.\n\n"
        "Return ONLY raw Python code for `test_suite.py` without markdown wraps.\n\n"
        f"Acceptance Criteria:\n{json.dumps(criteria, indent=2)}\n\n"
        f"Codebase Context:\n{codebase_context}"
    )

    response = invoke_llm_with_fallback(test_gen_prompt)
    test_suite_code = clean_extracted_code(response.content)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for task in tasks:
            (temp_path / task["filename"]).write_text(clean_extracted_code(task["generated_code"]), encoding="utf-8")
        (temp_path / "test_suite.py").write_text(test_suite_code, encoding="utf-8")

        try:
            cmd = ["python", "-u", "-m", "unittest", "test_suite.py"]
            result = run_code_in_sandbox(temp_dir, cmd, timeout=25)

            if result.returncode != 0:
                test_error_log = f"FunctionalValidationError (Exit Code {result.returncode}):\nStderr: {result.stderr}\nStdout: {result.stdout}"
                return {"error_message": test_error_log, "retry_count": current_retries + 1}

            print("-> Success: All dynamic functional tests passed cleanly!")
            return {"error_message": "", "retry_count": current_retries}

        except subprocess.TimeoutExpired:
            return {"error_message": "TimeoutError: Functional test execution timed out.", "retry_count": current_retries + 1}