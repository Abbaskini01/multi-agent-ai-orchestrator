"""
Neural Glass AI Orchestrator — Unified State Management Definition
"""

from typing import TypedDict, List, Dict, Any


class ProjectTask(TypedDict):
    filename: str          # e.g., "src/database.py", "tests/test_database.py", "requirements.txt"
    task_description: str  # Architectural role, inputs, outputs, public interfaces
    generated_code: str    # Filled by Executor Node


class OrchestratorState(TypedDict, total=False):
    user_requirement: str
    project_name: str          # e.g., "ExpenseTracker"
    architecture_pattern: str  # e.g., "Layered Clean Architecture (Modular CLI)"
    folders: List[str]         # e.g., ["src", "tests", "docs", "scripts", ".github/workflows"]
    acceptance_criteria: List[str]
    tasks: List[ProjectTask]
    current_task_index: int
    error_message: str
    retry_count: int
    human_feedback: str
    is_approved: bool

    # --- Phase V5.3 Multi-Agent Mesh Extensions ---
    clean_requirement: str
    parsed_intent: str
    generated_files: Dict[str, str]
    plan_steps: List[str]
    code_review_notes: List[str]
    security_findings: List[Dict[str, Any]]
    documentation_markdown: str
    git_commit_hash: str
    git_commit_msg: str

    # --- Phase V6.1 Interactive Sandbox & Testing Extensions ---
    execution_logs: List[Dict[str, Any]]
    lint_results: Dict[str, Any]
    type_check_results: Dict[str, Any]
    test_results: Dict[str, Any]

    # --- Phase V6.2 Reflection & Self-Repair Extensions ---
    repair_attempts: int
    is_repaired: bool
    repair_history: List[Dict[str, Any]]

    # --- Phase V6.3 Human-in-the-Loop (HITL) Extensions ---
    requires_approval: bool
    approval_status: str       # "PENDING", "APPROVED", "REJECTED"
    human_notes: str


def create_initial_orchestrator_state(requirement: str) -> OrchestratorState:
    """Helper factory to create a clean state dictionary for execution pipelines."""
    return OrchestratorState(
        user_requirement=requirement,
        clean_requirement=requirement,
        project_name="LiveGeneratedProject",
        architecture_pattern="Layered Clean Architecture",
        folders=["src", "tests"],
        acceptance_criteria=[],
        tasks=[],
        current_task_index=0,
        error_message="",
        retry_count=0,
        human_feedback="",
        is_approved=True,
        generated_files={},
        plan_steps=[],
        code_review_notes=[],
        security_findings=[],
        documentation_markdown="",
        git_commit_hash="",
        git_commit_msg="",
        execution_logs=[],
        lint_results={"passed": True, "exit_code": 0, "output": "Not run"},
        type_check_results={"passed": True, "exit_code": 0, "output": "Not run"},
        test_results={"passed": True, "exit_code": 0, "output": "Not run"},
        repair_attempts=0,
        is_repaired=False,
        repair_history=[],
        requires_approval=False,
        approval_status="APPROVED",
        human_notes=""
    )