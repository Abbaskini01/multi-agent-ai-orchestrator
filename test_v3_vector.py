import os
from orchestrator.code_graph import CodeGraphManager
from orchestrator.vector_store import VectorStoreManager

sample_repo = os.path.join("generated_projects", "expensetrackercli")

if os.path.exists(sample_repo):
    print("1. Building Code Graph...")
    graph_mgr = CodeGraphManager(sample_repo)
    graph_mgr.build_graph()

    print("2. Initializing Vector Store & Embedding AST Chunks...")
    vec_mgr = VectorStoreManager()
    total_indexed = vec_mgr.index_graph_chunks(graph_mgr)
    print(f"-> Successfully indexed {total_indexed} AST chunks into Qdrant Vector DB!\n")

    # Natural Language Semantic Queries
    queries = [
        "Where do we save new entries into SQLite database?",
        "How do we remove items from the database?",
        "Where is user input menu handled?"
    ]

    for q in queries:
        print(f"🔍 Natural Language Query: '{q}'")
        results = vec_mgr.search_similar_code(q, top_k=1)
        for res in results:
            print(f"   [Match Score: {res['score']}] File: {res['filepath']} | Symbol: {res['name']} ({res['type']})")
            print(f"   Code Snippet:\n   {res['code'].strip()}")
        print("-" * 60)
else:
    print(f"Path '{sample_repo}' not found.")