# Documentation index

| Document | Read it for |
| --- | --- |
| [../README.md](../README.md) | Product overview, features, pipeline, dashboard guide, limitations |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Install, configure and run locally; troubleshooting |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Process model, layers, run sequence, data ownership |
| [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) | Module reference, state, Gemini contract, telemetry, extension points |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | All 36 routes, request bodies, error behaviour, missing endpoints |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Service operation, proxies, probes, container notes |

## Screenshots

| File | State |
| --- | --- |
| [assets/dashboard.png](assets/dashboard.png) | Default dashboard, idle pipeline |
| [assets/web-terminal.png](assets/web-terminal.png) | Web terminal tab with xterm mounted |
| [assets/concept-modal.png](assets/concept-modal.png) | DLP concept explainer modal |

All three were captured from the running app with headless Chrome; no mockups.

## Source of truth

If a document and the code disagree, the code is right and the document should be
fixed. The areas most worth re-checking after changes:

* route count (`server.py`) — currently 36;
* telemetry event names (`orchestrator/pipeline.py`);
* the generated-file contract (`dict[path, contents]`);
* which stages are real vs illustrative (`AST_INDEXED`, `VECTORS_EMBEDDED`).
