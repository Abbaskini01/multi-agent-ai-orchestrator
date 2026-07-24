import ast
from typing import Dict, List, Any


def parse_file_symbols(filename: str, code: str) -> Dict[str, Any]:
    """Parses Python source code into an AST and extracts defined symbols and imports."""
    symbols = {
        "filename": filename,
        "imports": [],
        "classes": [],
        "functions": []
    }

    try:
        tree = ast.parse(code, filename=filename)
    except SyntaxError:
        return symbols

    for node in ast.iter_child_nodes(tree):
        # Extract direct function definitions
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            symbols["functions"].append(f"{node.name}({', '.join(args)})")

        # Extract class definitions and their methods
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    margs = [a.arg for a in item.args.args]
                    methods.append(f"{item.name}({', '.join(margs)})")
            symbols["classes"].append({
                "class_name": node.name,
                "methods": methods
            })

        # Extract imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                symbols["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                symbols["imports"].append(f"from {module} import {alias.name}")

    return symbols


def build_codebase_symbol_map(tasks: List[Dict[str, Any]]) -> str:
    """Generates a structured, human-readable AST symbol map across all workspace files."""
    summary_lines = []

    for t in tasks:
        fname = t.get("filename", "")
        code = t.get("generated_code", "")
        if not fname or not code:
            continue

        syms = parse_file_symbols(fname, code)
        summary_lines.append(f"=== File: {fname} ===")

        if syms["imports"]:
            summary_lines.append(f"  Imports: {', '.join(syms['imports'])}")

        if syms["classes"]:
            for c in syms["classes"]:
                m_str = ", ".join(c["methods"]) if c["methods"] else "None"
                summary_lines.append(f"  Class `{c['class_name']}` -> Methods: [{m_str}]")

        if syms["functions"]:
            summary_lines.append(f"  Functions: {', '.join(syms['functions'])}")

        summary_lines.append("")

    return "\n".join(summary_lines)