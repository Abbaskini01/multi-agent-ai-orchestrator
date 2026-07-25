"""
Orchestrator Context Engine (Version 3)
Unifies Code Graph, Vector Store, and Hybrid Search into a single entry point.
Retrieves surgical AST code context to inject directly into LLM prompts.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from orchestrator.code_graph import CodeGraphManager
from orchestrator.vector_store import VectorStoreManager
from orchestrator.hybrid_search import HybridSearchManager


class CodebaseContextEngine:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.graph_manager = CodeGraphManager(root_dir)
        self.vector_manager = VectorStoreManager()
        self.hybrid_manager = HybridSearchManager(self.vector_manager)
        self.is_indexed = False

    def index_codebase(self) -> Dict[str, Any]:
        """
        Executes full indexing pipeline:
        1. AST parsing & symbol graph construction
        2. Vector embedding & Qdrant loading
        3. BM25 corpus tokenization
        """
        graph_summary = self.graph_manager.build_graph()
        indexed_chunks = self.hybrid_manager.index_corpus(self.graph_manager)
        self.is_indexed = True

        return {
            "indexed_files": graph_summary["indexed_files_count"],
            "total_symbols": graph_summary["total_symbols_count"],
            "indexed_chunks": indexed_chunks
        }

    def get_context_for_task(
        self, 
        task_description: str, 
        target_symbols: Optional[List[str]] = None, 
        top_k: int = 2
    ) -> str:
        """
        Generates a highly focused context payload for the Executor / LLM node.
        Combines exact symbol definitions + hybrid RAG retrieval.
        """
        if not self.is_indexed:
            self.index_codebase()

        context_sections = []

        # 1. Exact Symbol Lookups (if specific target symbols are provided)
        if target_symbols:
            context_sections.append("=== EXACT SYMBOL DEFINITIONS ===")
            for symbol in target_symbols:
                defs = self.graph_manager.find_definition(symbol)
                for d in defs:
                    context_sections.append(
                        f"• Symbol '{symbol}' defined in '{d['file']}' (Lines {d['start_point'][0]+1}-{d['end_point'][0]+1})"
                    )

        # 2. Hybrid RAG Context Chunks
        hybrid_results = self.hybrid_manager.search_hybrid(task_description, top_k=top_k)
        if hybrid_results:
            context_sections.append("\n=== RELEVANT CODE CONTEXT CHUNKS ===")
            for res in hybrid_results:
                context_sections.append(
                    f"--- File: {res['filepath']} | Symbol: {res['name']} (RRF Score: {res['rrf_score']}) ---\n"
                    f"{res['code']}\n"
                )

        return "\n".join(context_sections)