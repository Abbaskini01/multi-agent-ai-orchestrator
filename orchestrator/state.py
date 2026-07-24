from typing import TypedDict


class ProjectTask(TypedDict):
    filename: str          # Name of target file (e.g., 'database.py')
    task_description: str  # Low-level coding instructions
    generated_code: str    # Raw Python code for this file


class OrchestratorState(TypedDict):
    user_requirement: str          # Original prompt passed into orchestrator
    acceptance_criteria: list[str] # Functional goals from Planner
    tasks: list[ProjectTask]        # Multi-file task array
    current_task_index: int        # Sequential execution pointer
    error_message: str             # Error traceback log
    retry_count: int               # Circuit breaker iteration counter
    human_feedback: str            # Phase 7: User feedback for re-planning
    is_approved: bool              # Phase 7: HITL approval flag