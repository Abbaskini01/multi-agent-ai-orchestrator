# Technical documentation

Implementation-level notes for maintainers. Behaviour described here is what the
code does now; gaps are called out explicitly.

---

## 1. Request and run model

| Concern | Implementation |
| --- | --- |
| HTTP app | `server.py` (`FastAPI`), `lifespan` validates config at startup |
| Static UI | `/` returns `static/index.html`; `/static` is a `StaticFiles` mount |
| Realtime | `WS /ws/orchestrate`, one connection per browser tab |
| Run trigger | `{"action": "START_PIPELINE", "prompt": "..."}` (only `prompt` is required) |
| Run scope | one asyncio task chain per message; no global queue |
| Cancellation | client disconnect / socket close stops further emits, not the run loop |

`server.py` exposes two process-wide objects used by the pipeline:

```python
latest_orchestrator_state: dict | None
current_approval_event: asyncio.Event | None
```

The pipeline imports `server` for these. That creates a circular import which is
safe because attribute access happens only while handling a run.

---

## 2. Module reference

### Entry points

| Module | Purpose | Notes |
| --- | --- | --- |
| `server.py` | Composition root: middleware, static UI, 36 routes, WebSocket | Start with `uvicorn server:app`; script mode fails on the import cycle |
| `app.py` | Interactive CLI over `orchestrator.graph.app` | Asks for approve/modify/quit at the blueprint |

### Orchestration

| Module | Purpose |
| --- | --- |
| `orchestrator/pipeline.py` | The 14 numbered stages; emits every telemetry event |
| `orchestrator/graph.py` | `StateGraph` with conditional edges and a 3-retry loop |
| `orchestrator/state.py` | `OrchestratorState` (`TypedDict`, `total=False`) + initial factory |
| `orchestrator/agents.py` | Planner (Gemini), security (heuristic), docs, reviewer |
| `orchestrator/planner.py`, `scaffolder.py`, `executor.py`, `validators.py` | LangGraph node implementations |
| `orchestrator/testers.py` | Subprocess runners for flake8 / mypy / pytest |
| `orchestrator/repair.py` | Traceback classification + repair prompt |
| `orchestrator/telemetry.py` | Wraps `websocket.manager.emit_event` |
| `orchestrator/finops.py` | Token/cost/latency accumulator |
| `orchestrator/dlp.py` | Secret patterns + redaction |
| `orchestrator/sandbox.py` | Writes files, initialises sandbox git |
| `orchestrator/indexer.py`, `dep_graph.py` | Symbol index and dependency edges |
| `orchestrator/git_agent.py` | AI commit message generation |

### Platform

| Module | Purpose |
| --- | --- |
| `core/config.py` | `Settings` (pydantic-settings) and validation |
| `core/logger.py` | `log_event(event, **fields)` JSON logging |
| `core/metrics.py` | Request/run counters, active WS gauge |
| `core/tracing.py` | `set_request_id` / `reset_request_id` context |
| `core/health.py` | `healthz`, `livez`, `readyz` probes |
| `core/memory.py` | Session memory (SQLite), history API |
| `core/plugins.py` | Plugin registry and hook dispatch |
| `core/*` domain modules | git, security, CI/CD, PM, deployment, IDE, collaboration, analytics, multi-repo, k8s |

---

## 3. `OrchestratorState`

`total=False` means any stage may read a partially filled state. The factory
`create_initial_orchestrator_state(requirement)` seeds every field.

| Group | Fields |
| --- | --- |
| Requirement | `user_requirement`, `clean_requirement`, `parsed_intent` |
| Blueprint | `project_name`, `architecture_pattern`, `folders`, `acceptance_criteria`, `tasks`, `plan_steps` |
| Execution | `current_task_index`, `generated_files`, `error_message`, `retry_count` |
| Approval | `is_approved`, `requires_approval`, `approval_status`, `human_feedback`, `human_notes` |
| Review | `security_findings`, `code_review_notes`, `documentation_markdown` |
| Verification | `execution_logs`, `lint_results`, `type_check_results`, `test_results` |
| Repair | `repair_attempts`, `is_repaired`, `repair_history` |
| Git | `git_commit_hash`, `git_commit_msg` |

`generated_files` is the contract between generation, the agents and the UI:
a `dict[str, str]` mapping relative paths to full file contents.

---

## 4. Gemini adapter contract

```python
async def call_gemini_intent(prompt: str) -> str
async def call_gemini_generator(requirement: str) -> dict[str, str]
```

* The SDK is synchronous; both functions offload to a thread with
  `asyncio.to_thread` and cap the wait with `asyncio.wait_for(..., REQUEST_TIMEOUT_SECONDS)`.
* The blocking helpers are decorated with `create_llm_retry_decorator("gemini")`,
  driven by `MAX_API_RETRIES`, `RETRY_DELAY_SECONDS` and
  `RETRY_EXPONENTIAL_MULTIPLIER`.
* The generator prompt demands **raw JSON** keyed by relative path. Leading and
  trailing markdown fences are stripped defensively before `json.loads`.
* An empty dict, a non-dict payload or any exception falls through to
  `generate_fallback_workspace`, so callers always receive at least one file.
* `call_gemini_intent` never raises; it returns the input prompt when offline.

Model selection is `_get_clean_gemini_model()` → `settings.default_gemini_model`
(current default `gemini-3.8-flash`). No provider routing exists in code that the
pipeline executes.

---

## 5. Telemetry catalogue

Envelope (see `websocket/manager.py`):

```json
{"type": "...", "event": "...", "data": {...}, "title": "...", "description": "...", "finops": {...}}
```

| Event | Emitted at | `data` essentials |
| --- | --- | --- |
| `PIPELINE_INITIATED` | after intent parsing | requirement / intent |
| `DLP_REDACTION_WARNING` | if secrets found | `leaks_detected[]`, `sanitized_prompt` |
| `CONCEPT_LEARNED` | several stages | `title`, `description`, `category`, `timestamp` |
| `NODE_ACTIVATED` | each agent stage | `node_id`, `node_name`, `phase` |
| `ARCHITECT_BLUEPRINT_CREATED` | after planning | plan/blueprint fields |
| `HUMAN_APPROVAL_REQUESTED` | before persistence | `step`, `preview` |
| `PIPELINE_HALTED` | on rejection | reason/status |
| `AGENT_MESH_COMPLETED` | after parallel agents | findings/notes |
| `VERIFICATION_SUITE_COMPLETED` | after tests | lint/type/test summaries |
| `SELF_REPAIR_TRIGGERED` | each repair attempt | attempt number, error class |
| `CODEBASE_INDEXED` | after indexing | symbol counts, graph |
| `AST_INDEXED` | teach stage | `ast_tree` string **or** `root` node |
| `VECTORS_EMBEDDED` | teach stage | `points[]` with `x, y, label, score, type` |
| `GIT_SNAPSHOT_CREATED` | after commit | commit message, diff preview |
| `PIPELINE_COMPLETE` | success | `status`, `generated_files_count`, `files` |
| `PIPELINE_ERROR` | failure | `error_message`, `traceback` |

Client behaviour lives in `handleTelemetryEvent` in `static/index.html`; unknown
events are appended to the stream without side effects.

---

## 6. Persistence, memory and plugins

* **Files** — `write_generated_files_to_sandbox` creates parent directories and
  writes each entry of `generated_files` under `WORKSPACE_DIR`.
* **Git** — the sandbox repository is initialised on demand; the run ends with a
  snapshot whose message is produced by `generate_ai_commit`.
* **Memory** — `core/memory.py` records session summaries in SQLite and exposes
  `GET /api/memory/history`. The database is local to the process host.
* **Plugins** — `core/plugins.py` loads modules from `plugins/` and dispatches
  lifecycle hooks around generation/persistence. Failures are logged, not fatal.

> Repository note: `workspace_sandbox/` is currently tracked by the parent repo
> because of a malformed `.gitignore` line, so a real run modifies tracked files.

---

## 7. Concurrency and timeouts

| Mechanism | Where | Value |
| --- | --- | --- |
| Agent mesh fan-out | `pipeline.py` | `asyncio.gather` (security, docs, reviewer) |
| Model call timeout | `llm/gemini.py` | `REQUEST_TIMEOUT_SECONDS` (30 s) |
| HITL wait | `pipeline.py` | 300 s |
| WebSocket idle | `core/config.py` | `WS_TIMEOUT_SECONDS` (60 s) |
| Repair attempts | `pipeline.py` / `graph.py` | 3 |

Verification subprocesses are synchronous calls executed off the event loop
inside the async stage; they inherit the server process environment.

---

## 8. Extending the system

**Add a pipeline stage**
1. Insert the step in `run_educational_pipeline` with a numbered comment.
2. Emit one envelope via `emit_pipeline_telemetry` (keep the event name stable).
3. If the UI should react, add a branch in `handleTelemetryEvent`.

**Add a domain endpoint**
1. Implement the engine function in `core/<domain>.py`.
2. Add the route in `server.py` with a docstring (it becomes the OpenAPI summary).
3. Document it in `docs/API_DOCUMENTATION.md` and verify the route count.

**Add a UI stage**
1. Add the stage element with `id="stage-<name>" data-state="idle"`.
2. Extend `STAGE_ORDER` and, if backend-driven, `NODE_TO_STAGE`.

---

## 9. Conventions

* Python: 4 spaces, type hints on public functions, module docstrings explain the
  contract and any intentional limitation.
* Python files in this repository use CRLF line endings; keep them when editing.
* Frontend: CSS custom properties for all colours; no inline colour literals in
  markup; presentation changes must not rename existing ids or function names.
* Tests: there is no automated suite yet; `tests/` is empty and the root
  `test_*.py` files are manual scripts. Dashboard logic is verified with the
  browser pass described in the README.
