from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from maritime_qa.agents.coverage_auditor import CoverageAuditorAgent
from maritime_qa.agents.spec_analyst import SpecAnalystAgent
from maritime_qa.agents.test_author import TestAuthorAgent
from maritime_qa.memory.store import RunStore, SessionMemory
from maritime_qa.models import PipelineResult, parsed_spec_from_dict

console = Console()


def run_pipeline(
    output_dir: Path,
    runs_dir: Path,
    spec_path: Path | None = None,
    spec_text: str | None = None,
    domain: str | None = None,
    use_llm: bool = False,
    run_playwright: bool = True,
    llm_provider: str | None = None,
) -> PipelineResult:
    """Execute the three-agent maritime QA pipeline."""
    from maritime_qa.tools.domain_infer import infer_domain_from_description

    if spec_text is None:
        if spec_path is None or not spec_path.is_file():
            raise ValueError("Provide spec_text or a valid spec_path")
        spec_text = spec_path.read_text(encoding="utf-8")
    elif spec_path is None:
        spec_path = None

    if not domain:
        domain = infer_domain_from_description(spec_text)

    output_dir.mkdir(parents=True, exist_ok=True)

    memory = SessionMemory()
    memory.set("spec_text", spec_text)
    memory.set("spec_path", str(spec_path) if spec_path else None)
    memory.set("domain", domain)
    memory.set("output_dir", str(output_dir))
    memory.set("run_playwright", run_playwright)

    run_store = RunStore(runs_dir)
    run_id = run_store.new_run_id()
    memory.set("run_id", run_id)

    agents = [SpecAnalystAgent(), TestAuthorAgent(), CoverageAuditorAgent()]

    memory.set("use_llm", use_llm)
    memory.set("llm_provider_pref", llm_provider)
    if use_llm:
        _run_with_llm_orchestration(memory, agents, llm_provider=llm_provider)
    else:
        for agent in agents:
            console.print(Panel(f"[bold]{agent.name}[/bold] running…", expand=False))
            agent.run(memory)

    parsed = parsed_spec_from_dict(memory.get("parsed_spec"))
    coverage = memory.get("coverage_report", {})

    artifacts = {
        "gherkin": memory.get("gherkin_path", ""),
        "playwright": memory.get("playwright_path", ""),
        "report_md": coverage.get("report_md", str(output_dir / "coverage-report.md")),
        "report_html": coverage.get("report_html", str(output_dir / "coverage-report.html")),
        "tool_calls": str(runs_dir / run_id / "tool_calls.json"),
    }
    run_store.save(run_id, memory, artifacts)

    _print_summary(memory, coverage)

    return PipelineResult(
        run_id=run_id,
        output_dir=str(output_dir),
        parsed_spec=parsed,
        gherkin_path=artifacts["gherkin"],
        playwright_path=artifacts["playwright"],
        report_md_path=artifacts["report_md"],
        report_html_path=artifacts["report_html"],
    )


def _print_summary(memory: SessionMemory, coverage: dict) -> None:
    table = Table(title="Pipeline summary")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Run ID", memory.get("run_id", ""))
    table.add_row("Coverage", f"{coverage.get('coverage_percent', 0)}%")
    table.add_row("Compliance flags", str(coverage.get("compliance_gap_count", 0)))
    pw = memory.get("playwright_results") or {}
    table.add_row("Playwright", pw.get("summary", "skipped"))
    console.print(table)
    console.print(f"[green]Artifacts[/green] → {memory.get('output_dir')}")
    console.print(f"[green]Memory[/green] → data/runs/{memory.get('run_id')}/tool_calls.json")


def _run_with_llm_orchestration(
    memory: SessionMemory,
    agents: list,
    llm_provider: str | None = None,
) -> None:
    from maritime_qa.api.llm import run_agent_with_llm
    from maritime_qa.api.llm_config import is_llm_available, resolve_llm_config

    cfg = resolve_llm_config(llm_provider)
    if not cfg:
        console.print(
            "[yellow]No GROQ_API_KEY or OPENAI_API_KEY — using rule-based tool pipeline[/yellow]"
        )
        for agent in agents:
            agent.run(memory)
        return
    console.print(f"[cyan]LLM enabled[/cyan] — {cfg.label} (dynamic tool-calling)")
    for agent in agents:
        console.print(Panel(f"[bold]{agent.name}[/bold] (LLM)…", expand=False))
        run_agent_with_llm(memory, agent.name, llm_provider=llm_provider)
    memory.set("llm_provider", cfg.provider)
    memory.set("llm_model", cfg.model)
