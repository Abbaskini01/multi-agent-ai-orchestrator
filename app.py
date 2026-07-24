import json
from langgraph.graph import StateGraph, START, END

from orchestrator.state import OrchestratorState
from orchestrator.planner import planner_node
from orchestrator.hitl import human_approval_node
from orchestrator.executor import executor_node
from orchestrator.validators import (
    syntax_tester_node,
    runtime_tester_node,
    functional_tester_node,
)
from orchestrator.exporter import filesystem_exporter_node
from orchestrator.notifier import notification_node
from orchestrator.router import (
    route_after_human_approval,
    route_after_executor,
    route_after_syntax,
    route_after_runtime,
    route_after_functional,
)

# Wire the LangGraph state graph
workflow = StateGraph(OrchestratorState)

# Register nodes
workflow.add_node("planner_agent", planner_node)
workflow.add_node("human_approval_agent", human_approval_node)
workflow.add_node("executor_agent", executor_node)
workflow.add_node("syntax_tester_agent", syntax_tester_node)
workflow.add_node("runtime_tester_agent", runtime_tester_node)
workflow.add_node("functional_tester_agent", functional_tester_node)
workflow.add_node("filesystem_exporter_agent", filesystem_exporter_node)
workflow.add_node("notification_agent", notification_node)

# Map linear edges
workflow.add_edge(START, "planner_agent")
workflow.add_edge("planner_agent", "human_approval_agent")
workflow.add_edge("filesystem_exporter_agent", "notification_agent")
workflow.add_edge("notification_agent", END)

# Map conditional routing switches
workflow.add_conditional_edges(
    "human_approval_agent",
    route_after_human_approval,
    {
        "executor_agent": "executor_agent",
        "planner_agent": "planner_agent",
        "notification_agent": "notification_agent"
    }
)
workflow.add_conditional_edges(
    "executor_agent",
    route_after_executor,
    {
        "executor_agent": "executor_agent",
        "syntax_tester_agent": "syntax_tester_agent"
    }
)
workflow.add_conditional_edges(
    "syntax_tester_agent",
    route_after_syntax,
    {
        "executor_agent": "executor_agent",
        "runtime_tester_agent": "runtime_tester_agent",
        "notification_agent": "notification_agent"
    }
)
workflow.add_conditional_edges(
    "runtime_tester_agent",
    route_after_runtime,
    {
        "executor_agent": "executor_agent",
        "functional_tester_agent": "functional_tester_agent",
        "notification_agent": "notification_agent"
    }
)
workflow.add_conditional_edges(
    "functional_tester_agent",
    route_after_functional,
    {
        "executor_agent": "executor_agent",
        "filesystem_exporter_agent": "filesystem_exporter_agent",
        "notification_agent": "notification_agent"
    }
)

orchestrator_app = workflow.compile()

if __name__ == "__main__":
    print("====================================================")
    print("=== Launching HITL-Enabled AI Orchestrator       ===")
    print("====================================================")

    initial_input = {
        "user_requirement": (
            "Build a minimal command-line Python expense tracker app. "
            "It must split into a database layout component and a main application driver loop file."
        ),
        "human_feedback": "",
        "is_approved": False
    }

    final_output_state = orchestrator_app.invoke(initial_input)

    print("\n=============================================")
    print("=== Graph Execution Finished: Final State ===")
    print("=============================================")
    print(json.dumps(final_output_state, indent=4))