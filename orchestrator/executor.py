import json
from orchestrator.config import llm
from orchestrator.state import OrchestratorState, ProjectTask
from orchestrator.utils import clean_extracted_code

def executor_node(state: OrchestratorState) -> dict:
    """Specialized Executor Agent: Generates initial task files OR performs targeted surgical repairs."""
    print("\n[Node Activating] ---> Executor Node")
    
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", 0)

    # -----------------------------------------------------------------
    # Branch A: Multi-File Targeted Self-Correction Mode
    # -----------------------------------------------------------------
    if error_message:
        print(f"-> Self-Correction Triggered (Attempt #{retry_count}). Analyzing for targeted repair...")
        codebase_context = ""
        for t in tasks:
            codebase_context += f"\nFile: {t['filename']}\n```python\n{t['generated_code']}\n```\n"

        fix_system_prompt = (
            "You are an expert Python engineer debugging a multi-file project workspace.\n"
            "Analyze the error trace log and the existing multi-file codebase.\n\n"
            "CRITICAL JSON FORMATTING RULES:\n"
            "1. You MUST respond with a single, valid JSON object containing a key called 'files'.\n"
            "2. 'files' must be an array of objects, each having 'filename' and 'code' keys.\n"
            "3. The 'code' property must contain valid, executable Python code as a standard JSON string.\n\n"
            "CRITICAL PYTHON SYNTAX RULES:\n"
            "1. MULTILINE STRINGS: When writing SQL statements or multi-line text in Python, ALWAYS use triple quotes (\"\"\"...\"\"\") "
            "or keep them on a single line.\n"
            "2. SURGICAL REPAIR: Modify ONLY the specific file(s) causing the failure."
        )

        user_prompt = (
            f"Requirement: '{state['user_requirement']}'\n\n"
            f"Validation Failure Error Trace:\n"
            f"--------------------------------------------------\n"
            f"{error_message}\n"
            f"--------------------------------------------------\n\n"
            f"Current Multi-File Codebase:\n"
            f"{codebase_context}\n\n"
            f"Identify the root cause, fix ONLY the affected file(s), and return valid JSON."
        )

        response = llm.bind(response_format={"type": "json_object"}).invoke(
            [("system", fix_system_prompt), ("human", user_prompt)]
        )

        try:
            parsed = json.loads(response.content)
            raw_files = parsed.get("files", [])
            if isinstance(raw_files, dict):
                raw_files = [raw_files]

            updated_tasks = list(tasks)
            repaired_filenames = []
            
            for fix in raw_files:
                if isinstance(fix, dict) and "filename" in fix and "code" in fix:
                    fname = fix["filename"]
                    fcode = clean_extracted_code(fix["code"])
                    for i, t in enumerate(updated_tasks):
                        if t["filename"] == fname:
                            updated_tasks[i] = ProjectTask(
                                filename=fname,
                                task_description=t["task_description"],
                                generated_code=fcode
                            )
                            repaired_filenames.append(fname)
            
            untouched_files = [t["filename"] for t in updated_tasks if t["filename"] not in repaired_filenames]
            print(f"-> Targeted Repair Complete. Repaired: {repaired_filenames} | Preserved untouched: {untouched_files}")
                        
            return {"tasks": updated_tasks}
        except Exception as e:
            print(f"-> Self-Correction JSON Parse Error: {e}")
            return {}

    # -----------------------------------------------------------------
    # Branch B: Standard Sequential File Generation
    # -----------------------------------------------------------------
    if not tasks or idx >= len(tasks):
        return {}

    active_task = tasks[idx]
    filename = active_task["filename"]
    task_desc = active_task["task_description"]

    print(f"-> Generating component [{idx + 1}/{len(tasks)}]: {filename}...")
    programmer_prompt = (
        f"You are an expert Python engineer working on a multi-file project workspace.\n"
        f"Implement component '{filename}' based on this plan:\n"
        f"{task_desc}\n\n"
        f"Requirement: '{state['user_requirement']}'\n\n"
        f"CRITICAL CODING RULES:\n"
        f"1. For SQL or multi-line strings, ALWAYS use Python triple quotes (\"\"\"...\"\"\").\n"
        f"2. For interactive loops, wrap `input()` in `try ... except (EOFError, KeyboardInterrupt): break` so automated runners exit cleanly.\n"
        f"3. If you use argparse, ensure default values are provided for arguments.\n\n"
        f"Return ONLY raw Python code for this file without markdown wraps."
    )
    
    response = llm.invoke(programmer_prompt)
    
    updated_tasks = list(tasks)
    updated_tasks[idx] = ProjectTask(
        filename=filename, 
        task_description=task_desc, 
        generated_code=clean_extracted_code(response.content)
    )

    return {
        "tasks": updated_tasks,
        "current_task_index": idx + 1
    }