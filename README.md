# Multi-Agent AI Orchestrator

A LangGraph-powered multi-agent system that turns high-level software requirements into validated, multi-file Python projects. The orchestrator plans work, generates code, runs layered validation, self-heals failures, and sends Telegram notifications when a run completes.

**Current status:** Phases 1–4 complete.

## What It Does

Given a natural-language requirement (for example, "build a command-line expense tracker"), the orchestrator:

1. Decomposes the requirement into structured tasks and acceptance criteria
2. Generates each project file sequentially
3. Validates the result through syntax, runtime, and functional test gates
4. Repairs only the affected files when validation fails
5. Notifies you via Telegram on success or final failure

## Architecture

The pipeline is implemented as a LangGraph `StateGraph` with shared `OrchestratorState`:

```
START → Planner → Executor ⇄ Task Router
                      ↓
              Syntax Tester ⇄ (retry loop)
                      ↓
              Runtime Tester ⇄ (retry loop)
                      ↓
            Functional Tester ⇄ (retry loop)
                      ↓
              Notification → END
```

### Planner Agent

Uses Groq (Llama 3.3) in JSON mode to produce:

- Machine-readable **acceptance criteria**
- A structured list of **tasks** (filename + implementation blueprint)

### Structured Task Decomposition

Each task maps to a single target file (`database.py`, `app.py`, etc.) with explicit interface and behavior instructions for the Executor.

### Task Router

After each Executor pass, the router decides whether to:

- Generate the next file in the task queue, or
- Forward the completed workspace to validation

### Executor Agent

Two modes:

- **Generation:** Writes initial code for the current task file
- **Targeted repair:** On validation failure, returns surgical JSON patches for only the broken file(s)

### Multi-File Temporary Workspace

Runtime and functional tests stage all generated files into an isolated `tempfile` directory and execute them with `cwd` set to that workspace—mirroring a real project layout without touching your source tree.

### Syntax Validation

Gate 1 compiles every generated file individually with Python's `compile()` to catch syntax errors before execution.

### Runtime / Integration Validation

Gate 2 runs the workspace entry point (`app.py` or `main.py`) as a subprocess with a timeout circuit breaker and simulated stdin to avoid hanging on interactive loops.

### Functional Validation

Gate 3 asks the LLM to generate a `unittest` suite from the acceptance criteria, then runs it inside the temp workspace against backend logic (not fragile stdout assertions).

### Self-Healing Repair Loop

When any gate fails, the Executor receives the error trace and full codebase context, then returns corrected files. The pipeline re-validates from the syntax gate.

### Targeted File Repair

Repairs modify only files implicated by the error; working files are preserved unless an interface change requires a coordinated update.

### Retry / Circuit Breaker

Each validation gate allows up to **3 retry attempts**. After the limit, the flow routes to the Notification agent with the last error.

### Telegram Notifications

The Notification agent sends Markdown alerts (with plain-text fallback) summarizing success, generated files, retry count, or final failure details.

## Future Roadmap — Five Orchestration Pillars

The long-term goal is a production-grade orchestrator implementing all five pillars:

1. **Git integration and diff/patch repair** — Version-controlled workspaces with patch-based fixes
2. **Containerized / sandboxed execution** — Isolated, reproducible test environments
3. **AST / symbol-based codebase retrieval and RAG** — Context-aware code search where appropriate
4. **Human-in-the-loop approval** — Review gates before applying changes
5. **Multi-model routing** — Route tasks to the best model for planning, coding, or testing

## Setup

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/)
- A Telegram bot token and chat ID (optional, for notifications)

### Installation

```bash
# Clone the repository
git clone https://github.com/Abbaskini01/multi-agent-ai-orchestrator.git
cd multi-agent-ai-orchestrator

# Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install python-dotenv langchain-groq langgraph

# Configure environment variables
cp .env.example .env
# Edit .env and add your credentials (never commit .env)
```

### Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for Llama 3.3 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token |
| `TELEGRAM_CHAT_ID` | Target chat ID for notifications |

### Run the Orchestrator

```bash
python app.py
```

### Test Telegram Notifications

```bash
python test_tele.py
```

## Project Files

| File | Purpose |
|---|---|
| `app.py` | Main LangGraph orchestrator (Phases 1–4) |
| `test_tele.py` | Standalone Telegram connectivity test |
| `.env.example` | Template for required environment variables |

## License

Add a license before public distribution if needed.
