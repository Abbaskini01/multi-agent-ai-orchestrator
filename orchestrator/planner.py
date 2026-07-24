import json
from orchestrator.config import invoke_llm_with_fallback
from orchestrator.state import OrchestratorState, ProjectTask


def planner_node(state: OrchestratorState) -> dict:
    """
    Version 2 Architect Agent Node:
    Analyzes requirements and designs a production-grade repository blueprint.
    """
    if state.get("is_approved", False) and state.get("tasks"):
        print("\n[Node Activating] ---> Architect Agent Node (Blueprint Approved — Proceeding)")
        return {}

    print("\n[Node Activating] ---> Architect Agent Node (Repo Blueprint & Architecture)")
    
    feedback = state.get("human_feedback", "")
    user_req = state.get("user_requirement", "")
    
    if feedback:
        print(f"-> Incorporating Human Feedback into Blueprint: '{feedback}'")
    else:
        print("-> Designing complete repository blueprint & software architecture...")

    architect_system_prompt = (
        "You are an Elite Principal Software Architect. Your job is to design a complete, production-ready "
        "software repository blueprint for the given requirement.\n\n"
        "STRICT JSON OUTPUT FORMAT:\n"
        "Return a single JSON object with EXACTLY these top-level keys:\n"
        "1. 'project_name': Short CamelCase string (e.g., 'ExpenseTrackerCLI').\n"
        "2. 'architecture_pattern': Specific design pattern (e.g., 'Layered Architecture (Modular CLI + SQLite Service Pattern)').\n"
        "3. 'folders': List of directory paths to scaffold (e.g., ['src', 'tests', 'docs', '.github/workflows']).\n"
        "4. 'acceptance_criteria': List of 5-6 verifiable string criteria.\n"
        "5. 'files': List of file objects, each containing 'filename' and 'task_description'.\n\n"
        "REPOSITORY BLUEPRINT RULES:\n"
        "- ARCHITECTURE: Organize code into logical layers (e.g., `src/main.py`, `src/database.py`, `src/services.py`, `src/config.py`, `src/logger.py`).\n"
        "- CONFIG & DEPENDENCIES: Include `requirements.txt`, `.env.example`, `.gitignore`, and `pyproject.toml` or `Dockerfile` if relevant.\n"
        "- TESTING: Include project-specific test suites under `tests/` (e.g., `tests/test_database.py`, `tests/test_services.py`).\n"
        "- DOCUMENTATION: Include `README.md` and `docs/architecture.md`.\n"
        "- CI/CD: Include `.github/workflows/python.yml` for automated testing.\n"
        "- COMPACT SCALE: Aim for 7 to 12 essential files total to balance completeness with generation speed.\n"
        "- INTERACTIVE LOOPS: Specify that main driver loops MUST handle `EOFError` and use simple numeric choices."
    )

    user_prompt = f"Requirement: '{user_req}'"
    if feedback:
        user_prompt += f"\nHuman Feedback / Requested Changes: '{feedback}'"

    response = invoke_llm_with_fallback(
        [("system", architect_system_prompt), ("human", user_prompt)],
        response_format={"type": "json_object"}
    )

    try:
        parsed_plan = json.loads(response.content)
        proj_name = parsed_plan.get("project_name", "GeneratedApp")
        arch_pattern = parsed_plan.get("architecture_pattern", "Layered Architecture")
        raw_folders = parsed_plan.get("folders", ["src", "tests", "docs"])
        raw_criteria = parsed_plan.get("acceptance_criteria", [])
        raw_files = parsed_plan.get("files", [])

        if not raw_files:
            raise ValueError("LLM returned an empty or invalid blueprint structure.")

        structured_tasks = [
            ProjectTask(
                filename=f["filename"],
                task_description=f["task_description"],
                generated_code=""
            )
            for f in raw_files
        ]

        print(f"-> Success: Blueprint created for '{proj_name}' using [{arch_pattern}].")
        print(f"   Scaffolding: {len(raw_folders)} Folders | {len(structured_tasks)} Files | {len(raw_criteria)} Acceptance Criteria")

        return {
            "project_name": proj_name,
            "architecture_pattern": arch_pattern,
            "folders": raw_folders,
            "acceptance_criteria": raw_criteria,
            "tasks": structured_tasks,
            "current_task_index": 0,
            "human_feedback": ""
        }
    except Exception as err:
        print(f"-> Blueprint Generation Failed: {err}")
        return {
            "project_name": "PendingGeneration",
            "architecture_pattern": "Unassigned",
            "folders": [],
            "acceptance_criteria": [],
            "tasks": [],
            "current_task_index": 0
        }