from orchestrator.state import OrchestratorState


def route_after_human_approval(state: OrchestratorState) -> str:
    """Phase 7: Decision switch following Human Approval Checkpoint."""
    error = state.get("error_message", "")
    is_approved = state.get("is_approved", False)

    if error:
        return "notification_agent"
    if is_approved:
        return "executor_agent"
    return "planner_agent"  # Route back for re-planning with user feedback


def route_after_executor(state: OrchestratorState) -> str:
    idx = state.get("current_task_index", 0)
    tasks = state.get("tasks", [])
    error = state.get("error_message", "")

    if error:
        return "syntax_tester_agent"
    if idx < len(tasks):
        return "executor_agent"
    return "syntax_tester_agent"


def route_after_syntax(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)

    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"
    return "runtime_tester_agent"


def route_after_runtime(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)

    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"
    return "functional_tester_agent"


def route_after_functional(state: OrchestratorState) -> str:
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)

    if error:
        return "notification_agent" if retries >= 3 else "executor_agent"

    print("\n[Routing Decision] -> All tests passed! Forwarding to Filesystem Exporter Node...")
    return "filesystem_exporter_agent"