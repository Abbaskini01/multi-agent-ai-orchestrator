# API documentation

Base URL: `http://127.0.0.1:8000` by default (`HOST` / `PORT`).
Interactive schema: `GET /docs` (Swagger UI) and `GET /openapi.json`.

This page documents the **36 routes that exist today**, verified against the
running server. Where a request body is listed as "see schema", the exact model
is defined by the route's Python type hints and is visible in `/openapi.json`.

---

## 1. System

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Returns `static/index.html`; falls back to a JSON banner if the file is absent |
| `GET` | `/healthz` | Overall health and metrics snapshot |
| `GET` | `/livez` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |

```bash
curl -s http://127.0.0.1:8000/healthz
```

---

## 2. Orchestration

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/execution/run` | Runs the pipeline over HTTP (prefer the WebSocket for live telemetry) |
| `POST` | `/api/execution/approve` | Approves the pending human-in-the-loop gate |
| `POST` | `/api/execution/reject` | Rejects the pending gate and halts before persistence |
| `GET` | `/api/execution/reflection` | Returns the latest reflection/self-review data |
| `GET` | `/api/execution/test-report` | Returns the latest verification suite report |
| `GET` | `/api/agents/state` | Returns the current orchestrator state snapshot |

Approve / reject body:

```json
{ "notes": "Reviewed the blueprint; safe to persist." }
```

If no run is waiting at the gate, the endpoints still respond; the effect is
simply that no event is set.

WebSocket `WS /ws/orchestrate` is documented in the
[README](../README.md#11-telemetry-protocol) and
[TECHNICAL_DOCUMENTATION](TECHNICAL_DOCUMENTATION.md#5-telemetry-catalogue).

---

## 3. Git intelligence

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/git/status` | Modified / staged / untracked files in the sandbox |
| `GET` | `/api/git/diff` | Unified diff of the sandbox |
| `GET` | `/api/git/commits` | Commit history |
| `POST` | `/api/git/rollback` | Rolls the sandbox back to a commit (see schema for the target field) |

---

## 4. Code intelligence

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/codebase/graph` | Dependency graph for the workspace |
| `GET` | `/api/codebase/symbols` | Symbol index produced by the indexer |
| `GET` | `/api/workspace/projects` | Projects discovered in the workspace |
| `GET` | `/api/workspace/cross-graph` | Cross-project dependency map |

---

## 5. Knowledge graph

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/knowledge/graph` | Full enterprise knowledge graph |
| `GET` | `/api/knowledge/impact` | Impact radius for a target symbol/path (query parameter) |

```bash
curl -s "http://127.0.0.1:8000/api/knowledge/impact?target=execute_query"
```

---

## 6. Security and compliance

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/security/scan` | Static scan of the workspace for risky patterns and secrets |
| `GET` | `/api/security/compliance` | Compliance readiness report |

---

## 7. Delivery (CI/CD and deployment)

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/cicd/generate` | Scaffolds CI workflow files; optional `provider` (`github` default) |
| `POST` | `/api/cicd/deploy-verify` | Post-deploy smoke check against a target URL |
| `GET` | `/api/deploy/targets` | Known deployment targets |
| `POST` | `/api/deploy/canary` | Adjusts canary traffic allocation |

```json
{ "provider": "github" }
```

```json
{ "target_url": "http://127.0.0.1:8000/healthz" }
```

---

## 8. Project management

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/pm/decompose` | Decomposes a requirement into milestones and agent roles |
| `GET` | `/api/pm/milestones` | Current roadmap |

```json
{ "requirement": "Build a CLI expense tracker with SQLite" }
```

---

## 9. IDE integration

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/ide/completion` | Inline completion for editor extensions |
| `GET` | `/api/ide/diagnostics` | Diagnostics for the current workspace |

---

## 10. Team collaboration

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/team/presence` | Team presence, active sessions, thread counts |
| `POST` | `/api/team/comment` | Attaches an inline comment to a file/location |

```json
{
  "author": "Ada",
  "file_path": "src/main.py",
  "line": 12,
  "comment": "Consider handling the empty-input case."
}
```

`comment` is required; an empty value returns `400`.

---

## 11. Platform

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/analytics/dashboard` | Platform telemetry, token use and execution analytics |
| `GET` | `/api/memory/history` | Session memory history |
| `GET` | `/api/plugins` | Registered plugins and their metadata |
| `POST` | `/api/k8s/execute` | Executes a command through the Kubernetes runner |

---

## 12. Error behaviour

* Validation failures return FastAPI's standard `422` with a `detail` array.
* Handled domain errors use `HTTPException` (for example `400` for an empty
  comment).
* Unhandled errors return `500`; with `DEBUG=true` the response includes more
  detail. Logs always carry `request_id`.
* Every HTTP response echoes `X-Request-ID` (generated if the client did not
  send one).

---

## 13. Endpoints the dashboard calls that do not exist

| Method | Path | Caller | Status |
| --- | --- | --- | --- |
| `POST` | `/api/export-zip` | "Download workspace" button | **Not implemented** — returns 404 |
| `POST` | `/api/create-pr` | "Create pull request" button | **Not implemented** — returns 404 |

These are pre-existing gaps; the UI surfaces the failure rather than hiding it
(the PR modal shows the error, the download shows an alert).

---

## 14. Verifying the route table

```bash
python - <<'PY'
from server import app
for r in sorted(app.routes, key=lambda r: getattr(r, "path", "")):
    methods = ",".join(sorted(getattr(r, "methods", []) or []))
    print(f"{methods:10} {getattr(r, 'path', '')}")
PY
```

Expected: 36 routes, of which 35 are HTTP and one is the WebSocket.
