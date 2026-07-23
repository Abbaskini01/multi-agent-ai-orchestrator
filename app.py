import os
import sys
import json
import re
import subprocess
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

# =====================================================================
# 1. ENVIRONMENT CONFIGURATION & MODEL INITIALIZATION
# =====================================================================
load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2
)


# =====================================================================
# 2. THE SHARED STATE SCHEMA
# =====================================================================
class ProjectTask(TypedDict):
    filename: str          # Name of the target file (e.g., 'database.py')
    task_description: str  # Low-level coding blueprints for this specific file
    generated_code: str    # Filled downstream by Executor workers


class OrchestratorState(TypedDict):
    user_requirement: str          # Original instruction passed into the system
    acceptance_criteria: list[str] # Functional goals from Planner
    tasks: list[ProjectTask]        # Structured task array decomposed by the architect
    current_task_index: int        # Tracks sequential execution loop
    error_message: str             # Catches syntax, runtime, or functional assertion errors
    retry_count: int               # Circuit breaker iteration counter


# =====================================================================
# 3. CORE UTILITIES & COMMUNICATIONS
# =====================================================================
def send_telegram_message(message: str) -> bool:
    """Sends a direct text alert to Telegram with plain-text fallback."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("[Error] Missing Telegram environment credentials in .env file.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload_markdown = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    data_markdown = urllib.parse.urlencode(payload_markdown).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data_markdown, method="POST")
        with urllib.request.urlopen(req) as response:
            return response.status == 200
    except Exception:
        clean_text = message.replace("*", "").replace("`", "").replace("_", "")
        payload_plain = {"chat_id": chat_id, "text": clean_text}
        data_plain = urllib.parse.urlencode(payload_plain).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=data_plain, method="POST")
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as fallback_err:
            print(f"-> Failed to send Telegram alert: {fallback_err}")
            return False


def clean_extracted_code(output_text: str) -> str:
    """Isolates raw Python code from markdown wraps."""
    python_block_match = re.search(r"```python\s*(.*?)\s*```", output_text, re.DOTALL)
    if python_block_match:
        return python_block_match.group(1)
    
    generic_block_match = re.search(r"```\s*(.*?)\s*```", output_text, re.DOTALL)
    if generic_block_match:
        return generic_block_match.group(1)
        
    return output_text.strip()


# =====================================================================
# 4. AGENT NODE DEFINITIONS
# =====================================================================
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
        "1. Provide default values or optional flags for CLI arguments.\n"
        "2. Handle EOFError gracefully in interactive input loops."
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


def executor_node(state: OrchestratorState) -> dict:
    """Specialized Executor Agent: Generates initial files or performs targeted repairs."""
    print("\n[Node Activating] ---> Executor Node")
    
    error_message = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    tasks = state.get("tasks", [])
    idx = state.get("current_task_index", 0)

    # Branch A: Targeted Self-Correction
    if error_message:
        print(f"-> Self-Correction Triggered (Attempt #{retry_count}). Analyzing for targeted repair...")
        codebase_context = ""
        for t in tasks:
            codebase_context += f"\nFile: {t['filename']}\n```python\n{t['generated_code']}\n```\n"

        fix_system_prompt = (
            "You are an expert Python engineer. Analyze the error trace and codebase context.\n"
            "Respond with JSON key 'files' containing an array of objects with 'filename' and 'code'.\n"
            "TARGETED REPAIR RULE: Modify ONLY the specific file(s) causing the failure."
        )

        user_prompt = (
            f"Requirement: '{state['user_requirement']}'\n\n"
            f"Error Trace:\n{error_message}\n\n"
            f"Codebase Context:\n{codebase_context}\n\n"
            f"Fix ONLY the affected file(s) and return in structured JSON format."
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
            print(f"-> Targeted Repair Complete. Repaired: {repaired_filenames} | Preserved: {untouched_files}")
            return {"tasks": updated_tasks}
        except Exception as e:
            print(f"-> Self-Correction Parse Error: {e}")
            return {}

    # Branch B: Standard Sequential Generation
    if not tasks or idx >= len(tasks):
        return {}

    active_task = tasks[idx]
    filename = active_task["filename"]
    task_desc = active_task["task_description"]

    print(f"-> Generating component [{idx + 1}/{len(tasks)}]: {filename}...")
    programmer_prompt = (
        f"Implement component '{filename}' based on this plan:\n{task_desc}\n\n"
        f"Requirement: '{state['user_requirement']}'\n\n"
        f"Return ONLY raw Python code. Do not include markdown wraps."
    )
    
    response = llm.invoke(programmer_prompt)
    
    updated_tasks = list(tasks)
    updated_tasks[idx] = ProjectTask(
        filename=filename, 
        task_description=task_desc, 
        generated_code=clean_extracted_code(response.content)
    )

    return {"tasks": updated_tasks, "current_task_index": idx + 1}


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
        "Generate an executable `unittest` script named `test_suite.py` that validates the code against acceptance criteria.\n"
        "STRICT RULES:\n"
        "1. Test backend data methods directly. Do NOT assert on print stdout.\n"
        "2. Do NOT call main driver loops.\n"
        "3. Wrap CLI argparse exit checks in `with self.assertRaises(SystemExit):`.\n"
        "Return ONLY raw Python code.\n\n"
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


def filesystem_exporter_node(state: OrchestratorState) -> dict:
    """
    Phase 5: Filesystem Exporter Node
    Writes verified files to disk, generates README.md & .gitignore, and runs git init.
    """
    print("\n[Node Activating] ---> Filesystem Exporter Node")
    
    tasks = state.get("tasks", [])
    user_req = state.get("user_requirement", "")
    criteria = state.get("acceptance_criteria", [])

    # Create a clean folder slug from requirement
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', user_req.lower())[:30].strip('_')
    if not clean_name:
        clean_name = "generated_app"
        
    export_dir = Path("generated_projects") / clean_name
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"-> Exporting verified project to: '{export_dir.resolve()}'")

    # 1. Export all Python task files
    for task in tasks:
        fname = task["filename"]
        code = clean_extracted_code(task["generated_code"])
        (export_dir / fname).write_text(code, encoding="utf-8")
        print(f"   [+] Exported: {fname}")

    # 2. Generate README.md
    readme_content = f"# {clean_name.replace('_', ' ').title()}\n\n"
    readme_content += f"## Requirement\n{user_req}\n\n"
    readme_content += "## Acceptance Criteria\n"
    for c in criteria:
        readme_content += f"- {c}\n"
    readme_content += "\n---\n*Generated and verified automatically by AI Multi-Agent Orchestrator.*"
    (export_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print("   [+] Generated: README.md")

    # 3. Generate .gitignore
    gitignore_content = "__pycache__/\n*.pyc\n*.db\n.env\nvenv/\n.vscode/\n"
    (export_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    print("   [+] Generated: .gitignore")

    # 4. Initialize local Git repository (Pillar 1)
    try:
        print("-> Initializing local Git repository...")
        subprocess.run(["git", "init"], cwd=export_dir, capture_output=True, text=True, check=True)
        subprocess.run(["git", "add", "."], cwd=export_dir, capture_output=True, text=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: initial verified commit by AI orchestrator"],
            cwd=export_dir, capture_output=True, text=True, check=True
        )
        print("-> Success: Git repository initialized with initial commit!")
    except Exception as git_err:
        print(f"-> Warning: Git initialization skipped or failed ({git_err}). Ensure Git is installed.")

    return {}


def notification_node(state: OrchestratorState) -> dict:
    """Notification Agent: Sends final status report via Telegram."""
    print("\n[Node Activating] ---> Notification Node")
    
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    tasks = state.get("tasks", [])
    
    if not error:
        file_list_str = "\n".join([f"• `{t['filename']}`" for t in tasks])
        alert_text = (
            f"✅ *Project Exported & Verified!*\n\n"
            f"*Requirement:* {state['user_requirement']}\n\n"
            f"*Generated Files:*\n{file_list_str}\n"
            f"• `README.md`\n• `.gitignore`\n\n"
            f"*Git Repository:* Initialized & Committed\n"
            f"*Total Retries Required:* {retries}"
        )
    else:
        alert_text = (
            f"❌ *Orchestration Aborted!*\n\n"
            f"*Requirement:* {state['user_requirement']}\n\n"
            f"*Last Logged Exception:*\n```\n{error}\n```"
        )
        
    print("-> Pinging outbound mobile notification stream...")
    send_telegram_message(alert_text)
    return {}


# =====================================================================
# 5. CONDITIONAL SWITCH ROUTERS & GRAPH PIPELINE WIRING
# =====================================================================
def route_after_executor(state: OrchestratorState) -> str:
    idx = state.get("current_task_index", 0)
    tasks = state.get("tasks", [])
    error = state.get("error_message", "")

    if error:
        return "syntax_tester_agent"
    if idx < len(tasks):
        return "executor_agent"
    return "syntax_tester_agent"


def route_after_syntax(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    
    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"
    return "runtime_tester_agent"


def route_after_runtime(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    
    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"
    return "functional_tester_agent"


def route_after_functional(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    
    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"
        
    print("\n[Routing Decision] -> All tests passed! Forwarding to Filesystem Exporter Node...")
    return "filesystem_exporter_agent"


# Define graph wiring paths
workflow = StateGraph(OrchestratorState)

# Register nodes
workflow.add_node("planner_agent", planner_node)
workflow.add_node("executor_agent", executor_node)
workflow.add_node("syntax_tester_agent", syntax_tester_node)
workflow.add_node("runtime_tester_agent", runtime_tester_node)
workflow.add_node("functional_tester_agent", functional_tester_node)
workflow.add_node("filesystem_exporter_agent", filesystem_exporter_node)
workflow.add_node("notification_agent", notification_node)

# Map edge connections
workflow.add_edge(START, "planner_agent")
workflow.add_edge("planner_agent", "executor_agent")
workflow.add_edge("filesystem_exporter_agent", "notification_agent")
workflow.add_edge("notification_agent", END)

# Connect conditional switches
workflow.add_conditional_edges("executor_agent", route_after_executor, {"executor_agent": "executor_agent", "syntax_tester_agent": "syntax_tester_agent"})
workflow.add_conditional_edges("syntax_tester_agent", route_after_syntax, {"executor_agent": "executor_agent", "runtime_tester_agent": "runtime_tester_agent", "notification_agent": "notification_agent"})
workflow.add_conditional_edges("runtime_tester_agent", route_after_runtime, {"executor_agent": "executor_agent", "functional_tester_agent": "functional_tester_agent", "notification_agent": "notification_agent"})
workflow.add_conditional_edges("functional_tester_agent", route_after_functional, {"executor_agent": "executor_agent", "filesystem_exporter_agent": "filesystem_exporter_agent", "notification_agent": "notification_agent"})

orchestrator_app = workflow.compile()


# =====================================================================
# 6. RUNTIME DECOMPOSITION VERIFICATION TEST
# =====================================================================
if __name__ == "__main__":
    print("====================================================")
    print("=== Launching Phase 5 Persistent Exporter Graph  ===")
    print("====================================================")
    
    initial_input = {
        "user_requirement": (
            "Build a minimal command-line Python expense tracker app. "
            "It must split into a database layout component and a main application driver loop file."
        )
    }
    
    final_output_state = orchestrator_app.invoke(initial_input)
    
    print("\n=============================================")
    print("=== Graph Execution Finished: Final State ===")
    print("=============================================")
    print(json.dumps(final_output_state, indent=4))