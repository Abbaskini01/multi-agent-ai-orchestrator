import sys
import json
import subprocess
import tempfile
from pathlib import Path
from orchestrator.config import llm
from orchestrator.state import OrchestratorState
from orchestrator.utils import clean_extracted_code


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
    """Gate 2: Isolated Subprocess Workspace Execution."""
    print("\n[Node Activating] ---> Multi-File Workspace Runtime Tester Node")
    tasks = state.get("tasks", [])
    current_retries = state.get("retry_count", 0)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for task in tasks:
            (temp_path / task["filename"]).write_text(clean_extracted_code(task["generated_code"]), encoding="utf-8")

        filenames = [t["filename"] for t in tasks]
        entry_point = "app.py" if "app.py" in filenames else filenames[0]
        entry_point_path = temp_path / entry_point

        try:
            result = subprocess.run(
                [sys.executable, str(entry_point_path)],
                input="4\n3\nexit\n",
                capture_output=True,
                text=True,
                timeout=3,
                cwd=temp_dir
            )

            if result.returncode != 0:
                runtime_error = f"RuntimeError in '{entry_point}' (Exit Code {result.returncode}):\n{result.stderr}"
                return {"error_message": runtime_error, "retry_count": current_retries + 1}

            print("-> Success: Workspace runtime integration test passed cleanly!")
            return {"error_message": "", "retry_count": current_retries}

        except subprocess.TimeoutExpired:
            return {"error_message": "TimeoutError: Execution exceeded 3 seconds safety limit.", "retry_count": current_retries + 1}


def functional_tester_node(state: OrchestratorState) -> dict:
    """Gate 3: Dynamic Unittest Assertion Engine."""
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
        "1. DIRECT CLASS IMPORTS: Import database and logic classes directly from their defining module "
        "(e.g., `from database import Database`).\n"
        "2. NO INTERACTIVE LOOPS: NEVER import or execute `main()`, driver loops, or functions that trigger `input()`. "
        "Test ONLY class methods, return values, and data mutations in isolation.\n"
        "3. EXPLICIT ARGPARSE ARGS: When unit testing `parse_args()`, ALWAYS pass an explicit list of string arguments "
        "(e.g., `parse_args([])` or `parse_args(['--database', 'test.db'])`). NEVER call `parse_args()` without arguments inside unittest because `sys.argv` contains test arguments!\n"
        "4. NO CUSTOM EXCEPTION ASSERTS: Do NOT assert that methods raise custom exception types unless explicitly raised in source.\n"
        "5. NO STDOUT MATCHING: Test object state and methods directly. Do NOT use stdout mocks or string prints.\n"
        "6. ISOLATED DB INSTANCES: Instantiate database classes directly using custom temp filenames or `:memory:`.\n"
        "7. CLI EXITS: Wrap invalid argparse CLI calls in `with self.assertRaises(SystemExit):`.\n\n"
        "Return ONLY raw Python code for `test_suite.py` without markdown wraps.\n\n"
        f"Acceptance Criteria:\n{json.dumps(criteria, indent=2)}\n\n"
        f"Codebase Context:\n{codebase_context}"
    )

    response = llm.invoke(test_gen_prompt)
    test_suite_code = clean_extracted_code(response.content)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for task in tasks:
            (temp_path / task["filename"]).write_text(clean_extracted_code(task["generated_code"]), encoding="utf-8")
        (temp_path / "test_suite.py").write_text(test_suite_code, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "test_suite.py"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=temp_dir
            )

            if result.returncode != 0:
                test_error_log = f"FunctionalValidationError (Exit Code {result.returncode}):\nStderr: {result.stderr}\nStdout: {result.stdout}"
                return {"error_message": test_error_log, "retry_count": current_retries + 1}

            print("-> Success: All dynamic functional tests passed cleanly!")
            return {"error_message": "", "retry_count": current_retries}

        except subprocess.TimeoutExpired:
            return {"error_message": "TimeoutError: Functional test execution timed out.", "retry_count": current_retries + 1}