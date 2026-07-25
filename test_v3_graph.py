import os
from orchestrator.code_graph import CodeGraphManager

# Run graph manager against our generated project export
sample_repo = os.path.join("generated_projects", "expensetrackercli")

if os.path.exists(sample_repo):
    print(f"=== Building Code Graph for: {sample_repo} ===")
    graph_mgr = CodeGraphManager(sample_repo)
    summary = graph_mgr.build_graph()
    print(f"Summary: {summary}")

    # Query definitions across files
    print("\n--- Querying Symbol: 'create_table' ---")
    print(graph_mgr.find_definition("create_table"))

    print("\n--- Querying Symbol: 'main' ---")
    print(graph_mgr.find_definition("main"))
else:
    print(f"Path '{sample_repo}' not found. Please verify folder location.")