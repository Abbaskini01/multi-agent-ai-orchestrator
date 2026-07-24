import sys
from orchestrator.graph import app as orchestrator_graph


def display_hitl_checkpoint(state: dict) -> str:
    """Renders the Version 2 Human-In-The-Loop Approval Checkpoint."""
    proj_name = state.get("project_name", "GeneratedApp")
    arch_pattern = state.get("architecture_pattern", "Layered Architecture")
    folders = state.get("folders", [])
    criteria = state.get("acceptance_criteria", [])
    tasks = state.get("tasks", [])

    print("\n==================================================")
    print("=== ⏸️  HUMAN-IN-THE-LOOP APPROVAL CHECKPOINT ===")
    print("==================================================")
    print(f"\n📦 PROJECT: {proj_name}")
    print(f"🏛️  ARCHITECTURE PATTERN: {arch_pattern}")

    print("\n📂 PROPOSED DIRECTORY SCAFFOLDING:")
    for f in folders:
        print(f"   📁 {f}/")

    print("\n📋 PROPOSED ACCEPTANCE CRITERIA:")
    for i, c in enumerate(criteria, 1):
        print(f"   {i}. {c}")

    print("\n📄 PROPOSED REPOSITORY FILE ARCHITECTURE:")
    for i, t in enumerate(tasks, 1):
        print(f"   {i}. {t['filename']} -> {t['task_description']}")

    print("\n--------------------------------------------------")
    print("Options:")
    print("   [A] Approve blueprint & proceed to Scaffolding & Code Generation")
    print("   [M] Modify blueprint (Provide custom feedback for Architect)")
    print("   [Q] Quit / Abort execution")
    print("--------------------------------------------------")
    
    try:
        choice = input("Enter choice ([A]/M/Q): ").strip().upper()
    except (EOFError, KeyboardInterrupt):
        choice = "Q"

    return choice if choice in ["A", "M", "Q"] else "A"


def main():
    print("====================================================")
    print("=== Launching V2 Repository AI Orchestrator      ===")
    print("====================================================")

    user_req = (
        "Build a minimal command-line Python expense tracker app. "
        "It must split into a database layout component and a main application driver loop file."
    )

    initial_state = {
        "user_requirement": user_req,
        "project_name": "",
        "architecture_pattern": "",
        "folders": [],
        "acceptance_criteria": [],
        "tasks": [],
        "current_task_index": 0,
        "error_message": "",
        "retry_count": 0,
        "human_feedback": "",
        "is_approved": False
    }

    # Run Planner to generate Blueprint
    config = {"configurable": {"thread_id": "session-v2-1"}}
    
    # Execute until HITL checkpoint
    state = orchestrator_graph.invoke(initial_state, config=config)

    # Interactive Approval Loop
    while not state.get("is_approved", False):
        choice = display_hitl_checkpoint(state)

        if choice == "A":
            print("\n-> Blueprint Approved by User! Resuming automated pipeline...")
            state["is_approved"] = True
            state["human_feedback"] = ""
            # Resume graph execution
            state = orchestrator_graph.invoke(state, config=config)
            break
        elif choice == "M":
            try:
                feedback = input("\nEnter custom instructions for the Architect Agent: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if feedback:
                state["human_feedback"] = feedback
                state["is_approved"] = False
                print("\n-> Re-routing to Architect Agent with custom feedback...")
                state = orchestrator_graph.invoke(state, config=config)
            else:
                print("-> No feedback provided. Keeping current blueprint.")
        elif choice == "Q":
            print("\n-> Execution aborted by user. Exiting cleanly.")
            sys.exit(0)

    print("\n=============================================")
    print("=== Graph Execution Finished: Final State ===")
    print("=============================================")


if __name__ == "__main__":
    main()