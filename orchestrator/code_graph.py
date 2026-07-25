"""
Orchestrator Code Graph (Version 3)
Builds a global symbol reference graph across an entire multi-directory codebase.
Tracks definitions (DEF), import statements, and references (REF) across files.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from orchestrator.code_indexer import MultilingualCodeIndexer


class CodeGraphManager:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.indexer = MultilingualCodeIndexer()
        # Symbol Table: maps 'symbol_name' -> list of file definitions/locations
        self.symbol_table: Dict[str, List[Dict[str, Any]]] = {}
        # File Map: stores AST metadata for each file in repository
        self.file_map: Dict[str, Dict[str, Any]] = {}

    def build_graph(self) -> Dict[str, Any]:
        """
        Scans all supported source files in root_dir and constructs global symbol map.
        """
        self.symbol_table.clear()
        self.file_map.clear()

        # Iterate over all files in root_dir
        for path in self.root_dir.rglob("*"):
            if path.is_file() and self.indexer.get_language_for_file(str(path)):
                rel_path = str(path.relative_to(self.root_dir)).replace("\\", "/")
                
                # Parse single file via Tree-sitter
                parsed = self.indexer.parse_file(str(path))
                if "error" in parsed:
                    continue

                self.file_map[rel_path] = parsed

                # Register Function Definitions into Global Symbol Table
                for func in parsed.get("functions", []):
                    name = func["name"]
                    if name not in self.symbol_table:
                        self.symbol_table[name] = []
                    
                    self.symbol_table[name].append({
                        "file": rel_path,
                        "type": "function",
                        "start_point": func["start_point"],
                        "end_point": func["end_point"]
                    })

                # Register Class Definitions into Global Symbol Table
                for cls in parsed.get("classes", []):
                    name = cls["name"]
                    if name not in self.symbol_table:
                        self.symbol_table[name] = []
                    
                    self.symbol_table[name].append({
                        "file": rel_path,
                        "type": "class",
                        "start_point": cls["start_point"],
                        "end_point": cls["end_point"]
                    })

        return {
            "indexed_files_count": len(self.file_map),
            "total_symbols_count": len(self.symbol_table)
        }

    def find_definition(self, symbol_name: str) -> List[Dict[str, Any]]:
        """
        Finds where a function or class is defined across the repository (SCIP / LSIF pattern).
        """
        return self.symbol_table.get(symbol_name, [])