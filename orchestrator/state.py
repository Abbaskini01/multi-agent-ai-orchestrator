from typing import TypedDict, List, Dict, Any


class ProjectTask(TypedDict):
    filename: str          # e.g., "src/database.py", "tests/test_database.py", "requirements.txt"
    task_description: str  # Architectural role, inputs, outputs, public interfaces
    generated_code: str    # Filled by Executor Node


class OrchestratorState(TypedDict):
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