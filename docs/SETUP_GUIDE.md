# Setup guide

Everything needed to get Neural Glass running locally, from a clean machine.

---

## 1. Prerequisites

| Requirement | Version | Why |
| --- | --- | --- |
| Python | 3.11.x | Type syntax and dependency versions target 3.11 |
| pip | current | Installs `requirements.txt` |
| Git | any recent | Sandbox snapshots and cloning |
| Browser | Chrome / Edge / Firefox | Dashboard needs WebSocket + modern CSS |
| Gemini API key | — | Optional; without it the pipeline uses the fallback scaffold |
| Internet | for first load | Tailwind, Lucide, xterm.js and fonts come from CDNs |

Disk: allow ~1 GB for the virtualenv; the generated projects are small.

---

## 2. Get the code

```bash
git clone https://github.com/Abbaskini01/multi-agent-ai-orchestrator.git
cd multi-agent-ai-orchestrator
```

If you already have the folder, just make sure you are on the right branch:

```bash
git status
git branch --show-current
```

---

## 3. Create the environment

**Windows (Git Bash / PowerShell)**

```bash
python -m venv venv
source venv/Scripts/activate
python --version        # expect 3.11.x
```

**macOS / Linux**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

Install:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

The requirements include the verification toolchain (`flake8`, `mypy`, `pytest`)
because the pipeline shells out to them.

---

## 4. Configure

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```env
GEMINI_API_KEY=your_key_here
DEFAULT_GEMINI_MODEL=gemini-3.8-flash
```

Rules:

* never commit `.env`;
* keep the model id in sync with a model your key can access;
* everything else has a working default (see the configuration table in the
  [README](../README.md#10-configuration)).

If `GEMINI_API_KEY` is blank, startup still succeeds and generation falls back to
a deterministic local scaffold — useful for UI work without spending tokens.

---

## 5. Run

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

> Do **not** run `python server.py`. Script mode executes the file as `__main__`
> and the pipeline's `import server` then re-enters the module, raising an
> `ImportError` on the partially initialised pipeline. Uvicorn imports it as the
> `server` module, which is why this is the supported command (see the README's
> known limitations).

Startup sequence in the log:

1. configuration validation;
2. Gemini SDK initialisation (`gemini_sdk_initialized key_len=…`);
3. plugin loading;
4. `Uvicorn running on http://127.0.0.1:8000`.

Open <http://127.0.0.1:8000/>.

---

## 6. Verify the install

```bash
curl -s http://127.0.0.1:8000/healthz
curl -s http://127.0.0.1:8000/readyz
curl -s http://127.0.0.1:8000/api/plugins
```

Then in the browser:

1. the header pill should read **CONNECTED**;
2. click **Run Pipeline** with the default prompt;
3. the stream should fill, the stepper should advance, and the approval modal
   should appear before files are written;
4. approve, and the run should finish with the generated file list.

---

## 7. Optional: CLI state machine

`app.py` exercises the LangGraph version instead of the web pipeline:

```bash
python app.py
```

It prints the blueprint and waits for `A` (approve), `M` (modify) or `Q` (quit).
This path writes to the same sandbox directory.

---

## 8. Reset / clean state

```bash
# stop the server first
rm -rf workspace_sandbox/generated_projects   # generated output (keep the sample files)
rm -f app.db                                  # local memory database, if present
```

To start completely fresh, delete `venv/` and recreate it.

> `workspace_sandbox/` currently contains tracked sample files; a run overwrites
> them. Back them up before running if you need the originals.

---

## 9. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `python: command not found` | Use `py -3.11` (Windows) or `python3.11`; ensure it is on `PATH` |
| `pip install` fails on `tree-sitter-languages` | Use Python 3.11; the pins require `tree-sitter<0.22` |
| `ModuleNotFoundError` when starting | The venv is not active, or deps went to another interpreter |
| Port 8000 busy | `python -m uvicorn server:app --port 8010` |
| UI unstyled / icons missing | CDN blocked; allow `cdn.tailwindcss.com`, `unpkg.com`, `cdn.jsdelivr.net`, `fonts.googleapis.com` |
| Header shows DISCONNECTED | Server not running, or a reverse proxy without WebSocket upgrade |
| Generation falls back | Key invalid/quota exceeded/model unavailable — check `gemini_generation_failed` |
| `pytest` cannot find tests | Run from the repository root |

---

## 10. Where to go next

* [README](../README.md) — features, pipeline, limitations
* [ARCHITECTURE](ARCHITECTURE.md) — component and sequence diagrams
* [TECHNICAL_DOCUMENTATION](TECHNICAL_DOCUMENTATION.md) — contracts and internals
* [API_DOCUMENTATION](API_DOCUMENTATION.md) — endpoint reference
* [DEPLOYMENT](DEPLOYMENT.md) — container and cluster notes
