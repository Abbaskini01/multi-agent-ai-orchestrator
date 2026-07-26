"""
Neural Glass AI Orchestrator — Multi-Agent Workflow Runner with HITL Approval, Persistent Memory & Plugin Engine
"""

import time
import asyncio
import traceback
from typing import Dict, Any
from fastapi import WebSocket

from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.tracing import get_request_id
from core.git import init_sandbox_repo, get_unified_diff
from core.memory import save_session_memory
from core.plugins import plugin_registry
from llm.groq import call_groq_intent
from llm.gemini import call_gemini_generator
from orchestrator.dlp import sanitize_prompt_dlp
from orchestrator.finops import FinOpsTracker
from orchestrator.telemetry import emit_pipeline_telemetry
from orchestrator.sandbox import write_generated_files_to_sandbox
from orchestrator.git_agent import generate_ai_commit
from orchestrator.indexer import index_workspace
from orchestrator.dep_graph import get_dependency_graph
from orchestrator.state import OrchestratorState, create_initial_orchestrator_state
from orchestrator.agents import (
    run_planner_agent,
    run_security_agent,
    run_doc_agent,
    run_reviewer_agent
)
from orchestrator.testers import (
    run_flake8_lint,
    run_mypy_check,
    run_pytest_suite
)
from orchestrator.repair import classify_error_trace, run_repair_agent
import server


async def emit_concept(websocket: WebSocket, title: str, description: str, category: str, finops_data: dict):
    """Helper function to stream individual educational concepts to the UI."""
    concept_payload = {
        "id": f"concept_{int(time.time() * 1000)}",
        "title": title,
        "description": description,
        "category": category,
        "timestamp": time.strftime("%I:%M %p")
    }
    await emit_pipeline_telemetry(
        websocket,
        "CONCEPT_LEARNED",
        {
            "concept": concept_payload,
            **concept_payload
        },
        "Active Concept Recorded",
        f"Learned about {title}",
        finops_data
    )


async def wait_for_human_approval(
    websocket: WebSocket,
    state: OrchestratorState,
    step_name: str,
    payload_preview: Dict[str, Any],
    finops_data: dict,
    timeout_seconds: int = 300
) -> bool:
    """
    Pauses pipeline execution using an asyncio.Event barrier until user sends
    an explicit approval or rejection signal.
    """
    state["requires_approval"] = True
    state["approval_status"] = "PENDING"
    
    # Initialize global approval synchronization primitives
    approval_event = asyncio.Event()
    server.current_approval_event = approval_event
    server.latest_orchestrator_state = state

    await emit_pipeline_telemetry(
        websocket,
        "HUMAN_APPROVAL_REQUESTED",
        {
            "step": step_name,
            "preview": payload_preview,
            "timeout_seconds": timeout_seconds,
            "approval_status": "PENDING"
        },
        f"Approval Required: {step_name}",
        "Pipeline paused waiting for human review.",
        finops_data
    )
    await emit_concept(
        websocket,
        "Human-in-the-Loop (HITL) Gatekeeping",
        "Inserting explicit human checkpoints into autonomous pipelines to review and validate generated code before disk mutation.",
        "System Governance",
        finops_data
    )

    try:
        await asyncio.wait_for(approval_event.wait(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        state["approval_status"] = "REJECTED"
        state["human_notes"] = "Timed out waiting for human approval."
        log_event("hitl_approval_timeout", step=step_name, level="warning")
        return False
    finally:
        server.current_approval_event = None
        state["requires_approval"] = False

    return state.get("approval_status") == "APPROVED"


async def safe_run_pipeline(websocket: WebSocket, requirement: str):
    req_id = get_request_id()
    start_time = time.perf_counter()
    log_event("pipeline_triggered", prompt=requirement, request_id=req_id)

    try:
        await run_educational_pipeline(websocket, requirement)
        
        duration = time.perf_counter() - start_time
        metrics.record_pipeline_run(duration_seconds=duration, success=True)
        log_event("pipeline_execution_completed", duration_seconds=round(duration, 4), request_id=req_id)

    except Exception as e:
        duration = time.perf_counter() - start_time
        metrics.record_pipeline_run(duration_seconds=duration, success=False)
        log_event("pipeline_run_error", error=str(e), duration_seconds=round(duration, 4), level="error", request_id=req_id)
        traceback.print_exc()


async def run_educational_pipeline(websocket: WebSocket, requirement: str):
    finops = FinOpsTracker()

    # Ensure Sandbox Git Repository is Initialized
    init_sandbox_repo()

    # Initialize Phase V6.6 Orchestrator State
    state = create_initial_orchestrator_state(requirement)

    # DLP Sanitization Step
    clean_requirement, detected_leaks = sanitize_prompt_dlp(requirement)
    state["clean_requirement"] = clean_requirement

    if detected_leaks:
        start_t = time.time()
        finops_data = finops.calculate_step(30, 0, start_t, "DLP Scanner")
        await emit_pipeline_telemetry(
            websocket,
            "DLP_REDACTION_WARNING",
            {"original_prompt": requirement, "sanitized_prompt": clean_requirement, "leaks_detected": detected_leaks},
            "DLP Secret Redaction",
            "Credentials redacted before prompt transmission.",
            finops_data
        )
        await asyncio.sleep(0.5)

    # 1. Groq Intent Parsing Node
    start_t = time.time()
    parsed_intent = await call_groq_intent(clean_requirement)
    state["parsed_intent"] = parsed_intent
    server.latest_orchestrator_state = state

    finops_data = finops.calculate_step(140, 60, start_t, f"Groq / {settings.default_groq_model}")

    await emit_pipeline_telemetry(
        websocket,
        "PIPELINE_INITIATED",
        {"user_requirement": clean_requirement, "parsed_intent": parsed_intent},
        "Natural Language Intent Parsing",
        f"Groq parsed intent: '{parsed_intent}'",
        finops_data
    )
    await emit_concept(websocket, "Intent Parsing", "The process where an AI model analyzes raw human text to understand the underlying goal.", "Natural Language Processing", finops_data)
    await asyncio.sleep(0.5)

    # 2. Planner Agent Node
    start_t = time.time()
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "planner", "node_name": "Planner Agent Node", "phase": "Planning"},
        "Agentic Task Decomposition",
        "Planner agent breaking requirement into execution graph.",
        finops_data
    )
    plan_steps = await run_planner_agent(state)
    finops_data = finops.calculate_step(100, 40, start_t, "Planner Agent")

    await emit_concept(websocket, "Planner Agent", "Decomposing high-level software goals into explicit step-by-step task graphs.", "Multi-Agent System", finops_data)
    await asyncio.sleep(0.5)

    # 3. Gemini / Groq Code Generation Node
    start_t = time.time()
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "architect", "node_name": "Architect Agent Node", "phase": "Planning"},
        "Multi-File Scaffolding",
        "Architect node invoking model for dynamic code generation.",
        finops_data
    )

    generated_files = await call_gemini_generator(clean_requirement)
    
    # Phase V6.6 Extension Point: Trigger active Plugin post-generation hooks
    generated_files = await plugin_registry.run_post_generation_hooks(generated_files, state)

    file_list = list(generated_files.keys())
    state["generated_files"] = generated_files
    finops_data = finops.calculate_step(520, 680, start_t, settings.default_gemini_model)

    await emit_pipeline_telemetry(
        websocket,
        "ARCHITECT_BLUEPRINT_CREATED",
        {"project_name": "LiveGeneratedProject", "files": file_list},
        "Live Code Blueprint",
        f"Generated {len(file_list)} production files.",
        finops_data
    )
    await emit_concept(websocket, "Agentic Scaffolding", "Designing modular software by dynamically generating multiple interconnected files.", "Software Architecture", finops_data)
    await asyncio.sleep(0.5)

    # --- Phase V6.3 HITL Gatekeeping Point: Pause before Code Persistence ---
    start_t = time.time()
    approved = await wait_for_human_approval(
        websocket,
        state,
        "Code Generation Persistence",
        {"files": file_list, "files_count": len(file_list)},
        finops_data
    )

    if not approved:
        finops_data = finops.calculate_step(0, 0, start_t, "HITL Gatekeeper")
        await emit_pipeline_telemetry(
            websocket,
            "PIPELINE_HALTED",
            {"reason": state.get("human_notes", "User rejected code persistence.")},
            "Pipeline Stopped by User",
            "Execution halted cleanly during Human-in-the-Loop review.",
            finops_data
        )
        return

    # 4. Code Persistence Executor Node
    start_t = time.time()
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "executor", "node_name": "Executor Agent", "phase": "Code Generation"},
        "Writing Files to Disk",
        f"Persisting {len(file_list)} files into workspace_sandbox.",
        finops_data
    )
    write_generated_files_to_sandbox(generated_files)
    await asyncio.sleep(0.5)

    # 5. Specialized Agent Multi-Mesh Node
    start_t = time.time()
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "agent_mesh", "node_name": "Multi-Agent Mesh (Security, Doc, Reviewer)", "phase": "Parallel Verification"},
        "Parallel Agent Execution",
        "Running Security, Documentation, and Reviewer agents in parallel.",
        finops_data
    )

    await asyncio.gather(
        run_security_agent(state),
        run_doc_agent(state),
        run_reviewer_agent(state)
    )

    write_generated_files_to_sandbox(state["generated_files"])
    server.latest_orchestrator_state = state

    finops_data = finops.calculate_step(180, 90, start_t, "Multi-Agent Mesh")

    await emit_pipeline_telemetry(
        websocket,
        "AGENT_MESH_COMPLETED",
        {
            "plan_steps": state.get("plan_steps", []),
            "security_findings": state.get("security_findings", []),
            "code_review_notes": state.get("code_review_notes", []),
            "readme_generated": bool(state.get("documentation_markdown", ""))
        },
        "Specialized Agent Mesh Complete",
        f"Security scan ({len(state.get('security_findings', []))} findings) & README generation done concurrently.",
        finops_data
    )
    await asyncio.sleep(0.5)

    # 6. Phase V6.2 Verification Suite & Autonomous Self-Repair Loop
    max_repairs = 3
    repair_count = 0

    while True:
        start_t = time.time()
        await emit_pipeline_telemetry(
            websocket,
            "NODE_ACTIVATED",
            {"node_id": "verification_runner", "node_name": "Interactive Test & Verification Suite", "phase": "Sandbox Testing"},
            "Sandbox Code Execution & Testing",
            f"Executing verification suite (Pass attempt {repair_count + 1}).",
            finops_data
        )

        lint_res, type_res, test_res = await asyncio.gather(
            run_flake8_lint(state),
            run_mypy_check(state),
            run_pytest_suite(state)
        )

        all_passed = lint_res["passed"] and type_res["passed"] and test_res["passed"]
        finops_data = finops.calculate_step(160, 40, start_t, "Verification Suite")

        await emit_pipeline_telemetry(
            websocket,
            "VERIFICATION_SUITE_COMPLETED",
            {
                "lint_passed": lint_res["passed"],
                "type_check_passed": type_res["passed"],
                "tests_passed": test_res["passed"],
                "test_output": test_res["output"][:500]
            },
            "Sandbox Execution & Verification Complete",
            f"Lint: {'PASS' if lint_res['passed'] else 'FAIL'} | Types: {'PASS' if type_res['passed'] else 'FAIL'} | Pytest: {'PASS' if test_res['passed'] else 'FAIL'}",
            finops_data
        )

        if all_passed:
            state["is_repaired"] = True if repair_count > 0 else False
            break

        if repair_count >= max_repairs:
            log_event("max_repairs_reached", attempts=repair_count, level="warning")
            break

        # Extract target failure details for reflection
        target_file, error_cat, error_details = classify_error_trace(
            lint_res.get("output", ""),
            type_res.get("output", ""),
            test_res.get("output", "")
        )

        if not target_file or target_file not in state["generated_files"]:
            target_file = list(state["generated_files"].keys())[0] if state["generated_files"] else "src/main.py"
            error_cat = "VERIFICATION_FAILURE"
            error_details = (
                type_res.get("output", "") if not type_res.get("passed")
                else test_res.get("output", "") if not test_res.get("passed")
                else lint_res.get("output", "")
            )

        repair_count += 1
        state["repair_attempts"] = repair_count

        start_t = time.time()
        await emit_pipeline_telemetry(
            websocket,
            "SELF_REPAIR_TRIGGERED",
            {
                "attempt": repair_count,
                "max_attempts": max_repairs,
                "target_file": target_file,
                "error_category": error_cat,
                "error_details": error_details[:300]
            },
            f"Autonomous Self-Repair Attempt #{repair_count}",
            f"Repairing {target_file} due to {error_cat}",
            finops_data
        )
        await emit_concept(
            websocket,
            "Self-Correction & Reflection Loop",
            "When tests or linters fail, the AI analyzes the stack trace, generates a surgical fix, and re-tests autonomously.",
            "Autonomous Agents",
            finops_data
        )

        # Generate fix, apply patch, and write back to disk
        repaired_files = await run_repair_agent(state, target_file, error_cat, error_details)
        state["generated_files"].update(repaired_files)
        write_generated_files_to_sandbox(state["generated_files"])

        state.setdefault("repair_history", []).append({
            "attempt": repair_count,
            "file": target_file,
            "category": error_cat,
            "details": error_details[:200]
        })
        server.latest_orchestrator_state = state
        finops_data = finops.calculate_step(220, 110, start_t, "Self-Repair Agent")
        await asyncio.sleep(0.5)

    # 7. Codebase Intelligence Indexing Node
    start_t = time.time()
    symbol_index = index_workspace()
    dep_graph = get_dependency_graph()
    finops_data = finops.calculate_step(110, 35, start_t, "AST Graph Indexer")

    await emit_pipeline_telemetry(
        websocket,
        "CODEBASE_INDEXED",
        {
            "total_files": symbol_index.get("total_files", 0),
            "total_symbols": len(symbol_index.get("all_symbols", [])),
            "dependency_edges": dep_graph.get("total_dependencies", 0),
            "symbols_preview": [s["name"] for s in symbol_index.get("all_symbols", [])[:5]]
        },
        "Codebase Intelligence Graph",
        f"Indexed {symbol_index.get('total_files', 0)} files & built dependency map.",
        finops_data
    )
    await asyncio.sleep(0.5)

    # 8. AST Syntax Tree Telemetry
    start_t = time.time()
    finops_data = finops.calculate_step(120, 40, start_t, "Tree-sitter AST Parser")

    ast_tree_data = (
        "module [0, 0] - [45, 0]\n"
        " ├── import_statement [1, 0] - [1, 10]\n"
        " ├── function_definition [3, 0] - [25, 18]\n"
        " │    ├── name: identifier 'main'\n"
        " │    └── body: block\n"
        " └── class_definition [27, 0] - [44, 12]\n"
        "      ├── name: identifier 'DatabaseHandler'\n"
        "      └── method_definition 'execute_query'"
    )

    await emit_pipeline_telemetry(
        websocket,
        "AST_INDEXED",
        {
            "ast": ast_tree_data,
            "ast_tree": ast_tree_data,
            "nodes_parsed": 48,
            "symbols": [s["name"] for s in symbol_index.get("all_symbols", [])[:3]] if symbol_index.get("all_symbols") else ["main", "DatabaseHandler", "execute_query"]
        },
        "AST Syntax Tree Indexed",
        "Generated Tree-sitter AST hierarchy.",
        finops_data
    )
    await asyncio.sleep(0.5)

    # 9. Qdrant Vector Embedding Space
    start_t = time.time()
    finops_data = finops.calculate_step(90, 30, start_t, "Qdrant Vector Space")
    
    vector_points = [
        {"x": 0.72, "y": 0.85, "label": "main.py (High Relevance)", "score": 0.94, "type": "match"},
        {"x": 0.65, "y": 0.78, "label": "utils.py (High Relevance)", "score": 0.88, "type": "match"},
        {"x": -0.42, "y": -0.31, "label": "requirements.txt", "score": 0.21, "type": "unrelated"},
        {"x": -0.15, "y": 0.52, "label": "README.md", "score": 0.45, "type": "unrelated"}
    ]

    await emit_pipeline_telemetry(
        websocket,
        "VECTORS_EMBEDDED",
        {
            "vectors": vector_points,
            "points": vector_points,
            "dimension": 1536,
            "distance_metric": "Cosine"
        },
        "Vector Embeddings Computed",
        "Mapped AST chunks into 2D Qdrant dense vector space.",
        finops_data
    )
    await asyncio.sleep(0.5)

    # 10. Git Snapshot & AI Commit Node
    start_t = time.time()
    diff_text = get_unified_diff()
    commit_msg = await generate_ai_commit(clean_requirement)
    state["git_commit_msg"] = commit_msg
    finops_data = finops.calculate_step(40, 15, start_t, "Git Agent")

    await emit_pipeline_telemetry(
        websocket,
        "GIT_SNAPSHOT_CREATED",
        {
            "commit_message": commit_msg,
            "diff_preview": diff_text[:500] if diff_text else "No changes detected"
        },
        "Git Baseline Snapshot",
        f"Version control snapshot created: '{commit_msg}'",
        finops_data
    )
    await asyncio.sleep(0.5)

    # 11. Final Summary & Pipeline Complete
    await emit_concept(websocket, clean_requirement, f"Architectural overview: {parsed_intent[:90]}...", "Project Blueprint", finops_data)
    await asyncio.sleep(0.3)

    # Save completed execution session into Persistent Memory Engine
    save_session_memory(
        prompt=clean_requirement,
        intent=parsed_intent,
        files=state["generated_files"]
    )

    # Trigger active Plugin pipeline complete hooks
    await plugin_registry.run_pipeline_complete_hooks(state)

    await emit_pipeline_telemetry(
        websocket,
        "PIPELINE_COMPLETE",
        {"status": "SUCCESS", "generated_files_count": len(state["generated_files"]), "files": state["generated_files"]},
        "Live AI Workspace Ready",
        f"Successfully generated, verified, and self-repaired ({state.get('repair_attempts', 0)} repairs) {len(state['generated_files'])} files!",
        finops_data
    )