# Project structure

```
maritime-qa-agent/
├── .env.example              # Copy to .env (Groq API key, etc.)
├── .gitignore
├── pyproject.toml            # Package metadata, dependencies, pytest config
├── README.md
│
├── docs/                     # Documentation
│   ├── API.md
│   ├── DEMO_SCRIPT.md
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── TASK3_SUBMISSION.md
│   └── openapi.json
│
├── scripts/                  # Helper launchers (Windows)
│   ├── run-ui.bat
│   └── run-ui.ps1
│
├── data/                     # Non-source data & runtime output
│   ├── samples/              # Maritime feature spec inputs
│   ├── runs/                 # Long-term memory (gitignored contents)
│   ├── out/                  # Generated Gherkin, Playwright, reports
│   └── generated/            # Pinned demo artifacts for submission
│
├── src/                      # Application source (installable package)
│   └── maritime_qa/
│       ├── __init__.py
│       ├── paths.py          # Central path constants
│       ├── cli.py            # `qa-agent` Typer CLI
│       ├── orchestrator.py
│       ├── models.py
│       ├── agents/           # Spec analyst, test author, coverage auditor
│       ├── api/              # REST + HTTP UI server
│       ├── memory/           # Session + run persistence
│       ├── tools/            # Gherkin, Playwright, coverage, etc.
│       └── ui/
│           └── static/
│               └── index.html
│
└── tests/                    # Pytest suite
    ├── test_api.py
    ├── test_pipeline_smoke.py
    ├── test_task3_requirements.py
    ├── test_groq_config.py
    └── e2e/
        ├── fixtures/
        └── test_generated_maritime.py
```

## Path constants in code

Import from `maritime_qa.paths`:

| Constant        | Location                          |
|-----------------|-----------------------------------|
| `PROJECT_ROOT`  | Repository root                   |
| `SAMPLES_DIR`   | `data/samples/`                   |
| `RUNS_DIR`      | `data/runs/` (memory per run)     |
| `OUT_DIR`       | `data/out/` (latest artifacts)    |
| `GENERATED_DIR` | `data/generated/` (pinned demos)  |

## What is gitignored

- `data/runs/*` — per-run session, tool calls, parsed spec
- `data/out/*` — generated test assets from UI/CLI
- `.venv/`, `.env`, caches
