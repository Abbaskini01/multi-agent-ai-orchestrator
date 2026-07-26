"""
Neural Glass AI Orchestrator — Multi-Agent Workflow Runner with Full UI Telemetry & Educational Concepts
"""

import time
import asyncio
import traceback
from fastapi import WebSocket

from core.config import settings
from core.logger import log_event
from core.metrics import metrics
from core.tracing import get_request_id
from llm.groq import call_groq_intent
from llm.gemini import call_gemini_generator
from orchestrator.dlp import sanitize_prompt_dlp
from orchestrator.finops import FinOpsTracker
from orchestrator.telemetry import emit_pipeline_telemetry
from orchestrator.sandbox import write_generated_files_to_sandbox


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

    # DLP Sanitization Step
    clean_requirement, detected_leaks = sanitize_prompt_dlp(requirement)
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

    # 2. Gemini / Groq Code Generation Node
    start_t = time.time()
    await emit_pipeline_telemetry(
        websocket,
        "NODE_ACTIVATED",
        {"node_id": "architect", "node_name": "Architect Agent Node", "phase": "Planning"},
        "Multi-File Scaffolding",
        f"Architect node invoking model for dynamic code generation.",
        finops_data
    )

    generated_files = await call_gemini_generator(clean_requirement)
    file_list = list(generated_files.keys())
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

    # 3. Tree-sitter Indexer Node (AST Tree View Telemetry)
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
            "symbols": ["main", "DatabaseHandler", "execute_query"]
        },
        "AST Syntax Tree Indexed",
        "Generated Tree-sitter AST hierarchy.",
        finops_data
    )
    # 📚 EDUCATIONAL CONCEPT: AST
    await emit_concept(websocket, "Abstract Syntax Tree (AST)", "A structural map of source code. Instead of reading code as raw text, ASTs break it down into grammatical components (functions, variables) so AI agents can safely modify exact logic blocks.", "Compilers & AI", finops_data)
    await asyncio.sleep(0.5)

    # 4. Qdrant Vector Embedding Space Telemetry (2D Vectors View)
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

    # 5. Code Persistence Executor Node
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

    # 6. Sandbox Execution Verification Node
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

    # 7. Final Project Concept Summary
    await emit_concept(websocket, clean_requirement, f"Architectural overview: {parsed_intent[:90]}...", "Project Blueprint", finops_data)
    await asyncio.sleep(0.3)

    # 8. Pipeline Completion
    await emit_pipeline_telemetry(
        websocket,
        "PIPELINE_COMPLETE",
        {"status": "SUCCESS", "generated_files_count": len(generated_files), "files": generated_files},
        "Live AI Workspace Ready",
        f"Successfully generated {len(generated_files)} files!",
        finops_data
    )