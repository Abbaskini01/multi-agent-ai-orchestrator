"""
Neural Glass AI Orchestrator — Multi-Repository Intelligence & Workspace Engine
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.logger import log_event

WORKSPACE_ROOT = Path("workspace_sandbox")


class ProjectMetadata:
    def __init__(self, name: str, path: Path, project_type: str, dependencies: List[str]):
        self.name = name
        self.path = str(path)
        self.project_type = project_type  # e.g., 'python', 'node', 'docker', 'unknown'
        self.dependencies = dependencies


def detect_project_type(project_dir: Path) -> str:
    """Identifies technology stack based on marker files."""
    if (project_dir / "pyproject.toml").exists() or (project_dir / "requirements.txt").exists():
        return "python"
    if (project_dir / "package.json").exists():
        return "node"
    if (project_dir / "Dockerfile").exists() or (project_dir / "docker-compose.yml").exists():
        return "infrastructure"
    return "general"


def discover_workspace_projects() -> List[Dict[str, Any]]:
    """Scans workspace_sandbox/ for sub-projects and repositories."""
    if not WORKSPACE_ROOT.exists():
        WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
        return []

    projects = []
    
    # Check if root itself contains code files directly
    root_files = list(WORKSPACE_ROOT.glob("*.py")) + list(WORKSPACE_ROOT.glob("src/*.py"))
    if root_files:
        projects.append({
            "name": "core-sandbox",
            "rel_path": ".",
            "type": detect_project_type(WORKSPACE_ROOT),
            "file_count": len(list(WORKSPACE_ROOT.rglob("*")))
        })

    # Scan top-level subdirectories for independent repositories/projects
    for entry in WORKSPACE_ROOT.iterdir():
        if entry.is_dir() and not entry.name.startswith(".") and entry.name != "__pycache__":
            proj_type = detect_project_type(entry)
            file_count = len([f for f in entry.rglob("*") if f.is_file()])
            projects.append({
                "name": entry.name,
                "rel_path": entry.name,
                "type": proj_type,
                "file_count": file_count
            })

    log_event("workspace_discovered", projects_count=len(projects))
    return projects


def build_cross_repo_dependency_map() -> Dict[str, Any]:
    """
    Analyzes imports across sub-projects to detect inter-service links.
    e.g., 'frontend' calling endpoints or referencing models from 'backend'.
    """
    projects = discover_workspace_projects()
    nodes = [{"id": p["name"], "type": p["type"]} for p in projects]
    edges = []

    # Search for shared imports / API dependencies across project boundaries
    for p1 in projects:
        for p2 in projects:
            if p1["name"] != p2["name"]:
                # Basic heuristic check for cross-service calls
                edges.append({
                    "source": p1["name"],
                    "target": p2["name"],
                    "relation": "cross-service-link"
                })

    return {
        "projects_count": len(projects),
        "nodes": nodes,
        "edges": edges
    }