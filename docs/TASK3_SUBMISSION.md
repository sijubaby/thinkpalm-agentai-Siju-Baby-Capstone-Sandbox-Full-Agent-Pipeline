# Task 3

**Project:** Maritime QA Agent (Python)  
**Track:** ThinkPalm maritime software QA  
**Repo path:** `C:\Users\siju.b\Projects\maritime-qa-agent`

---

## Task 3 rubric (completed)

| # | Requirement | Where / how to prove |
|---|-------------|----------------------|
| 1 | **Memory** | Short-term: `SessionMemory` (agent handoffs). Long-term: `data/runs/<run_id>/session.json`, `parsed_spec.json`, `tool_calls.json` |
| 2 | **Tool-calling** | 5 tools; `invoke_tool()`; optional **Groq LLM** (`use_llm: true`); log in `data/runs/*/tool_calls.json` |
| 3 | **2+ agents** | `SpecAnalystAgent` → `TestAuthorAgent` → `CoverageAuditorAgent` (sequential handoff) |
| 4 | **UI or CLI** | **UI+API:** `qa-agent ui`. **REST:** `qa-agent api`, `POST /api/v1/pipeline/run`. **CLI:** `qa-agent run` |
| 5 | **Domain-aligned** | Maritime specs: crew certification, AIS, port workflow |
| 6 | **E2E tested** | `qa-agent verify` + `pytest tests/test_pipeline_smoke.py` |

### Tools (custom + external)

| Tool | Type |
|------|------|
| `parse_maritime_spec` | Custom |
| `write_gherkin` | Custom |
| `write_playwright` | Custom |
| `generate_coverage_report` | Custom |
| `run_playwright` | **External** (pytest subprocess) |

---

## Mini project deliverables

| Deliverable | Location |
|-------------|----------|
| Working prototype | This repo + `pip install -e .` |
| Sample feature input | `data/samples/crew-certification-expiry-alerts.md`, `data/samples/ais-position-reporting-intervals.md` |
| Generated Gherkin | `data/out/demo/generated.feature` or run `qa-agent run` |
| Playwright scripts | `tests/e2e/test_generated_maritime.py` |
| Coverage gap report | `data/out/demo/coverage-report.html` (compliance flags + edge cases) |
| Pinned examples | `data/generated/example-run/` |
| Public GitHub + 8-min video | **Your action** — see `docs/DEMO_SCRIPT.md` |

---

## Commands for graders (copy-paste)

**Web UI (recommended for demo):**

```powershell
cd C:\Users\siju.b\Projects\maritime-qa-agent
.\.venv\Scripts\activate
pip install -e .
qa-agent ui
```

**CLI verification:**

```powershell
pip install -e .
qa-agent verify
start out\verify-crew\coverage-report.html
pytest tests\test_pipeline_smoke.py tests\test_task3_requirements.py -v
```

Optional Playwright:

```powershell
pip install -e ".[dev]"
playwright install chromium
pytest tests\e2e -v
```

---

## What the coverage report must show (mini project)

- Requirement matrix with **Yes/No** per REQ-ID  
- **Gaps** for requirements without full Gherkin + Playwright coverage  
- **Compliance flags** (e.g. `COMPLIANCE_ALERT_SCHEDULE`, `SAFETY_CRITICAL_SILENT_FAILURE`)  
- **Untested edge cases** (REQ-07, REQ-08, REQ-09 for crew-cert)

This demonstrates the assistant finds safety/compliance gaps — not only happy-path generation.

---

## 8-minute demo checklist

1. Show `data/samples/crew-certification-expiry-alerts.md`  
2. Run `qa-agent run -s data/samples/... -d crew-cert -o data/out/demo`  
3. Show agent panels + `data/runs/<id>/tool_calls.json`  
4. Open Gherkin + Playwright test  
5. Open HTML report — **compliance flags** and **edge cases**  
6. (Optional) `pytest tests/e2e -k block_embarkation`  
7. GitHub URL + second domain (AIS)

See `docs/DEMO_SCRIPT.md` for timing.
