from orchestrator.state import OrchestratorState


def human_approval_node(state: OrchestratorState) -> dict:
    """
    Phase 7: Human-in-the-Loop (HITL) Checkpoint
    Pauses execution to allow user approval, feedback modification, or abortion.
    """
    print("\n==================================================")
    print("=== ⏸️  HUMAN-IN-THE-LOOP APPROVAL CHECKPOINT ===")
    print("==================================================")

    criteria = state.get("acceptance_criteria", [])
    tasks = state.get("tasks", [])

    print("\n📋 PROPOSED ACCEPTANCE CRITERIA:")
    for idx, c in enumerate(criteria, 1):
        print(f"   {idx}. {c}")

    print("\n📂 PROPOSED FILE ARCHITECTURE:")
    for idx, t in enumerate(tasks, 1):
        print(f"   {idx}. {t['filename']} -> {t['task_description']}")

    print("\n--------------------------------------------------")
    print("Options:")
    print("   [A] Approve plan and proceed to Code Generation")
    print("   [M] Modify plan (Provide custom feedback for Planner)")
    print("   [Q] Quit / Abort execution")
    print("--------------------------------------------------")

    while True:
        try:
            choice = input("Enter choice ([A]/M/Q): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice in ["a", "approve", ""]:
            print("\n-> Plan Approved by User! Resuming automated pipeline...")
            return {"is_approved": True, "error_message": ""}

        elif choice in ["m", "modify"]:
            try:
                user_notes = input("\nEnter feedback/modifications for the Architect: ").strip()
            except (EOFError, KeyboardInterrupt):
                user_notes = ""

            print(f"\n-> Feedback recorded. Routing back to Planner Node...")
            return {"is_approved": False, "human_feedback": user_notes}

        elif choice in ["q", "quit", "abort"]:
            print("\n-> User aborted execution.")
            return {"is_approved": False, "error_message": "Execution canceled by user at HITL checkpoint."}

        else:
            print("Invalid selection. Please type 'A' to approve, 'M' to modify, or 'Q' to quit.")