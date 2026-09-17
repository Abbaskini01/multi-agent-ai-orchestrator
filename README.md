# Autonomous Multi-Agent AI Software Engineering Orchestrator

> A local AI software engineering system that transforms high-level software requirements into validated, tested, self-correcting, Git-managed project repositories using multi-agent orchestration, LangGraph, Docker sandboxing, AST-based code intelligence, human approval, and multi-model routing.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed%20Execution-2496ED.svg)](https://www.docker.com/)
[![Git](https://img.shields.io/badge/Git-Version%20Control-F05032.svg)](https://git-scm.com/)
[![Status](https://img.shields.io/badge/Status-Active%20Development-green.svg)]()

---

## Overview

The **Autonomous Multi-Agent AI Software Engineering Orchestrator** is a local AI-powered software engineering system designed to automate the software development lifecycle from a natural-language requirement to a validated project repository.

Instead of treating an LLM as a simple code generator, the system models software development as a coordinated workflow involving specialized agents and deterministic engineering tools.

A typical execution follows:

```text
User Requirement
       │
       ▼
Architect / Planner
       │
       ▼
Structured Project Blueprint
       │
       ▼
Human Approval
       │
       ▼
Task Decomposition
       │
       ▼
Code Executors
       │
       ▼
Project Workspace
       │
       ├───────────────┐
       ▼               ▼
Syntax Validation   AST Analysis
       │
       ▼
Runtime Validation
       │
       ▼
Functional Testing
       │
       ▼
Failure?
   ┌───┴───┐
   │       │
  Yes      No
   │       │
   ▼       ▼
Targeted  Continue
Repair      │
   │        │
   └────┐   │
        ▼   ▼
      Re-validation
            │
            ▼
       Git-managed
       Project Output
            │
            ▼
         Complete
````

The central idea is simple:

> **Generate → Validate → Diagnose → Repair → Re-validate → Deliver**

---

# Why This Project Exists

Large Language Models are extremely capable at generating code, but generating code is only one part of software engineering.

Real software development also requires:

* architecture
* dependency management
* project organization
* testing
* debugging
* version control
* environment isolation
* documentation
* human review
* failure recovery
* deployment preparation

A naive AI coding workflow looks like:

```text
Prompt
  ↓
LLM
  ↓
Code
```

This project explores a more reliable architecture:

```text
Requirement
     ↓
Planning
     ↓
Execution
     ↓
Validation
     ↓
Diagnosis
     ↓
Targeted Repair
     ↓
Re-validation
     ↓
Version Control
     ↓
Project Delivery
```

The goal is to investigate how autonomous software engineering systems can be built by combining **LLMs with deterministic software engineering infrastructure**.

---

# Core Design Philosophy

The orchestrator is built around five principles.

### 1. LLMs make decisions; deterministic tools verify them

The LLM can generate code and reason about failures.

Python, Git, Docker, AST parsing, and test frameworks provide deterministic verification.

---

### 2. Failure is feedback

A failed test does not immediately terminate the workflow.

Instead:

```text
Failure
   ↓
Error Trace
   ↓
LLM Diagnosis
   ↓
Repair
   ↓
Validation
```

---

### 3. Repair should be targeted

The system should avoid unnecessarily regenerating the entire project.

When possible, only the affected file or code region is modified.

---

### 4. Humans remain in control

The system supports a human approval checkpoint before expensive code-generation operations.

---

### 5. Generated software should become a real repository

The final result should not be a block of code returned by an LLM.

It should become an organized software project containing source code, tests, documentation, configuration, and version-control metadata.

---

# Architecture

The system uses **LangGraph** as the orchestration and state-management layer.

The workflow is represented as a state machine composed of specialized nodes.

```text
                         ┌─────────────────┐
                         │ User Requirement│
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Architect       │
                         │ / Planner       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Human Approval  │
                         │ HITL            │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Task Decomposer │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Executor Agents │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Project         │
                         │ Workspace       │
                         └────────┬────────┘
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
                 Syntax        Runtime      Functional
                 Testing       Testing      Testing
                     │            │            │
                     └────────────┼────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Failure         │
                         │ Diagnosis       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ AST-guided      │
                         │ Targeted Repair │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Git Diff /      │
                         │ Patch           │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Docker          │
                         │ Validation      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Project Export  │
                         └─────────────────┘
```

---

# Multi-Agent Responsibilities

## Architect / Planner Agent

Responsible for transforming the user's natural-language requirement into a structured software blueprint.

It determines:

* project structure
* modules
* file responsibilities
* interfaces
* acceptance criteria
* implementation tasks

---

## Executor Agent

Responsible for implementing individual project components.

The Executor receives:

* user requirements
* architectural instructions
* task descriptions
* existing code
* validation errors
* AST information

and produces or repairs code accordingly.

---

## Syntax Validation Agent

Performs static validation before execution.

The current implementation uses Python compilation mechanisms to detect invalid syntax.

```text
Generated Code
     ↓
compile()
     ↓
Syntax Valid / Invalid
```

---

## Runtime Validation Agent

Executes generated software and verifies that it can start and run without unhandled runtime failures.

Execution is performed inside an isolated environment when Docker is available.

---

## Functional Testing Agent

Tests whether the generated implementation actually satisfies its intended behavior.

The functional validation layer uses generated test suites and assertions rather than relying solely on process exit codes.

---

## AST Analysis Agent

Analyzes the structure of the generated code.

The AST layer extracts information such as:

* classes
* functions
* methods
* arguments
* imports
* structural relationships

This information is supplied to repair workflows so that the LLM has structural context when diagnosing failures.

---

## Human-in-the-Loop Agent

Provides a checkpoint between planning and execution.

The developer can:

```text
[A] Approve
[M] Modify
[Q] Quit
```

This prevents the system from blindly executing an architecture that the developer has not reviewed.

---

## Git Repair Engine

Uses Git-based diff/patch workflows to preserve stable parts of the project while modifying defective components.

Conceptually:

```text
Existing Repository
       │
       ▼
Failure Diagnosis
       │
       ▼
Target File
       │
       ▼
Generated Patch
       │
       ▼
git diff / patch
       │
       ▼
Updated Repository
```

---

## Multi-Model Router

The orchestrator supports multiple LLM providers.

The current routing strategy uses:

```text
Primary Model
Groq / Llama 3.3 70B
        │
        │ failure / rate limit / timeout
        ▼
Fallback Model
Google Gemini 2.5 Flash
```

This improves resilience against provider-specific failures.

---

# Three-Tier Quality Control System

A major component of the project is its validation pipeline.

## Gate 1 — Syntax

Checks whether the generated Python code is syntactically valid.

```text
Source Code
    ↓
Python Compiler
    ↓
PASS / FAIL
```

---

## Gate 2 — Runtime

Checks whether the application can actually execute.

```text
Project
   ↓
Sandbox
   ↓
Python Process
   ↓
Exit Code / Runtime Trace
```

Timeouts and runtime exceptions are captured and converted into repair feedback.

---

## Gate 3 — Functional

Checks whether the implementation behaves according to its intended requirements.

For example:

```text
Requirement:
"Add an expense"

        ↓

Functional Test:

Create expense
      ↓
Query database
      ↓
Verify record exists
```

This distinguishes:

> "The program runs"

from:

> "The program actually works."

---

# Self-Healing Architecture

When validation fails, the orchestrator does not immediately terminate.

Instead, the error becomes part of the next reasoning cycle.

```text
             ┌─────────────────────┐
             │ Generated Project   │
             └──────────┬──────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Validation  │
                 └──────┬──────┘
                        │
                 ┌──────┴──────┐
                 │             │
                PASS          FAIL
                 │             │
                 ▼             ▼
              Continue      Diagnose
                               │
                               ▼
                         AST Context
                               │
                               ▼
                         LLM Repair
                               │
                               ▼
                         Git Patch
                               │
                               ▼
                          Validation
```

A retry/circuit-breaker mechanism prevents infinite repair loops.

---

# Docker Sandboxing

Generated code is potentially untrusted.

Therefore, runtime and functional validation can be executed inside ephemeral Docker containers.

The intended environment is based on:

```text
python:3.11-slim
```

The container provides an isolated execution boundary between generated code and the host environment.

The system also supports a local subprocess fallback when Docker is unavailable.

---

# Git-Based Surgical Repair

One of the key architectural improvements is the transition from full-project regeneration to targeted modification.

### Earlier approach

```text
Failure
  ↓
Regenerate entire project
```

### Current approach

```text
Failure
  ↓
Identify affected component
  ↓
Analyze AST / traceback
  ↓
Generate targeted repair
  ↓
Apply Git diff
```

This reduces unnecessary modifications and helps preserve working code.

---

# Project Generation

The long-term Version 2 architecture is designed to generate complete repositories rather than only two Python files.

A generated project can evolve toward a structure such as:

```text
generated_projects/
└── ExpenseTracker/
    │
    ├── README.md
    ├── LICENSE
    ├── requirements.txt
    ├── pyproject.toml
    ├── .env.example
    ├── .gitignore
    ├── Dockerfile
    ├── docker-compose.yml
    │
    ├── src/
    │   ├── main.py
    │   ├── database.py
    │   ├── models.py
    │   ├── services.py
    │   ├── crud.py
    │   ├── schemas.py
    │   ├── config.py
    │   ├── logger.py
    │   ├── validators.py
    │   └── exceptions.py
    │
    ├── tests/
    │   ├── test_database.py
    │   ├── test_models.py
    │   └── test_services.py
    │
    ├── docs/
    │   └── architecture.md
    │
    ├── scripts/
    │   └── seed_database.py
    │
    └── .github/
        └── workflows/
            └── python.yml
```

The exact structure should be determined dynamically by the architecture generated for the user's requirement.

---

# Version 1 — Completed Capabilities

The first major version of the system was developed through ten phases.

### Phase 1 — Architecture & State Graph

Established the LangGraph workflow and shared state model.

---

### Phase 2 — Planner & Executor

Introduced structured task decomposition and LLM-powered code generation.

---

### Phase 3 — Three-Tier Validation

Introduced:

* syntax validation
* runtime validation
* functional validation

---

### Phase 4 — Self-Correction & Notifications

Added:

* automatic repair loops
* retry limits
* Telegram notifications

---

### Phase 5 — Workspace Export & Git

Added:

* persistent project export
* README generation
* `.gitignore`
* Git repository initialization
* commit tracking

---

### Phase 6 — Git Diff Surgical Patching

Replaced destructive full-project repair with targeted Git-based modifications.

---

### Phase 7 — Human-in-the-Loop

Added developer approval before code generation.

---

### Phase 8 — Docker Sandboxing

Moved validation into isolated Docker environments with local fallback support.

---

### Phase 9 — AST Code Intelligence

Added structural code analysis and symbol extraction for repair context.

---

### Phase 10 — Multi-Model Routing

Added primary/fallback LLM routing using:

* Groq Llama 3.3 70B
* Google Gemini 2.5 Flash

---

# The Five Engineering Pillars

Version 1 established five major engineering capabilities.

| Pillar | Capability                 | Purpose                             |
| ------ | -------------------------- | ----------------------------------- |
| 1      | Git Integration & Patching | Preserve stable code during repairs |
| 2      | Human-in-the-Loop          | Maintain developer control          |
| 3      | Container Sandboxing       | Isolate generated code              |
| 4      | AST Code Intelligence      | Understand code structure           |
| 5      | Multi-Model Routing        | Improve LLM resilience              |

---

# Version 2 — Advanced Repository Engineering

Version 2 focuses on moving from a **multi-file code generator** toward a **complete software repository engineering system**.

The major architectural transformation is:

```text
VERSION 1

Requirement
    ↓
Planner
    ↓
Executor
    ↓
Validation
    ↓
Repair
    ↓
Export
```

to:

```text
VERSION 2

Requirement
      ↓
Architect
      ↓
Project Blueprint
      ↓
Human Approval
      ↓
Project Scaffolding
      ↓
Dependency Planning
      ↓
Parallel Execution
      ↓
Validation
      ↓
AST Intelligence
      ↓
Targeted Repair
      ↓
Documentation
      ↓
Testing
      ↓
CI/CD
      ↓
Docker
      ↓
Git
      ↓
Complete Repository
```

---

## Version 2 Planned Components

### Architect Agent

Designs the complete repository before implementation.

---

### Project Scaffolder

Creates:

* directories
* package structure
* configuration structure
* testing structure
* documentation structure

---

### Dependency Agent

Determines and generates:

* `requirements.txt`
* `pyproject.toml`
* environment configuration
* dependency metadata

---

### Documentation Agent

Generates:

* README
* architecture documentation
* usage documentation
* API documentation where applicable

---

### Testing Planner

Creates project-specific tests based on requirements and acceptance criteria.

---

### Configuration Agent

Handles:

* environment variables
* application configuration
* logging configuration
* runtime settings

---

### CI/CD Agent

Generates appropriate CI configuration such as:

```text
.github/
└── workflows/
    └── python.yml
```

---

### Deployment Agent

Determines whether deployment configuration is required and generates appropriate artifacts.

---

### Parallel Execution

Independent tasks should eventually be executed concurrently rather than forcing every file through a sequential pipeline.

This is intended to improve throughput while preserving dependency ordering where required.

---

# Example

A user could provide:

```text
Build a REST API for managing student records.
```

The system should not simply produce:

```text
app.py
database.py
```

Instead, the Architect should determine an appropriate repository structure, potentially including:

```text
student-api/

src/
    main.py
    models.py
    schemas.py
    database.py
    services.py
    routes/
        students.py
    config.py

tests/
    test_students.py
    test_services.py

docs/
    architecture.md

.github/
    workflows/
        tests.yml

Dockerfile
requirements.txt
pyproject.toml
.env.example
.gitignore
README.md
```

The exact structure remains architecture-dependent.

---

# Technology Stack

## Core

* Python 3.11+
* LangGraph
* LangChain
* Groq
* Google Gemini

## AI / LLM

* Llama 3.3 70B
* Gemini 2.5 Flash
* Multi-model fallback routing

## Software Engineering

* Git
* Git diff / patch workflows
* Python AST
* unittest / functional testing
* subprocess execution

## Sandboxing

* Docker
* `python:3.11-slim`

## Infrastructure

* Temporary workspaces
* Persistent project export
* Environment variables
* Telegram notifications

---

# Repository Structure

The orchestrator itself is being evolved toward a modular architecture.

A target structure is:

```text
multi-agent-ai-orchestrator/

├── orchestrator/
│   ├── agents/
│   │   ├── architect.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── tester.py
│   │   └── repair.py
│   │
│   ├── validators/
│   │   ├── syntax.py
│   │   ├── runtime.py
│   │   └── functional.py
│   │
│   ├── tools/
│   │   ├── git.py
│   │   ├── docker.py
│   │   └── filesystem.py
│   │
│   ├── ast_parser.py
│   ├── router.py
│   ├── state.py
│   └── notifications.py
│
├── tests/
│
├── generated_projects/
│
├── docs/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

The exact structure may change as the Version 2 architecture evolves.

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/Abbaskini01/multi-agent-ai-orchestrator.git
cd multi-agent-ai-orchestrator
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Configuration

Create a local `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

GOOGLE_API_KEY=your_google_api_key
```

Never commit `.env` to Git.

The repository provides `.env.example` as a safe configuration template.

---

# Running the Orchestrator

Run:

```bash
python app.py
```

The orchestrator will initialize the workflow and process the configured requirement.

The generated project then passes through the orchestration and validation pipeline.

---

# Example Workflow

Input:

```text
Build a minimal command-line Python expense tracker.
```

The system performs:

```text
1. Requirement analysis
2. Architecture planning
3. Task decomposition
4. Human approval
5. Code generation
6. Workspace construction
7. Syntax validation
8. Runtime validation
9. Functional testing
10. AST analysis
11. Failure diagnosis
12. Targeted repair
13. Git patching
14. Docker validation
15. Project export
16. Notification
```

---

# Failure Recovery

Suppose generated code produces:

```text
ModuleNotFoundError
```

The workflow can process the failure as:

```text
Runtime Failure
      ↓
Traceback captured
      ↓
Affected module identified
      ↓
AST structure inspected
      ↓
LLM receives relevant context
      ↓
Repair generated
      ↓
Git diff applied
      ↓
Syntax validation
      ↓
Runtime validation
      ↓
Functional validation
```

The system only considers the workflow successful after the required validation stages pass.

---

# Security Considerations

Generated code is potentially unsafe.

For this reason, the project incorporates sandboxed execution using Docker where available.

Additional safeguards include:

* execution timeouts
* retry limits
* isolated workspaces
* environment-variable based secrets
* Git-controlled changes
* human approval checkpoints

However:

> **This project should not be treated as a fully secure execution environment for arbitrary hostile code.**

Docker-based isolation is an engineering safeguard, not an absolute security boundary.

Do not execute untrusted code without appropriate infrastructure and security hardening.

---

# Design Trade-offs

This project intentionally combines probabilistic AI components with deterministic engineering infrastructure.

### LLMs

Good at:

* planning
* code generation
* debugging
* reasoning
* interpreting requirements

### Deterministic systems

Good at:

* compilation
* testing
* version control
* filesystem operations
* process execution
* container isolation
* AST parsing

The architecture therefore avoids relying on the LLM alone to determine whether its own output is correct.

---

# Current Limitations

The project is still an experimental engineering system rather than a replacement for a professional software development organization.

Known limitations include:

* LLM-generated architecture can still be imperfect.
* Generated projects may require additional human review.
* Model output can vary between executions.
* Dependency selection can be incorrect.
* Complex applications may require additional planning iterations.
* Docker isolation is not equivalent to a hardened production sandbox.
* Model availability and rate limits depend on external providers.
* Autonomous software development remains constrained by the reasoning and tool-use capabilities of the underlying models.

These limitations are part of the engineering problem the project is designed to explore.

---

# Future Development

The long-term roadmap focuses on improving autonomy, reliability, and software-engineering depth.

Potential future capabilities include:

* parallel agent execution
* dependency-aware task scheduling
* persistent agent memory
* semantic code retrieval
* vector-based project knowledge
* advanced test generation
* browser-based application testing
* API integration testing
* observability and tracing
* token and cost tracking
* execution metrics
* rollback and checkpointing
* richer human approval interfaces
* web-based orchestration dashboard
* automated deployment workflows

---

# What This Project Demonstrates

This project is intended to demonstrate practical understanding of:

### AI Engineering

* LLM integration
* multi-agent systems
* agent orchestration
* model routing
* prompt-driven planning
* structured LLM output

### Software Engineering

* state machines
* modular architecture
* automated testing
* Git workflows
* patch-based repair
* dependency management
* project scaffolding

### AI Reliability

* validation gates
* self-healing workflows
* failure feedback loops
* circuit breakers
* deterministic verification

### Infrastructure

* Docker
* sandboxed execution
* subprocess management
* filesystem isolation
* environment configuration

### Code Intelligence

* Python AST
* symbol extraction
* dependency awareness
* structural code analysis

---

# Why LangGraph?

LangGraph provides a natural abstraction for this project because the orchestrator is fundamentally a **stateful workflow**.

The system must maintain information such as:

```text
user requirement
project blueprint
tasks
generated files
validation results
errors
retry count
repair state
```

and route execution dynamically depending on the state.

For example:

```text
Validation PASS
      ↓
Continue

Validation FAIL
      ↓
Repair

Retry Limit Reached
      ↓
Stop
```

This is naturally represented as a state graph.

---

# Project Philosophy

The objective of this project is not:

> "Make an LLM generate code."

The objective is:

> **Build an engineering system around an LLM that can plan, execute, test, diagnose, repair, and deliver software.**

That distinction drives the architecture.

---

# Learning Outcomes

Building this project provides hands-on experience with:

* LLM APIs
* LangGraph
* multi-agent orchestration
* state management
* structured generation
* automated testing
* runtime execution
* Git automation
* Docker
* AST parsing
* model routing
* human-in-the-loop workflows
* software architecture
* autonomous coding systems

---

# Project Status

**Version 1:** Completed

**Version 2:** Advanced repository-engineering upgrade in progress

The current objective is to evolve the system from a multi-file code generation and repair engine into a more complete **AI software engineering operating system** capable of constructing and maintaining structured software repositories.

---

# Contributing

This project is primarily an experimental learning and engineering project.

Contributions, architectural discussions, and suggestions around:

* agent orchestration
* AI coding systems
* software validation
* sandboxing
* code intelligence
* autonomous software engineering

are welcome.

---

# License

This project is currently intended for educational and experimental purposes.

Add an appropriate open-source license before distributing the project publicly.

---

# Author

**Abbas Mashak Kini**

Computer Science & Engineering

Interested in:

* Artificial Intelligence
* Machine Learning
* AI Engineering
* Multi-Agent Systems
* Autonomous Software Engineering
* Developer Tools

---

# Final Perspective

Most LLM applications follow:

```text
Prompt → Response
```

This project explores a different model:

```text
Requirement
     ↓
Reason
     ↓
Plan
     ↓
Build
     ↓
Test
     ↓
Observe
     ↓
Repair
     ↓
Verify
     ↓
Version
     ↓
Deliver
```

The ultimate goal is to investigate how far a carefully engineered combination of **LLMs, stateful orchestration, deterministic validation, code intelligence, version control, sandboxing, and human oversight** can push autonomous software development.

```