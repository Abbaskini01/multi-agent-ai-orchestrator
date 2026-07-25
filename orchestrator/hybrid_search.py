"""
Orchestrator Hybrid Search Manager (Version 3)
Combines Sparse BM25 Keyword Retrieval + Dense Qdrant Vector Search using Reciprocal Rank Fusion (RRF).
"""

from typing import Dict, List, Any
from rank_bm25 import BM25Okapi
from orchestrator.vector_store import VectorStoreManager


class HybridSearchManager:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.bm25: BM25Okapi = None
        self.corpus_chunks: List[Dict[str, Any]] = []

    def index_corpus(self, graph_manager) -> int:
        """
        Indexes all AST code chunks into both BM25 and the Vector Store.
        """
        # 1. First index into Qdrant Vector Store
        indexed_count = self.vector_store.index_graph_chunks(graph_manager)

        # 2. Extract corpus chunks for BM25 keyword index
        self.corpus_chunks = []
        tokenized_corpus = []

        for rel_path, file_data in graph_manager.file_map.items():
            abs_path = graph_manager.root_dir / rel_path
            if not abs_path.exists():
                continue

            code_bytes = abs_path.read_bytes()

            # Process Functions
            for func in file_data.get("functions", []):
                chunk_text = code_bytes[func["start_byte"]:func["end_byte"]].decode("utf-8", errors="ignore")
                doc_payload = {
                    "filepath": rel_path,
                    "type": "function",
                    "name": func["name"],
                    "code": chunk_text
                }
                self.corpus_chunks.append(doc_payload)
                # Tokenize function name, filepath, and code content for BM25
                tokens = f"{rel_path} {func['name']} {chunk_text}".lower().split()
                tokenized_corpus.append(tokens)

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

        return indexed_count

    def search_hybrid(self, query: str, top_k: int = 3, k_rrf: int = 60) -> List[Dict[str, Any]]:
        """
        Executes Hybrid Retrieval combining BM25 and Vector Search using Reciprocal Rank Fusion (RRF).
        RRF Score Formula: Score(doc) = 1 / (60 + rank_bm25) + 1 / (60 + rank_vector)
        """
        # 1. Vector Search Results
        vector_res = self.vector_store.search_similar_code(query, top_k=top_k * 2)

        # 2. BM25 Search Results
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query) if self.bm25 else []
        
        # Rank BM25 results
        ranked_bm25_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k * 2]

        # 3. Reciprocal Rank Fusion (RRF) Reranking
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # Process Vector Ranks
        for rank, item in enumerate(vector_res):
            key = f"{item['filepath']}::{item['name']}"
            chunk_map[key] = item
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k_rrf + (rank + 1)))

        # Process BM25 Ranks
        for rank, idx in enumerate(ranked_bm25_indices):
            if idx < len(self.corpus_chunks):
                item = self.corpus_chunks[idx]
                key = f"{item['filepath']}::{item['name']}"
                if key not in chunk_map:
                    chunk_map[key] = item
                rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k_rrf + (rank + 1)))

        # Sort combined results by RRF score
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]

        final_results = []
        for key in sorted_keys:
            chunk = chunk_map[key]
            final_results.append({
                "rrf_score": round(rrf_scores[key], 5),
                "filepath": chunk["filepath"],
                "name": chunk["name"],
                "type": chunk.get("type", "code"),
                "code": chunk["code"]
            })

        return final_results