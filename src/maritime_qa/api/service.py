from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from maritime_qa.orchestrator import run_pipeline
from maritime_qa.paths import OUT_DIR, PROJECT_ROOT, RUNS_DIR
from maritime_qa.tools.domain_infer import infer_domain_from_description


def execute_pipeline(
    description: str,
    *,
    domain: str | None = None,
    run_playwright: bool = False,
    use_llm: bool = False,
    llm_provider: str | None = None,
    output_subdir: str = "api-latest",
    runs_dir: Path | None = None,
) -> dict[str, Any]:
    """Run the agent pipeline and return a JSON-serializable API response."""
    text = description.strip()
    if not text:
        raise ValueError("description is required")

    resolved_domain = domain if domain and domain != "auto" else infer_domain_from_description(text)
    if resolved_domain not in ("crew-cert", "ais", "port-workflow"):
        raise ValueError("domain must be auto, crew-cert, ais, or port-workflow")

    out_root = OUT_DIR / output_subdir
    runs = runs_dir or RUNS_DIR

    result = run_pipeline(
        output_dir=out_root,
        runs_dir=runs,
        spec_text=text,
        domain=resolved_domain,
        use_llm=use_llm,
        run_playwright=run_playwright,
        llm_provider=llm_provider,
    )

    run_dir = runs / result.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "input-description.md").write_text(text, encoding="utf-8")

    tool_calls = _read_json(run_dir / "tool_calls.json", [])
    parsed_spec = _read_json(run_dir / "parsed_spec.json", {})
    coverage = _coverage_from_session(run_dir / "session.json")

    pw_summary = "skipped"
    for entry in reversed(tool_calls):
        if entry.get("tool") == "run_playwright" and entry.get("type") == "result":
            pw_summary = entry.get("result_summary", "done")
            break

    session = _read_json(run_dir / "session.json", {})
    session_data = session.get("data", {})

    return {
        "run_id": result.run_id,
        "detected_domain": resolved_domain,
        "llm_provider": session_data.get("llm_provider"),
        "llm_model": session_data.get("llm_model"),
        "dynamic_llm": use_llm and bool(session_data.get("llm_provider")),
        "coverage_percent": coverage.get("coverage_percent"),
        "compliance_gap_count": coverage.get("compliance_gap_count"),
        "gaps": coverage.get("gaps", []),
        "playwright_summary": pw_summary,
        "tool_calls": tool_calls,
        "parsed_spec": parsed_spec,
        "artifacts": {
            "gherkin": _read_file(Path(result.gherkin_path)),
            "playwright": _read_file(Path(result.playwright_path)),
            "report_md": _read_file(Path(result.report_md_path)),
            "report_html": _read_file(Path(result.report_html_path)),
        },
        "links": {
            "run": f"/api/v1/runs/{result.run_id}",
            "report_html": f"/api/v1/runs/{result.run_id}/artifacts/report.html",
        },
    }


def list_runs(*, runs_dir: Path | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """List persisted runs (long-term memory), newest first."""
    runs = runs_dir or RUNS_DIR
    if not runs.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for run_dir in sorted(runs.iterdir(), key=lambda p: p.name, reverse=True):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        meta = _read_json(run_dir / "meta.json", {})
        session = _read_json(run_dir / "session.json", {})
        data = session.get("data", {})
        coverage = data.get("coverage_report", {})
        desc = _read_file(run_dir / "input-description.md") or data.get("spec_text", "")
        preview = " ".join(desc.split())
        if len(preview) > 140:
            preview = preview[:137] + "…"

        parsed = _read_json(run_dir / "parsed_spec.json", {})
        title = parsed.get("feature_title") or preview[:60] or run_id

        items.append(
            {
                "run_id": run_id,
                "saved_at": meta.get("saved_at"),
                "detected_domain": data.get("domain"),
                "coverage_percent": coverage.get("coverage_percent"),
                "compliance_gap_count": coverage.get("compliance_gap_count"),
                "description_preview": preview,
                "title": title,
                "status": "completed",
            }
        )
        if len(items) >= limit:
            break
    return items


def get_run(run_id: str, runs_dir: Path | None = None) -> dict[str, Any]:
    """Fetch a previous run by ID."""
    runs = runs_dir or RUNS_DIR
    run_dir = runs / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run not found: {run_id}")

    meta = _read_json(run_dir / "meta.json", {})
    session = _read_json(run_dir / "session.json", {})
    data = session.get("data", {})
    coverage = data.get("coverage_report", {})

    return {
        "run_id": run_id,
        "meta": meta,
        "detected_domain": data.get("domain"),
        "llm_provider": data.get("llm_provider"),
        "llm_model": data.get("llm_model"),
        "coverage_percent": coverage.get("coverage_percent"),
        "compliance_gap_count": coverage.get("compliance_gap_count"),
        "gaps": coverage.get("gaps", []),
        "tool_calls": _read_json(run_dir / "tool_calls.json", []),
        "parsed_spec": _read_json(run_dir / "parsed_spec.json", {}),
        "description": _read_file(run_dir / "input-description.md") or data.get("spec_text", ""),
    }


def get_run_for_ui(run_id: str, runs_dir: Path | None = None) -> dict[str, Any]:
    """Full run payload for the web UI (description + artifacts)."""
    runs = runs_dir or RUNS_DIR
    run_dir = runs / run_id
    base = get_run(run_id, runs_dir)
    meta = base.get("meta", {})
    session = _read_json(run_dir / "session.json", {})
    data = session.get("data", {})

    def _artifact_path(key: str) -> Path | None:
        raw = meta.get("artifacts", {}).get(key) or data.get(f"{key}_path")
        if not raw:
            cov = data.get("coverage_report") or {}
            raw = cov.get(key) or cov.get(f"{key}_path")
        return Path(raw) if raw else None

    gherkin_path = _artifact_path("gherkin")
    playwright_path = _artifact_path("playwright")
    report_html_path = _artifact_path("report_html")
    if not report_html_path:
        report_html_path = _artifact_path("report_md")

    gherkin = _read_file(gherkin_path) if gherkin_path else ""
    playwright = _read_file(playwright_path) if playwright_path else ""
    report_html = _read_file(report_html_path) if report_html_path else ""

    return {
        **base,
        "gherkin": gherkin or data.get("gherkin_text", ""),
        "playwright": playwright or data.get("playwright_text", ""),
        "report_html": report_html,
    }


def delete_run(run_id: str, runs_dir: Path | None = None) -> None:
    """Remove one persisted run from memory."""
    run_dir = (runs_dir or RUNS_DIR) / run_id
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run not found: {run_id}")
    shutil.rmtree(run_dir)


def clear_runs(runs_dir: Path | None = None) -> int:
    """Delete all persisted runs. Returns count removed."""
    runs = runs_dir or RUNS_DIR
    if not runs.is_dir():
        return 0
    count = 0
    for run_dir in list(runs.iterdir()):
        if run_dir.is_dir():
            shutil.rmtree(run_dir)
            count += 1
    return count


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _coverage_from_session(session_path: Path) -> dict[str, Any]:
    if not session_path.is_file():
        return {}
    session = json.loads(session_path.read_text(encoding="utf-8"))
    return session.get("data", {}).get("coverage_report", {})
