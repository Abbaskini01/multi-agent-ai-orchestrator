"""
Neural Glass AI Orchestrator — Specialized Executor Agent Node (V3 Enhanced)
Implements Tree-sitter AST, Hybrid RAG Context Retrieval, Self-Correction, and Diff Logging.
"""

import json
import tempfile
from pathlib import Path

from core.logger import log_event
from orchestrator.config import invoke_llm_with_fallback
from orchestrator.state import OrchestratorState, ProjectTask
from orchestrator.utils import clean_extracted_code, compute_git_diff
from orchestrator.context_engine import CodebaseContextEngine


def _build_temporary_v3_context(tasks: list, query: str) -> str:
    """
    Helper function: Writes generated tasks to a temporary workspace,
    indexes them via Tree-sitter + Qdrant, and retrieves surgical AST context.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write current generated files into temp dir for Tree-sitter indexing
            for t in tasks:
                if t.get("generated_code"):
                    file_path = Path(temp_dir) / t["filename"]
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(t["generated_code"], encoding="utf-8")
            
            # Run V3 CodebaseContextEngine on the temporary codebase
            engine = CodebaseContextEngine(temp_dir)
            summary = engine.index_codebase()
            if summary.get("indexed_chunks", 0) > 0:
                return engine.get_context_for_task(task_description=query, top_k=2)
    except Exception as e:
        log_event("v3_context_engine_warning", level="warning", error=str(e))
    return ""


def executor_node(state: OrchestratorState) -> dict:
    """Specialized Executor Agent (V3 Enhanced): Uses Tree-sitter AST & Hybrid Search for Context."""
    log_event("executor_node_activating", phase="Executor Node V3 Hybrid Context")
    
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", 0)

    # -----------------------------------------------------------------
    # Branch A: Multi-File Targeted Self-Correction Mode (V3 Hybrid RAG)
    # -----------------------------------------------------------------
    if error_message:
        log_event("self_correction_triggered", attempt=retry_count)
        
        # Retrieve AST Symbol Table & Hybrid RAG Context for the Error Trace
        v3_context = _build_temporary_v3_context(tasks, f"Fix error: {error_message}")

        codebase_context = ""
        for t in tasks:
            codebase_context += f"\nFile: {t['filename']}\n```python\n{t['generated_code']}\n```\n"

        fix_system_prompt = (
            "You are an expert Python engineer debugging a multi-file project workspace.\n"
            "Analyze the error trace log, the V3 AST Codebase Context, and the multi-file source code.\n\n"
            "CRITICAL JSON FORMATTING RULES:\n"
            "1. You MUST respond with a single, valid JSON object containing a key called 'files'.\n"
            "2. 'files' must be an array of objects, each having 'filename' and 'code' keys.\n"
            "3. STRICT JSON STRING FORMATTING: The 'code' property MUST be a standard JSON string enclosed in single double-quotes (\"). "
            "NEVER use Python triple quotes (\"\"\") to enclose the JSON string value for 'code'! "
            "Escape all double quotes inside the code as \\\" and represent newlines as standard \\n.\n\n"
            "CRITICAL PYTHON CODING RULES:\n"
            "1. SYMBOL ALIGNMENT: Match function and class signatures across files as defined in the AST Symbol Index.\n"
            "2. INTERACTIVE LOOPS: ALL interactive menu loops MUST support simple numeric options (1, 2, 3, 4...) and MUST wrap `input()` calls in a `try ... except (EOFError, KeyboardInterrupt): break` block so automated execution exits cleanly on EOF.\n"
            "3. MULTILINE STRINGS: For SQL queries or multi-line text, ALWAYS use Python triple quotes (\"\"\"...\"\"\").\n"
            "4. ARGPARSE TESTING: If writing `parse_args`, define it as `def parse_args(args=None): ... return parser.parse_args(args)`.\n"
            "5. SURGICAL REPAIR: Modify ONLY the specific file(s) causing the failure."
        )

        user_prompt = (
            f"Requirement: '{state['user_requirement']}'\n\n"
            f"Validation Failure Error Trace:\n"
            f"--------------------------------------------------\n"
            f"{error_message}\n"
            f"--------------------------------------------------\n\n"
        )

        if v3_context:
            user_prompt += (
                f"V3 AST & HYBRID RAG CODEBASE CONTEXT:\n"
                f"--------------------------------------------------\n"
                f"{v3_context}\n"
                f"--------------------------------------------------\n\n"
            )

        user_prompt += (
            f"Current Multi-File Codebase:\n"
            f"{codebase_context}\n\n"
            f"Identify the root cause, fix ONLY the affected file(s), and return valid JSON."
        )

        response = invoke_llm_with_fallback(
            [("system", fix_system_prompt), ("human", user_prompt)],
            response_format={"type": "json_object"}
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
                            old_code = t["generated_code"]
                            
                            diff_text = compute_git_diff(old_code, fcode, fname)
                            if diff_text:
                                log_event("git_patch_generated", filename=fname, diff=diff_text.strip())

                            updated_tasks[i] = ProjectTask(
                                filename=fname,
                                task_description=t["task_description"],
                                generated_code=fcode
                            )
                            repaired_filenames.append(fname)
            
            untouched_files = [t["filename"] for t in updated_tasks if t["filename"] not in repaired_filenames]
            log_event("targeted_repair_complete", repaired=repaired_filenames, untouched=untouched_files)
                        
            return {"tasks": updated_tasks}
        except Exception as e:
            log_event("self_correction_json_parse_error", error=str(e), level="error")
            return {}

    # -----------------------------------------------------------------
    # Branch B: Standard Sequential File Generation (V3 Context-Aware)
    # -----------------------------------------------------------------
    if not tasks or idx >= len(tasks):
        return {}

    active_task = tasks[idx]
    filename = active_task["filename"]
    task_desc = active_task["task_description"]

    # V3 Upgrade: Index previously generated components to ensure cross-file symbol alignment
    v3_prev_context = ""
    already_generated = [t for t in tasks[:idx] if t.get("generated_code")]
    if already_generated:
        v3_prev_context = _build_temporary_v3_context(already_generated, f"Implement {filename}: {task_desc}")

    log_event("generating_component", component_index=idx + 1, total_components=len(tasks), filename=filename)
    programmer_prompt = (
        f"You are an expert Python engineer working on a multi-file project workspace.\n"
        f"Implement component '{filename}' based on this plan:\n"
        f"{task_desc}\n\n"
        f"Requirement: '{state['user_requirement']}'\n\n"
    )

    if v3_prev_context:
        programmer_prompt += (
            f"V3 CONTEXT FROM PREVIOUSLY GENERATED MODULES:\n"
            f"--------------------------------------------------\n"
            f"{v3_prev_context}\n"
            f"--------------------------------------------------\n\n"
        )

    programmer_prompt += (
        f"CRITICAL CODING RULES:\n"
        f"1. For interactive loops, ALWAYS use simple numeric menu choices (1, 2, 3, 4...) and wrap `input()` in `try ... except (EOFError, KeyboardInterrupt): break` so automated runners exit cleanly.\n"
        f"2. If writing `parse_args`, ALWAYS define it as `def parse_args(args=None): ... return parser.parse_args(args)`.\n"
        f"3. For SQL queries, ALWAYS use Python triple quotes (\"\"\"...\"\"\").\n\n"
        f"Return ONLY raw Python code for this file without markdown wraps."
    )
    
    response = invoke_llm_with_fallback(programmer_prompt)
    
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