# Maritime QA Agent — REST API

Base URL (default): `http://127.0.0.1:8765`

Start server (UI + API):

```powershell
qa-agent ui
```

API only:

```powershell
qa-agent api
```

## Authentication (optional)

Set environment variable:

```text
MARITIME_QA_API_KEY=your-secret-key
```

Send header on protected endpoints:

```text
X-API-Key: your-secret-key
```

## Endpoints

### `GET /api/v1/health`

```powershell
curl http://127.0.0.1:8765/api/v1/health
```

### `GET /api/v1/samples`

Returns crew-cert, AIS, and port-workflow sample descriptions.

### `POST /api/v1/pipeline/run`

**Request:**

```json
{
  "description": "# Feature: Crew Certification...\n\n## Business rules\n1. Alerts at 90/30/7 days...",
  "domain": "auto",
  "run_playwright": false,
  "use_llm": false
}
```

| Field | Description |
|-------|-------------|
| `description` | **Required.** Feature text (markdown/plain). |
| `domain` | `auto` (default), `crew-cert`, `ais`, or `port-workflow`. |
| `run_playwright` | Run external Playwright tool via pytest. |
| `use_llm` | Use OpenAI API + tool-calling (needs `OPENAI_API_KEY`). |

**Example (PowerShell):**

```powershell
$body = @{
  description = Get-Content samples/description-crew-cert.txt -Raw
  domain = "auto"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8765/api/v1/pipeline/run `
  -Method POST -Body $body -ContentType "application/json"
```

**Response (excerpt):**

```json
{
  "run_id": "20260601-120000-abc123",
  "detected_domain": "crew-cert",
  "coverage_percent": 44.4,
  "compliance_gap_count": 2,
  "gaps": ["REQ-02: ..."],
  "artifacts": {
    "gherkin": "Feature: ...",
    "playwright": "...",
    "report_html": "<!DOCTYPE html>..."
  }
}
```

### `GET /api/v1/runs/{run_id}`

Fetch stored run metadata, tool calls, and parsed spec.

### `GET /api/v1/runs/{run_id}/artifacts/report.html`

Download HTML coverage report for a run.

## Groq / OpenAI LLM (dynamic results)

```powershell
copy .env.example .env
# Set GROQ_API_KEY=gsk_...   from https://console.groq.com/keys
.\.venv\Scripts\python.exe -m pip install -e ".[llm]"
```

If you see `unexpected keyword argument 'proxies'`, fix httpx compatibility:

```powershell
.\.venv\Scripts\python.exe -m pip install "httpx>=0.23,<0.28"
```

```json
POST /api/v1/pipeline/run
{
  "description": "...",
  "use_llm": true,
  "llm_provider": "groq"
}
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | — | Groq API key (preferred) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq chat model |
| `LLM_PROVIDER` | auto | `groq` or `openai` |
| `OPENAI_API_KEY` | — | Fallback if no Groq key |

Agents use **tool-calling** (Groq OpenAI-compatible API) to run the same pipeline tools with LLM-driven orchestration.

## UI integration

The web UI calls the same API:

- `GET /api/samples` → sample texts
- `POST /api/run` → alias of `/api/v1/pipeline/run` (UI-compatible response)

Legacy `/api/run` remains for the browser UI.
