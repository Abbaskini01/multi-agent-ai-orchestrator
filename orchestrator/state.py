from typing import TypedDict

class ProjectTask(TypedDict):
    filename: str          # Name of target file (e.g., 'database.py')
    task_description: str  # Low-level coding instructions
    generated_code: str    # Raw Python code for this file


class OrchestratorState(TypedDict):
    user_requirement: str          # User prompt
    acceptance_criteria: list[str] # Architect acceptance rules
    tasks: list[ProjectTask]        # Multi-file task array
    current_task_index: int        # Sequential pointer
    error_message: str             # Error traceback log
    retry_count: int               # Circuit breaker iteration counter