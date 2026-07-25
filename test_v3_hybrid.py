import os
from orchestrator.code_graph import CodeGraphManager
from orchestrator.vector_store import VectorStoreManager
from orchestrator.hybrid_search import HybridSearchManager

sample_repo = os.path.join("generated_projects", "expensetrackercli")

if os.path.exists(sample_repo):
    print("1. Building Code Graph...")
    graph_mgr = CodeGraphManager(sample_repo)
    graph_mgr.build_graph()

    print("2. Initializing Hybrid Search Engine (BM25 + Qdrant)...")
    vec_mgr = VectorStoreManager()
    hybrid_mgr = HybridSearchManager(vec_mgr)
    total_indexed = hybrid_mgr.index_corpus(graph_mgr)
    print(f"-> Indexed {total_indexed} AST chunks into Hybrid Engine!\n")

    # Test Queries: One exact keyword match & One natural language conceptual match
    queries = [
        "insert_expense",  # Exact symbol keyword test
        "Where do we calculate or delete costs?"  # Conceptual query test
    ]

    for q in queries:
        print(f"⚡ Hybrid Search Query: '{q}'")
        results = hybrid_mgr.search_hybrid(q, top_k=2)
        for res in results:
            print(f"   [RRF Score: {res['rrf_score']}] File: {res['filepath']} | Symbol: {res['name']}")
        print("-" * 60)
else:
    print(f"Path '{sample_repo}' not found.")