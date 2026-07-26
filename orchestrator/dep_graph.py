"""
Neural Glass AI Orchestrator — Codebase Dependency Graph Engine
"""

from typing import Dict, List, Any
from orchestrator.indexer import index_workspace


class CodebaseDependencyGraph:
    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, str]] = []

    def build_graph(self) -> Dict[str, Any]:
        """Constructs an adjacency graph mapping import relationships between files."""
        index = index_workspace()
        self.nodes = []
        self.edges = []

        files = index.get("files", {})

        for file_path, file_data in files.items():
            self.nodes.append({
                "id": file_path, 
                "type": "file", 
                "symbol_count": len(file_data.get("symbols", []))
            })

            for imp in file_data.get("imports", []):
                possible_target = imp.replace(".", "/") + ".py"
                possible_target_alt = f"src/{possible_target}"

                target = None
                if possible_target in files:
                    target = possible_target
                elif possible_target_alt in files:
                    target = possible_target_alt

                if target:
                    self.edges.append({
                        "source": file_path,
                        "target": target,
                        "type": "imports"
                    })

        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "total_modules": len(self.nodes),
            "total_dependencies": len(self.edges)
        }


def get_dependency_graph() -> Dict[str, Any]:
    graph_builder = CodebaseDependencyGraph()
    return graph_builder.build_graph()