"""
Neural Glass AI Orchestrator — Automated Verification & Testing Engine
"""

import sys
from typing import Dict, Any
from orchestrator.state import OrchestratorState
from orchestrator.runner import run_sandbox_command
from core.logger import log_event


async def run_flake8_lint(state: OrchestratorState) -> Dict[str, Any]:
    """Runs flake8 static code analysis on workspace_sandbox, ignoring cosmetic whitespace rules."""
    cmd = (
        f"{sys.executable} -m flake8 . "
        f"--max-line-length=120 "
        f"--ignore=E501,W503,E302,E303,E305,W291,W292,W293"
    )
    code, out, err = await run_sandbox_command(cmd)
    
    passed = (code == 0)
    output_text = out if out.strip() else ("No lint issues found." if passed else err)
    
    result = {
        "passed": passed,
        "exit_code": code,
        "output": output_text
    }
    state["lint_results"] = result
    log_event("flake8_lint_complete", passed=passed, exit_code=code)
    return result
    
async def run_mypy_check(state: OrchestratorState) -> Dict[str, Any]:
    """Runs mypy static type analysis on workspace_sandbox."""
    cmd = f"{sys.executable} -m mypy . --ignore-missing-imports"
    code, out, err = await run_sandbox_command(cmd)
    
    passed = (code == 0)
    output_text = out if out.strip() else (err if err.strip() else "Type check passed.")
    
    result = {
        "passed": passed,
        "exit_code": code,
        "output": output_text
    }
    state["type_check_results"] = result
    log_event("mypy_check_complete", passed=passed, exit_code=code)
    return result


async def run_pytest_suite(state: OrchestratorState) -> Dict[str, Any]:
    """Runs pytest unit test suite inside workspace_sandbox."""
    cmd = f"{sys.executable} -m pytest -v --tb=short"
    code, out, err = await run_sandbox_command(cmd)
    
    passed = (code == 0)
    output_text = out if out.strip() else (err if err.strip() else "No tests collected or executed.")
    
    result = {
        "passed": passed,
        "exit_code": code,
        "output": output_text
    }
    state["test_results"] = result
    log_event("pytest_suite_complete", passed=passed, exit_code=code)
    return result