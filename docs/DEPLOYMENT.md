# Deployment notes

> There is **no Dockerfile, compose file, Kubernetes manifest or CI workflow in
> this repository today**. This page describes how to run the app as a service
> and what to add if you containerise it. It does not claim any of that is
> already provided.

---

## 1. Runtime shape

One Uvicorn process serves the API, the WebSocket and the static dashboard. It
keeps in-memory state (connection registry, FinOps ledger, latest run state), so:

* **do not scale horizontally** without moving that state out of the process;
* run a **single worker** — multiple workers would each have their own registry
  and HITL event, and a browser could connect to the wrong one.

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## 2. Environment

| Variable | Production guidance |
| --- | --- |
| `GEMINI_API_KEY` | Inject from a secret store; never bake into an image |
| `DEFAULT_GEMINI_MODEL` | Pin explicitly so upgrades are deliberate |
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `CORS_ORIGINS` | Replace `["*"]` with your dashboard origin(s) |
| `LOG_LEVEL` | `INFO` (JSON logs are on by default) |
| `WORKSPACE_DIR` | A writable volume, not the container's ephemeral layer |
| `REQUEST_TIMEOUT_SECONDS` | Keep below your proxy timeout |

---

## 3. Probes

| Probe | Path | Use |
| --- | --- | --- |
| Liveness | `/livez` | Restart the process if it fails |
| Readiness | `/readyz` | Remove from the load balancer while failing |
| Health | `/healthz` | Human/ops check with metrics |

The dashboard itself is `GET /`; the WebSocket is `WS /ws/orchestrate`.

---

## 4. Reverse proxy requirements

The UI is useless if the WebSocket cannot upgrade. For nginx:

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;   # runs include a 300s approval wait
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Request-ID $request_id;
}
```

`proxy_read_timeout` must exceed the human-approval window, otherwise the socket
drops mid-run.

---

## 5. If you containerise it

A minimal, correct image needs:

1. Python 3.11 base;
2. `pip install -r requirements.txt`;
3. the repo copied to `/app` (the sandbox and `static/` are relative to the code);
4. a writable volume for `WORKSPACE_DIR`;
5. `uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1` as the command;
6. no secrets in layers — pass `GEMINI_API_KEY` at runtime.

Sketch (not shipped):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV WORKSPACE_DIR=/data/workspace_sandbox
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

Mount `/data` as a volume. Remember that the pipeline executes subprocesses
inside that directory — treat the container as trusted-code execution, not as a
security boundary.

---

## 6. Operational checklist

- [ ] `.env` not committed; keys injected at deploy time
- [ ] `CORS_ORIGINS` narrowed
- [ ] `DEBUG=false`
- [ ] writable workspace volume mounted
- [ ] proxy WebSocket upgrade verified (`CONNECTED` in the header)
- [ ] probes wired to `/livez` and `/readyz`
- [ ] log aggregation picks up JSON lines with `request_id`
- [ ] single worker confirmed
- [ ] disk growth from generated projects monitored
