"""
Neural Glass AI Orchestrator — Enterprise Knowledge Graph Engine
"""

from typing import Dict, List, Any
from core.logger import log_event
from core.multi_repo import discover_workspace_projects
from orchestrator.indexer import index_workspace
from orchestrator.dep_graph import get_dependency_graph
from core.git import get_commit_history


def build_enterprise_knowledge_graph() -> Dict[str, Any]:
    """
    Synthesizes code symbols, cross-repo nodes, git commits, and dependency edges
    into a unified Enterprise Knowledge Graph.
    """
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    
    # 1. Index Projects
    projects = discover_workspace_projects()
    for proj in projects:
        nodes.append({
            "id": f"project:{proj['name']}",
            "label": proj["name"],
            "type": "Project",
            "metadata": {"type": proj["type"], "file_count": proj["file_count"]}
        })

    # 2. Index Code Symbols
    symbols_data = index_workspace()
    for sym in symbols_data.get("symbols", []):
        sym_id = f"symbol:{sym['file']}:{sym['name']}"
        nodes.append({
            "id": sym_id,
            "label": sym["name"],
            "type": sym.get("type", "Symbol"),
            "metadata": {"file": sym["file"], "line": sym.get("line", 1)}
        })
        
        # Connect symbol to project root
        edges.append({
            "source": sym_id,
            "target": "project:core-sandbox",
            "relation": "DEFINED_IN"
        })

    # 3. Add Dependency Edges
    dep_graph = get_dependency_graph()
    for edge in dep_graph.get("edges", []):
        edges.append({
            "source": f"module:{edge['source']}",
            "target": f"module:{edge['target']}",
            "relation": "IMPORTS"
        })

    # 4. Add Git Commit Context
    commits = get_commit_history()
    for c in commits[:5]:  # Top 5 recent commits
        c_id = f"commit:{c.get('hash', 'head')}"
        nodes.append({
            "id": c_id,
            "label": c.get("subject", "Commit"),
            "type": "Commit",
            "metadata": {"author": c.get("author", "Dev"), "date": c.get("date", "")}
        })

    log_event("knowledge_graph_built", total_nodes=len(nodes), total_edges=len(edges))
    
    return {
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges)
        },
        "nodes": nodes,
        "edges": edges
    }


def analyze_impact_radius(target_path_or_symbol: str) -> Dict[str, Any]:
    """
    Calculates the blast radius of a change to a specific file or symbol.
    """
    graph = build_enterprise_knowledge_graph()
    affected_nodes = []
    
    for edge in graph["edges"]:
        if target_path_or_symbol in edge["source"] or target_path_or_symbol in edge["target"]:
            affected_nodes.append(edge)

    return {
        "target": target_path_or_symbol,
        "impact_score": len(affected_nodes),
        "affected_relations": affected_nodes
    }