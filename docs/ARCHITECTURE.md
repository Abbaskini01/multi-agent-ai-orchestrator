# 🏛️ Neural Glass — System Architecture Specification (v1.0.0)

> This document details the internal design, agent communication loops, dependency pipelines, and sandbox mechanics powering the Neural Glass AI Engineering Operating System.

---

## 1. High-Level System Design

Neural Glass operates as a **hybrid multi-agent orchestrator** combining asynchronous event streams (WebSockets), fast HTTP REST endpoints, AST syntax feedback loops, and an Enterprise Knowledge Graph (EKG).

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENT LAYER                                      |
|                  (VS Code Extension / JetBrains / Web Dashboard)                  |
+------------------------------------------+----------------------------------------+
                                           |
                                  [ WS / REST API ]
                                           |
+------------------------------------------v----------------------------------------+
|                                ORCHESTRATION LAYER                                |
|                                   (server.py)                                     |
|                                                                                   |
|  +-----------------------+   +-----------------------+   +---------------------+  |
|  | Request Tracing /     |   | WebSocket Event Bus   |   | Plugin Middleware   |  |
|  | Metrics Middleware    |   | (/ws/orchestrate)     |   | Engine              |  |
|  +-----------------------+   +-----------------------+   +---------------------+  |
+------------------------------------------+----------------------------------------+
                                           |
+------------------------------------------v----------------------------------------+
|                              SPECIALIZED AGENTS ENGINE                            |
|                                                                                   |
|   +-------------------+    +--------------------+    +------------------------+   |
|   |  SystemArchitect  |    |   CodeGenerator    |    |    SecurityReviewer    |   |
|   +-------------------+    +--------------------+    +------------------------+   |
|   |  ProjectManager   |    |  DependencyIndexer |    |  DeploymentController  |   |
|   +-------------------+    +--------------------+    +------------------------+   |
+------------------------------------------+----------------------------------------+
                                           |
+------------------------------------------v----------------------------------------+
|                             CORE SUBSYSTEMS & ENGINES                             |
|                                                                                   |
|  +---------------------+  +---------------------+  +---------------------------+  |
|  | Knowledge Graph     |  | SAST & Compliance   |  | CI/CD Pipeline Generator  |  |
|  | (core/knowledge.py) |  | (core/security.py)  |  | (core/cicd_engine.py)     |  |
|  +---------------------+  +---------------------+  +---------------------------+  |
|  | Telemetry Analytics |  | Ephemeral Sandbox   |  | Team Collaboration        |  |
|  | (core/analytics.py) |  | (Kubernetes / Local)|  | (core/collaboration.py)   |  |
|  +---------------------+  +---------------------+  +---------------------------+  |
+-----------------------------------------------------------------------------------+

2. Multi-Agent Delegation Model
Tasks are parsed by the Project Manager Engine (core/pm_engine.py) and dynamically decomposed into structured phases:

SystemArchitectAgent: Analyzes requirements, checks workspace symbols via AST parsing, and defines interface contracts.

CodeGeneratorAgent: Generates code implementation files and runs closed-loop AST verification.

SecurityReviewerAgent: Scans generated outputs against SAST patterns (OWASP, hardcoded secrets, shell injections).

DeploymentController: Scaffolds CI/CD pipelines and runs post-deployment HTTP smoke tests (/api/cicd/deploy-verify).

3. Autonomous Self-Repair Loop
When code generation or refactoring is triggered, Neural Glass executes a closed-loop verification pipeline:

[ User Prompt / Code Request ]
              │
              ▼
    [ Synthesize Code ]
              │
              ▼
   [ AST Syntax Analysis ] ◄─── Fail ─── [ Self-Repair Engine ]
              │                                      ▲
            Pass                                     │
              │                                      │
              ▼                                      │
     [ Run Sandbox Test ] ─────── Fail ──────────────┘
              │
            Pass
              │
              ▼
   [ Commit to Sandbox ]

   4. Enterprise Knowledge Graph (EKG) Schema
The EKG (core/knowledge_graph.py) dynamically maps workspace entities into relational nodes and edges:

Node Types: Project, Module, Class, Function, Route, Commit

Edge Relations: DEFINED_IN, IMPORTS, CALLS, MODIFIED_BY, TESTED_BY

Impact Radius Analysis: Querying /api/knowledge/impact?target=<symbol> walks the graph adjacency list to calculate the change blast radius before code modifications are staged.