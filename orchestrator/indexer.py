"""
Neural Glass AI Orchestrator — Codebase Symbol Indexer
"""

import ast
from pathlib import Path
from typing import Dict, List, Any
from core.logger import log_event

SANDBOX_DIR = Path("workspace_sandbox")


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.symbols: List[Dict[str, Any]] = []
        self.imports: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            full_import = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full_import)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.symbols.append({
            "name": node.name,
            "type": "function",
            "line": node.lineno,
            "file": self.filepath,
            "args": [arg.arg for arg in node.args.args]
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.symbols.append({
            "name": node.name,
            "type": "class",
            "line": node.lineno,
            "file": self.filepath,
            "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        })
        self.generic_visit(node)


def index_workspace() -> Dict[str, Any]:
    """Scans all Python files in the sandbox and extracts symbols and import statements."""
    index_data = {"files": {}, "all_symbols": [], "total_files": 0}

    if not SANDBOX_DIR.exists():
        return index_data

    py_files = list(SANDBOX_DIR.rglob("*.py"))
    index_data["total_files"] = len(py_files)

    for file_path in py_files:
        rel_path = str(file_path.relative_to(SANDBOX_DIR)).replace("\\", "/")
        try:
            code = file_path.read_text(encoding="utf-8")
            tree = ast.parse(code, filename=rel_path)
            visitor = SymbolVisitor(rel_path)
            visitor.visit(tree)

            index_data["files"][rel_path] = {
                "symbols": visitor.symbols,
                "imports": visitor.imports
            }
            index_data["all_symbols"].extend(visitor.symbols)
        except Exception as e:
            log_event("symbol_index_error", file=rel_path, error=str(e), level="warning")

    log_event("workspace_indexed", files_count=len(py_files), symbols_count=len(index_data["all_symbols"]))
    return index_data