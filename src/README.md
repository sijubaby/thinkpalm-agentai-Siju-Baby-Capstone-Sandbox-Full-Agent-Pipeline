# Maritime QA Agent (Python)

**Task 3 + ThinkPalm maritime mini project** — agentic pipeline that reads a feature spec, generates Gherkin + Playwright tests, and produces a **coverage gap report with compliance flags**.

## Web UI (Task 3 interface)

```powershell
cd C:\Users\siju.b\Projects\maritime-qa-agent
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -e ".[llm]"
.\.venv\Scripts\qa-agent.exe ui
```

Or double-click **`scripts\run-ui.bat`** (no `activate` needed).

If `qa-agent` is not recognized, you must use **`.\.venv\Scripts\qa-agent.exe`** — it is not on PATH until the venv is activated.

Opens **http://127.0.0.1:8770** — paste a **feature description**, click **Generate test assets**. Same server exposes the **REST API** at `/api/v1/`. Enable **dynamic results** with Groq — see [docs/API.md](docs/API.md).

Project layout: **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)**

```powershell
copy .env.example .env
# Add GROQ_API_KEY from https://console.groq.com/keys
pip install -e ".[llm]"
```

```powershell
qa-agent api          # API only
curl http://127.0.0.1:8770/api/v1/health
```

## Quick start (submission)

```powershell
cd C:\Users\siju.b\Projects\maritime-qa-agent
.\.venv\Scripts\activate
pip install -e .
qa-agent verify
start data\out\verify-crew\coverage-report.html
```

Full rubric mapping: **[docs/TASK3_SUBMISSION.md](docs/TASK3_SUBMISSION.md)**

## Task 3 checklist

| Requirement | Implementation |
|-------------|----------------|
| **Memory** | `SessionMemory` + `data/runs/<id>/` (`session.json`, `tool_calls.json`, `parsed_spec.json`) |
| **Tool-calling** | 4 custom + 1 external (`run_playwright` via pytest) — logged per run |
| **2+ agents** | Spec Analyst → Test Author → Coverage Auditor |
| **UI / CLI** | `qa-agent ui` (web) or `qa-agent run` / `verify` |
| **Maritime domain** | Crew cert, AIS, port workflow samples |
| **E2E** | `qa-agent verify` + pytest |

## Run pipeline

```powershell
qa-agent run -s data/samples/crew-certification-expiry-alerts.md -d crew-cert -o data/out/demo
```

Outputs: `generated.feature`, `test_generated_maritime.py`, `coverage-report.html`, `data/runs/<run_id>/`.

## Domains

| `--domain` | Sample |
|------------|--------|
| `crew-cert` | `data/samples/crew-certification-expiry-alerts.md` |
| `ais` | `data/samples/ais-position-reporting-intervals.md` |
| `port-workflow` | `data/samples/port-arrival-departure-workflow.md` |

## Playwright

```powershell
pip install -e ".[dev]"
playwright install chromium
pytest tests/e2e -v
```

## Mini project deliverables

| Item | Status |
|------|--------|
| Prototype | This repo |
| Sample specs | `data/samples/` |
| Gherkin + Playwright | Generated under `data/out/` |
| Coverage report | HTML + MD with compliance flags |
| GitHub + 8-min video | See `docs/DEMO_SCRIPT.md` |

## Architecture

```
qa-agent CLI → Orchestrator
  → SpecAnalystAgent      → parse_maritime_spec
  → TestAuthorAgent       → write_gherkin, write_playwright
  → CoverageAuditorAgent  → run_playwright (external), generate_coverage_report
  → data/runs/<id>/ memory
```
