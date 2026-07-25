import os
from orchestrator.context_engine import CodebaseContextEngine

sample_repo = os.path.join("generated_projects", "expensetrackercli")

if os.path.exists(sample_repo):
    print("🚀 Initializing Codebase Context Engine...")
    engine = CodebaseContextEngine(sample_repo)
    summary = engine.index_codebase()
    print(f"-> Codebase Indexing Complete: {summary}\n")

    # Simulate a realistic brownfield maintenance task
    task = "Add input validation for expense amount so negative numbers are rejected."
    print(f"🎯 Simulated AI Task: '{task}'")

    # Retrieve context for LLM prompt
    prompt_context = engine.get_context_for_task(
        task_description=task,
        target_symbols=["insert_expense"],
        top_k=2
    )

    print("\n" + "="*60)
    print("  GENERATED LLM PROMPT CONTEXT PAYLOAD")
    print("="*60)
    print(prompt_context)
else:
    print(f"Path '{sample_repo}' not found.")