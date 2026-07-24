import re
import subprocess
from pathlib import Path
from orchestrator.state import OrchestratorState
from orchestrator.utils import clean_extracted_code


def filesystem_exporter_node(state: OrchestratorState) -> dict:
    """Phase 5 & 6: Writes verified files to disk, generates README.md & .gitignore, and runs git init."""
    print("\n[Node Activating] ---> Filesystem Exporter Node")
    
    tasks = state.get("tasks", [])
    user_req = state.get("user_requirement", "")
    criteria = state.get("acceptance_criteria", [])
    retries = state.get("retry_count", 0)

    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', user_req.lower())[:30].strip('_')
    if not clean_name:
        clean_name = "generated_app"
        
    export_dir = Path("generated_projects") / clean_name
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"-> Exporting verified project to: '{export_dir.resolve()}'")

    # 1. Export Python task files
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
    readme_content += f"\n## Verification Audit\n- Self-Repair Retries Required: `{retries}`\n"
    readme_content += "\n---\n*Generated and verified automatically by AI Multi-Agent Orchestrator.*"
    (export_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print("   [+] Generated: README.md")

    # 3. Generate .gitignore
    gitignore_content = "__pycache__/\n*.pyc\n*.db\n.env\nvenv/\n.vscode/\n"
    (export_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    print("   [+] Generated: .gitignore")

    # 4. Initialize Local Git Repository & Initial Commit
    try:
        print("-> Initializing local Git repository...")
        subprocess.run(["git", "init"], cwd=export_dir, capture_output=True, text=True, check=True)
        subprocess.run(["git", "add", "."], cwd=export_dir, capture_output=True, text=True, check=True)
        
        commit_msg = f"feat: initial verified build (self-repair iterations: {retries})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir, capture_output=True, text=True, check=True)
        print(f"-> Success: Git repository initialized with commit message: '{commit_msg}'")
    except Exception as git_err:
        print(f"-> Warning: Git initialization skipped or failed ({git_err}). Ensure Git is installed.")

    return {}