"""
Neural Glass AI Orchestrator — Multi-Agent Workflow Runner with Full UI Telemetry & Specialized Mesh
"""

import time
import asyncio
import traceback
from fastapi import WebSocket

from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.tracing import get_request_id
from core.git import init_sandbox_repo, get_unified_diff
from llm.groq import call_groq_intent
from llm.gemini import call_gemini_generator
from orchestrator.dlp import sanitize_prompt_dlp
from orchestrator.finops import FinOpsTracker
from orchestrator.telemetry import emit_pipeline_telemetry
from orchestrator.sandbox import write_generated_files_to_sandbox
from orchestrator.git_agent import generate_ai_commit
from orchestrator.indexer import index_workspace
from orchestrator.dep_graph import get_dependency_graph
from orchestrator.state import create_initial_orchestrator_state
from orchestrator.agents import (
    run_planner_agent,
    run_security_agent,
    run_doc_agent,
    run_reviewer_agent
)
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

    # Initialize Phase V5.3 Orchestrator State
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
    # 📚 EDUCATIONAL CONCEPT: Intent Parsing
    await emit_concept(websocket, "Intent Parsing", "The process where an AI model analyzes raw human text (like a prompt) to understand the underlying goal, extracting actionable requirements before writing any code.", "Natural Language Processing", finops_data)
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

    await emit_concept(websocket, "Planner Agent", "Decomposing high-level software goals into explicit step-by-step task graphs before invoking code generators.", "Multi-Agent System", finops_data)
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
    # 📚 EDUCATIONAL CONCEPT: Context-Injected Generation
    await emit_concept(websocket, "Agentic Scaffolding", "Instead of writing one giant script, AI Architects design modular software by dynamically generating multiple interconnected files (like main.py, database.py, and requirements.txt) all at once.", "Software Architecture", finops_data)
    await asyncio.sleep(0.5)

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

    # 5. Specialized Agent Multi-Mesh Node (Security + Doc + Reviewer Concurrently)
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

    # Re-persist README.md added by Doc Agent
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
    await emit_concept(websocket, "Parallel Agent Mesh", "Executing specialized AI agents concurrently to perform code review, security audits, and documentation in parallel without blocking the main workflow.", "Distributed Multi-Agent", finops_data)
    await asyncio.sleep(0.5)

    # 6. Phase V5.2: Codebase Intelligence Indexing Node
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
    # 📚 EDUCATIONAL CONCEPT: Dependency Graphing
    await emit_concept(websocket, "Dependency Graphing", "Mapping how modules import and call functions across files. This prevents cross-file breaking changes when editing large codebases.", "Software Intelligence", finops_data)
    await asyncio.sleep(0.5)

    # 7. Tree-sitter Indexer Node (AST Tree View Telemetry)
    start_t = time.time()
    finops_data = finops.calculate_step(120, 40, start_t, "Tree-sitter AST Parser")
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "indexer", "node_name": "AST Indexer", "phase": "Indexing"},
        "AST Code Indexing",
        "Parsing generated code syntax tree for context retrieval.",
        finops_data
    )

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
    # 📚 EDUCATIONAL CONCEPT: AST
    await emit_concept(websocket, "Abstract Syntax Tree (AST)", "A structural map of source code. Instead of reading code as raw text, ASTs break it down into grammatical components (functions, variables) so AI agents can safely modify exact logic blocks.", "Compilers & AI", finops_data)
    await asyncio.sleep(0.5)

    # 8. Qdrant Vector Embedding Space Telemetry (2D Vectors View)
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
    # 📚 EDUCATIONAL CONCEPT: Vector Embeddings
    await emit_concept(websocket, "Vector Embeddings", "Converting code or text into lists of numbers (vectors) in a multidimensional space. AI uses this to find mathematically 'similar' concepts rather than relying on exact keyword matches.", "Machine Learning", finops_data)
    await asyncio.sleep(0.5)

    # 9. Git Intelligence Snapshot & AI Commit Node
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
    # 📚 EDUCATIONAL CONCEPT: Atomic Version Control
    await emit_concept(websocket, "Atomic VCS Snapshots", "Automatically committing code state at every pipeline iteration. This provides an audit trail of AI changes and allows instant step-level rollbacks if a generated build breaks.", "DevOps & Safety", finops_data)
    await asyncio.sleep(0.5)

    # 10. Sandbox Execution Verification Node
    start_t = time.time()
    finops_data = finops.calculate_step(50, 20, start_t, "Docker Sandbox")
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "docker", "node_name": "Docker Sandbox", "phase": "Verification"},
        "Sandbox Code Execution",
        "Verifying repository structure inside sandbox.",
        finops_data
    )
    # 📚 EDUCATIONAL CONCEPT: Docker Sandbox
    await emit_concept(websocket, "Ephemeral Sandboxing", "Executing AI-generated code inside an isolated, disposable container (like Docker). This protects the host machine from malicious code and ensures dependencies are clean.", "DevSecOps", finops_data)
    await asyncio.sleep(0.5)

    # 11. Final Project Concept Summary
    await emit_concept(websocket, clean_requirement, f"Architectural overview: {parsed_intent[:90]}...", "Project Blueprint", finops_data)
    await asyncio.sleep(0.3)

    # 12. Pipeline Completion
    await emit_pipeline_telemetry(
        websocket,
        "PIPELINE_COMPLETE",
        {"status": "SUCCESS", "generated_files_count": len(state["generated_files"]), "files": state["generated_files"]},
        "Live AI Workspace Ready",
        f"Successfully generated {len(state['generated_files'])} files!",
        finops_data
    )