import json
from orchestrator.config import llm
from orchestrator.state import OrchestratorState, ProjectTask

def planner_node(state: OrchestratorState) -> dict:
    """System Architect Agent: Analyzes requirements to generate task plans & criteria."""
    print("\n[Node Activating] ---> Planner Node (Decomposition + Criteria)")
    print("-> Requesting structured JSON plan and acceptance criteria from Groq (Llama 3.3)...")
    
    architect_system_prompt = (
        "You are an elite software architect. Analyze the user requirement "
        "and produce a JSON object with EXACTLY two top-level keys:\n"
        "1. 'acceptance_criteria': A list of verifiable string statements.\n"
        "2. 'tasks': A list of objects with 'filename' and 'task_description'.\n\n"
        "CRITICAL RULES:\n"
        "1. Keep project structure concise (maximum 2-3 essential files like 'database.py' and 'app.py').\n"
        "2. Provide default values or optional flags for CLI arguments.\n"
        "3. Handle EOFError gracefully in interactive input loops."
    )
    
    user_prompt = f"Decompose this project requirement: '{state['user_requirement']}'"
    
    response = llm.bind(response_format={"type": "json_object"}).invoke(
        [("system", architect_system_prompt), ("human", user_prompt)]
    )
    
    try:
        parsed_plan = json.loads(response.content)
        raw_criteria = parsed_plan.get("acceptance_criteria", [])
        raw_tasks = parsed_plan.get("tasks", [])
        
        structured_tasks = [
            ProjectTask(filename=t["filename"], task_description=t["task_description"], generated_code="")
            for t in raw_tasks
        ]
        
        print(f"-> Success: Planner produced {len(raw_criteria)} Criteria & {len(structured_tasks)} Tasks.")
        return {
            "acceptance_criteria": raw_criteria,
            "tasks": structured_tasks,
            "current_task_index": 0
        }
    except Exception as err:
        print(f"-> Critical Failure: Planner JSON parse error: {err}")
        return {"acceptance_criteria": [], "tasks": [], "current_task_index": 0}