import subprocess
from pathlib import Path
from orchestrator.state import OrchestratorState
from orchestrator.utils import clean_extracted_code


def exporter_node(state: OrchestratorState) -> dict:
    """
    Filesystem Exporter Node:
    Exports verified multi-directory project to generated_projects/ folder and initializes Git.
    """
    print("\n[Node Activating] ---> Filesystem Exporter Node")
    proj_name = state.get("project_name", "GeneratedProject")
    tasks = state.get("tasks", [])
    
    # Base export path
    export_dir = Path("generated_projects") / proj_name.lower().replace(" ", "_")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"-> Exporting verified project to: '{export_dir.resolve()}'")
    
    for task in tasks:
        filename = task["filename"]
        code = clean_extracted_code(task.get("generated_code", ""))
        if code:
            file_path = export_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code, encoding="utf-8")
            print(f"   [+] Exported: {filename}")
            
    # Initialize Git repo in exported directory
    try:
        subprocess.run(["git", "init"], cwd=export_dir, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=export_dir, capture_output=True, check=True)
        retries = state.get("retry_count", 0)
        commit_msg = f"feat: initial verified build (self-repair iterations: {retries})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir, capture_output=True, check=True)
        print("-> Initializing local Git repository...")
        print(f"-> Success: Git repository initialized with commit message: '{commit_msg}'")
    except Exception as e:
        print(f"-> Warning: Could not initialize Git repository: {e}")

    return {}