"""
Orchestrator Code Indexer (Version 3)
Uses Tree-sitter to parse source files across multiple languages (Python, JS, TS, Go, C++)
and extract semantic symbols (Functions, Classes, Imports) with exact byte ranges.
"""

from pathlib import Path
from typing import Dict, List, Any
from tree_sitter_languages import get_parser, get_language


class MultilingualCodeIndexer:
    def __init__(self):
        # File extension map to language grammars
        self.extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".go": "go",
            ".cpp": "cpp",
            ".c": "c",
        }

    def get_language_for_file(self, filepath: str) -> str:
        ext = Path(filepath).suffix.lower()
        return self.extension_map.get(ext, None)

    def parse_file(self, filepath: str, code_content: str = None) -> Dict[str, Any]:
        """
        Parses code string or file content into a structured semantic symbol dictionary.
        """
        lang_name = self.get_language_for_file(filepath)
        if not lang_name:
            return {"error": f"Unsupported file extension for '{filepath}'"}

        if code_content is None:
            path = Path(filepath)
            if not path.exists():
                return {"error": f"File '{filepath}' not found"}
            code_bytes = path.read_bytes()
        else:
            code_bytes = code_content.encode("utf-8")

        # Get language parser
        parser = get_parser(lang_name)
        tree = parser.parse(code_bytes)
        root = tree.root_node

        symbols = {
            "filepath": filepath,
            "language": lang_name,
            "has_errors": root.has_error,
            "functions": [],
            "classes": [],
            "imports": []
        }

        # Traverse the Syntax Tree recursively
        self._traverse_tree(root, code_bytes, symbols, lang_name)
        return symbols

    def _traverse_tree(self, node, code_bytes: bytes, symbols: Dict[str, Any], lang: str):
        """
        Recursively scans tree nodes to identify semantic entities based on grammar types.
        """
        # Node types vary slightly by language
        func_types = ["function_definition", "function_declaration", "method_definition", "arrow_function"]
        class_types = ["class_definition", "class_declaration"]
        import_types = ["import_statement", "import_from_statement", "import_declaration"]

        node_type = node.type

        if node_type in func_types:
            name_node = node.child_by_field_name("name")
            func_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "anonymous"
            symbols["functions"].append({
                "name": func_name,
                "start_point": node.start_point,
                "end_point": node.end_point,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
            })

        elif node_type in class_types:
            name_node = node.child_by_field_name("name")
            class_name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8") if name_node else "anonymous"
            symbols["classes"].append({
                "name": class_name,
                "start_point": node.start_point,
                "end_point": node.end_point,
                "start_byte": node.start_byte,
                "end_byte": node.end_byte,
            })

        elif node_type in import_types:
            import_str = code_bytes[node.start_byte:node.end_byte].decode("utf-8")
            symbols["imports"].append(import_str)

        # Recurse through child nodes
        for child in node.children:
            self._traverse_tree(child, code_bytes, symbols, lang)