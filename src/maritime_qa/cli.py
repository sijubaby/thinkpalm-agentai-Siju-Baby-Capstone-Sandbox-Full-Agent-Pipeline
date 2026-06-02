from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from maritime_qa.orchestrator import run_pipeline
from maritime_qa.paths import OUT_DIR, RUNS_DIR, SAMPLES_DIR

app = typer.Typer(
    name="qa-agent",
    help="Maritime QA Agent — ThinkPalm Task 3 + mini project (Python)",
    no_args_is_help=True,
)


@app.command("run")
def run_cmd(
    spec: Path = typer.Option(..., "--spec", "-s", help="Path to feature spec markdown"),
    domain: str = typer.Option(
        "crew-cert",
        "--domain",
        "-d",
        help="Maritime domain: crew-cert | ais | port-workflow",
    ),
    output: Path = typer.Option(OUT_DIR / "demo", "--output", "-o", help="Output directory"),
    runs: Path = typer.Option(RUNS_DIR, "--runs", help="Long-term memory directory"),
    llm: bool = typer.Option(False, "--llm", help="Enable LLM orchestration (requires OPENAI_API_KEY)"),
    mock: bool = typer.Option(
        True,
        "--mock/--no-mock",
        help="Use rule-based tools (default, no API key)",
    ),
    skip_playwright: bool = typer.Option(
        False,
        "--skip-playwright",
        help="Skip external Playwright test execution",
    ),
) -> None:
    """Run Spec Analyst → Test Author → Coverage Auditor (Task 3 pipeline)."""
    if domain not in ("crew-cert", "ais", "port-workflow"):
        raise typer.BadParameter("domain must be crew-cert, ais, or port-workflow")
    if not spec.is_file():
        raise typer.BadParameter(f"Spec file not found: {spec}")

    result = run_pipeline(
        output_dir=output,
        runs_dir=runs,
        spec_path=spec,
        domain=domain,
        use_llm=llm and not mock,
        run_playwright=not skip_playwright,
    )
    rprint(f"\n[bold green]Done.[/bold green] Open: {result.report_html_path}")


@app.command("verify")
def verify_cmd(
    runs: Path = typer.Option(RUNS_DIR, "--runs", help="Long-term memory directory"),
) -> None:
    """End-to-end verification for Task 3 submission (crew-cert + ais)."""
    rprint("[bold]Task 3 E2E verification[/bold]\n")
    specs = [
        ("crew-cert", SAMPLES_DIR / "crew-certification-expiry-alerts.md", OUT_DIR / "verify-crew"),
        ("ais", SAMPLES_DIR / "ais-position-reporting-intervals.md", OUT_DIR / "verify-ais"),
    ]
    for domain, spec, out in specs:
        if not spec.is_file():
            raise typer.Exit(f"Missing sample: {spec}")
        rprint(f"→ {domain}: {spec.name}")
        run_pipeline(
            output_dir=out,
            runs_dir=runs,
            spec_path=spec,
            domain=domain,
            run_playwright=False,
        )

    rprint("\n[bold green]Verification complete.[/bold green]")
    rprint(f"Check: {OUT_DIR / 'verify-crew' / 'coverage-report.html'} (compliance flags)")
    rprint(f"Check: {OUT_DIR / 'verify-ais' / 'coverage-report.html'}")
    rprint(f"Check: {RUNS_DIR}/*/tool_calls.json (tool-calling log)")
    rprint("Run Playwright: pip install -e \".[dev]\" && playwright install chromium && pytest tests/e2e -v")


@app.command("ui")
def ui_cmd(
    port: int = typer.Option(8770, "--port", "-p", help="Web UI + API port"),
    no_browser: bool = typer.Option(False, "--no-browser", help="Do not open browser automatically"),
) -> None:
    """Launch web UI and REST API on the same port."""
    from maritime_qa.api.handler import start_server

    rprint(f"[bold]Starting Maritime QA UI + API[/bold] on port {port}")
    start_server(port=port, open_browser=not no_browser, serve_ui=True)


@app.command("api")
def api_cmd(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8770, "--port", "-p", help="API port"),
) -> None:
    """Start REST API only (no browser UI)."""
    from maritime_qa.api.handler import start_server

    rprint(f"[bold]Maritime QA REST API[/bold] → http://{host}:{port}/api/v1/health")
    start_server(host=host, port=port, open_browser=False, serve_ui=False)


@app.command("domains")
def domains_cmd() -> None:
    """List supported maritime domains and sample specs."""
    rprint("[bold]Domains[/bold]")
    rprint(f"  crew-cert      → {SAMPLES_DIR / 'crew-certification-expiry-alerts.md'}")
    rprint(f"  ais            → {SAMPLES_DIR / 'ais-position-reporting-intervals.md'}")
    rprint(f"  port-workflow  → {SAMPLES_DIR / 'port-arrival-departure-workflow.md'}")


if __name__ == "__main__":
    app()
