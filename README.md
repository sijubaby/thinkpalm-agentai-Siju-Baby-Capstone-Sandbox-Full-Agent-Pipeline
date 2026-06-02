# Maritime QA Agent (Python)

> Agentic test automation assistant for maritime software QA.  
> Paste a feature description → get **Gherkin BDD scenarios**, **Playwright automation scripts**, and a **coverage gap + compliance report** — powered by a 3-agent AI pipeline with optional Groq LLM.

## Quick Start

### 1. Install

```powershell
cd C:\Users\siju.b\Projects\maritime-qa-agent
.\.venv\Scripts\python.exe -m pip install -e .
```

Optional — enable Groq LLM for dynamic AI-generated results:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[llm]"
copy .env.example .env
# Open .env and set: GROQ_API_KEY=your_key_here
```

### 2. Launch Web UI

```powershell
scripts\run-ui.bat
```

Or manually:

```powershell
.\.venv\Scripts\python.exe -m maritime_qa.api
```

Opens **http://127.0.0.1:8770** in your browser.

> If `qa-agent` is not recognised, use `.\.venv\Scripts\qa-agent.exe` directly — it is only on PATH after venv activation.

---

## Web UI Features (Latest — 02-06-2026)

| Area | What it does |
|------|--------------|
| **Feature Description** | Free-text input (up to 2000 chars) for any maritime feature |
| **RUN PIPELINE** | Triggers the 3-agent pipeline and streams results |
| **Agent Workflow sidebar** | Live step indicators: Requirement Analysis → BDD Generation → Playwright → Coverage & Compliance |
| **Output tabs** | Requirements, Gherkin Tests, Playwright Scripts, Coverage Report, Compliance Report, Execution Logs |
| **History panel (right)** | Lists all past runs with search, reload, delete per run, and Clear All History |
| **Groq LLM** | Auto-enabled when `GROQ_API_KEY` is set — uses `llama-3.3-70b-versatile` |

---

## Task 3 Checklist

| Requirement | Implementation |
|-------------|----------------|
| **Memory** | Short-term: `SessionMemory` during agent handoffs. Long-term: each run saved under `data/runs/<run_id>/` (`session.json`, `tool_calls.json`, `parsed_spec.json`, input description). History panel reloads past runs from memory. |
| **Tool-calling** | 5 tools: `parse_maritime_spec`, `write_gherkin`, `write_playwright`, `generate_coverage_report`, `run_playwright` (external via pytest). All calls logged per run. Optional Groq LLM for dynamic orchestration. |
| **2+ agents** | `SpecAnalystAgent` → `TestAuthorAgent` → `CoverageAuditorAgent` (sequential pipeline, clear roles) |
| **Working UI / CLI** | Web UI at http://127.0.0.1:8770 + REST API (`POST /api/v1/pipeline/run`) + CLI (`qa-agent run`, `qa-agent verify`) |
| **Domain-aligned** | Maritime domains: crew certification expiry, AIS position reporting, port arrival/departure (auto-detected from input) |
| **E2E tested** | `qa-agent verify` + `pytest tests/test_pipeline_smoke.py tests/test_task3_requirements.py` |

---

## Agent Pipeline Architecture

```
User input (feature description)
        │
        ▼
  Orchestrator
        │
        ├─► SpecAnalystAgent      → parse_maritime_spec
        │       extracts REQ-IDs, rules, edge cases
        │
        ├─► TestAuthorAgent       → write_gherkin
        │                         → write_playwright
        │       generates BDD scenarios + Playwright scripts
        │
        └─► CoverageAuditorAgent  → generate_coverage_report
                                  → run_playwright (optional)
                generates HTML/MD coverage + compliance flags
                                  │
                                  ▼
                         data/runs/<run_id>/
                         (session, tool calls, parsed spec — long-term memory)
```

---

## CLI Commands

```powershell
# Run full pipeline on a sample
qa-agent run -s data/samples/crew-certification-expiry-alerts.md -d crew-cert -o data/out/demo

# Verify installation (crew-cert sample end-to-end)
qa-agent verify

# Start web UI + API server
qa-agent ui

# Start API server only
qa-agent api
```

---

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Server health + LLM status |
| `POST` | `/api/v1/pipeline/run` | Run full pipeline |
| `GET` | `/api/v1/runs` | List all saved runs (history) |
| `GET` | `/api/v1/runs/{run_id}` | Get a specific past run |
| `DELETE` | `/api/v1/runs/{run_id}` | Delete a specific run |
| `DELETE` | `/api/v1/runs` | Clear all history |
| `GET` | `/api/v1/samples` | List available sample specs |

Full OpenAPI spec: [`docs/openapi.json`](docs/openapi.json) | Docs: [`docs/API.md`](docs/API.md)

---

## Supported Maritime Domains

| `--domain` | Sample file |
|------------|-------------|
| `crew-cert` | `data/samples/crew-certification-expiry-alerts.md` |
| `ais` | `data/samples/ais-position-reporting-intervals.md` |
| `port-workflow` | `data/samples/port-arrival-departure-workflow.md` |

Domain is **auto-detected** from description text when `--domain auto` (default in UI).

---
## Run Tests

```powershell
# Core tests (API, pipeline, task3 rubric, groq config)
.\.venv\Scripts\python.exe -m pytest tests\test_api.py tests\test_task3_requirements.py tests\test_pipeline_smoke.py tests\test_groq_config.py -v

# Full suite (excludes browser e2e)
.\.venv\Scripts\python.exe -m pytest tests\ --ignore=tests\e2e -v

# Playwright e2e (requires chromium)
pip install -e ".[dev]"
playwright install chromium
pytest tests\e2e -v
```

---
## Project Structure

```
maritime-qa-agent/
├── .env.example              # Copy to .env — add GROQ_API_KEY
├── pyproject.toml
├── README.md
├── docs/                     # API.md, DEMO_SCRIPT.md, TASK3_SUBMISSION.md, openapi.json
├── scripts/
│   ├── run-ui.bat            # Double-click to launch (Windows)
│   └── run-ui.ps1
├── data/
│   ├── samples/              # Maritime feature spec inputs
│   ├── runs/                 # Long-term memory per run (auto-generated)
│   ├── out/                  # Generated Gherkin, Playwright, reports (auto-generated)
│   └── generated/            # Pinned demo artifacts for submission
├── src/maritime_qa/
│   ├── agents/               # SpecAnalystAgent, TestAuthorAgent, CoverageAuditorAgent
│   ├── api/                  # REST handler, service, Groq LLM integration
│   ├── memory/               # SessionMemory + run persistence store
│   ├── tools/                # 5 tools: parse_spec, gherkin, playwright_gen, coverage, playwright_runner
│   ├── ui/static/index.html  # Redesigned web UI (02-06-2026)
│   ├── cli.py                # qa-agent CLI (Typer)
│   ├── orchestrator.py
│   └── models.py
└── tests/
    ├── test_api.py
    ├── test_pipeline_smoke.py
    ├── test_task3_requirements.py
    ├── test_groq_config.py
    └── e2e/test_generated_maritime.py
```

Full path constants: import from `maritime_qa.paths` (`PROJECT_ROOT`, `SAMPLES_DIR`, `RUNS_DIR`, `OUT_DIR`, `GENERATED_DIR`).
