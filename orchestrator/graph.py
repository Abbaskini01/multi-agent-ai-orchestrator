"""
Neural Glass AI Orchestrator — LangGraph State Machine
======================================================

This module compiles the explicit agent graph: planner -> scaffolder ->
executor -> syntax_tester -> runtime_tester -> functional_tester -> exporter
-> notifier. Conditional edges send the state back to the executor when a
tester reports an error and retries remain (3 by default).

`app` is consumed by app.py, the interactive CLI harness. The web dashboard
drives orchestrator.pipeline directly, which is the same conceptual flow with
websocket telemetry attached.
"""

from langgraph.graph import StateGraph, END
from orchestrator.state import OrchestratorState
from orchestrator.planner import planner_node
from orchestrator.scaffolder import scaffolder_node
from orchestrator.executor import executor_node
from orchestrator.exporter import exporter_node
from orchestrator.notifier import notifier_node
from orchestrator.validators import (
    syntax_tester_node,
    runtime_tester_node,
    functional_tester_node,
)


def route_after_planner(state: OrchestratorState) -> str:
    """If blueprint is approved, move to Scaffolder. Otherwise pause at HITL checkpoint."""
    if state.get("is_approved", False):
        return "scaffolder"
    return END


def route_after_syntax(state: OrchestratorState) -> str:
    if state.get("error_message", ""):
        return "executor"
    return "runtime_tester"


def route_after_runtime(state: OrchestratorState) -> str:
    if state.get("error_message", ""):
        return "executor"
    return "functional_tester"


def route_after_functional(state: OrchestratorState) -> str:
    """If tests fail and retries remain, loop to Executor. If tests pass, route to Exporter."""
    error = state.get("error_message", "")
    retries = state.get("retry_count", 0)
    if error and retries < 3:
        return "executor"
    return "exporter"


# Define the LangGraph State Machine
workflow = StateGraph(OrchestratorState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("scaffolder", scaffolder_node)
workflow.add_node("executor", executor_node)
workflow.add_node("syntax_tester", syntax_tester_node)
workflow.add_node("runtime_tester", runtime_tester_node)
workflow.add_node("functional_tester", functional_tester_node)
workflow.add_node("exporter", exporter_node)
workflow.add_node("notifier", notifier_node)

# Flow Connections
workflow.set_entry_point("planner")

# After planning the graph pauses at END until a human sets is_approved.
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
    {"scaffolder": "scaffolder", END: END}
)

workflow.add_edge("scaffolder", "executor")
workflow.add_edge("executor", "syntax_tester")

workflow.add_conditional_edges(
    "syntax_tester",
    route_after_syntax,
    {"executor": "executor", "runtime_tester": "runtime_tester"}
)

workflow.add_conditional_edges(
    "runtime_tester",
    route_after_runtime,
    {"executor": "executor", "functional_tester": "functional_tester"}
)

# Loop guard: a failing functional run may re-enter the executor at most
# three times before the graph proceeds to export.
workflow.add_conditional_edges(
    "functional_tester",
    route_after_functional,
    {"executor": "executor", "exporter": "exporter"}
)

workflow.add_edge("exporter", "notifier")
workflow.add_edge("notifier", END)

# Export Compiled Graph App
app = workflow.compile()