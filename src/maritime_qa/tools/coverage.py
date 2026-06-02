from __future__ import annotations

from pathlib import Path

from maritime_qa.models import (
    ComplianceGap,
    CoverageReport,
    CoverageRow,
    parsed_spec_from_dict,
)

# Gherkin + Playwright signals required to mark a requirement as fully covered.
_REQ_SIGNALS: dict[str, dict[str, list[str]]] = {
    "crew-cert": {
        "REQ-01": {"gherkin": ["90-day", "90 day"], "playwright": ["test_90", "alert-90"]},
        "REQ-02": {"gherkin": ["30-day", "30 day"], "playwright": ["test_30", "alert-30"]},
        "REQ-03": {"gherkin": ["7-day", "7 day"], "playwright": ["test_7", "alert-7"]},
        "REQ-04": {"gherkin": ["embarkation is blocked", "certificate expired"], "playwright": ["test_block_embarkation", "embarkation-blocked"]},
        "REQ-05": {"gherkin": ["dashboard"], "playwright": ["dashboard", "alert"]},
        "REQ-06": {"gherkin": ["pending", "remains blocked"], "playwright": ["test_pending", "pending"]},
        "REQ-07": {"gherkin": ["earliest expiry", "multiple"], "playwright": ["earliest", "multiple cert"]},
        "REQ-08": {"gherkin": ["midnight", "timezone"], "playwright": ["midnight", "timezone"]},
        "REQ-09": {"gherkin": ["delayed", "alert job"], "playwright": ["delayed", "alert_job"]},
    },
    "ais": {
        "REQ-01": {"gherkin": ["10 minute", "underway"], "playwright": ["underway", "10"]},
        "REQ-02": {"gherkin": ["anchor", "3 minute"], "playwright": ["anchor"]},
        "REQ-03": {"gherkin": ["stale track", "20 minute"], "playwright": ["test_stale", "stale-alert"]},
        "REQ-04": {"gherkin": ["invalid mmsi", "rejected"], "playwright": ["test_invalid_mmsi", "reject"]},
        "REQ-05": {"gherkin": ["utc", "timestamp"], "playwright": ["utc", "timestamp"]},
        "REQ-06": {"gherkin": ["transponder reset", "gap"], "playwright": ["reset", "gap"]},
    },
    "port-workflow": {
        "REQ-01": {"gherkin": ["arrival", "berth"], "playwright": ["arrival", "berth"]},
        "REQ-02": {"gherkin": ["departure", "in-port"], "playwright": ["departure"]},
        "REQ-03": {"gherkin": ["clearance", "blocked"], "playwright": ["clearance", "block"]},
    },
}


def generate_coverage_report(
    parsed_spec: dict,
    gherkin_text: str,
    playwright_text: str,
    output_dir: str,
    playwright_results: dict | None = None,
) -> dict:
    """Tool: map spec requirements to tests and emit gap + compliance report."""
    spec = parsed_spec_from_dict(parsed_spec)
    gherkin_lower = gherkin_text.lower()
    pw_lower = playwright_text.lower()
    domain_signals = _REQ_SIGNALS.get(spec.domain, {})

    rows: list[CoverageRow] = []
    gaps: list[str] = []
    compliance_gaps: list[ComplianceGap] = []
    edge_missing: list[str] = []

    for req in spec.requirements:
        covered, ref = _requirement_covered(req.id, req.edge_case, domain_signals, gherkin_lower, pw_lower)
        rows.append(
            CoverageRow(
                requirement_id=req.id,
                title=req.title,
                covered=covered,
                test_reference=ref,
                compliance_tags=req.compliance_tags,
            )
        )
        if not covered:
            kind = "edge case" if req.edge_case else "requirement"
            gaps.append(f"{req.id}: {req.title} — no automated {kind} coverage")
        if req.edge_case and not covered:
            edge_missing.append(f"{req.id}: {req.title}")

    _add_compliance_flags(spec, gherkin_lower, pw_lower, compliance_gaps)

    covered_count = sum(1 for r in rows if r.covered)
    total = len(rows) or 1
    report = CoverageReport(
        feature_title=spec.feature_title,
        domain=spec.domain,
        rows=rows,
        gaps=gaps,
        compliance_gaps=compliance_gaps,
        coverage_percent=round(100.0 * covered_count / total, 1),
        edge_cases_missing=edge_missing,
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / "coverage-report.md"
    html_path = out / "coverage-report.html"
    md_path.write_text(_render_md(report, playwright_results), encoding="utf-8")
    html_path.write_text(_render_html(report, playwright_results), encoding="utf-8")
    return {
        "report_md": str(md_path),
        "report_html": str(html_path),
        "coverage_percent": report.coverage_percent,
        "compliance_gap_count": len(compliance_gaps),
        "gaps": gaps,
    }


def _requirement_covered(
    req_id: str,
    edge_case: bool,
    domain_signals: dict,
    gherkin_lower: str,
    pw_lower: str,
) -> tuple[bool, str | None]:
    signals = domain_signals.get(req_id)
    if not signals:
        return False, None

    g_ok = any(s in gherkin_lower for s in signals.get("gherkin", []))
    p_ok = any(s in pw_lower for s in signals.get("playwright", []))

    if edge_case:
        if g_ok and p_ok:
            return True, "generated.feature + test_generated_maritime.py"
        return False, None

    if g_ok and p_ok:
        return True, "generated.feature + test_generated_maritime.py"
    if g_ok:
        return False, "gherkin-only (missing Playwright automation)"
    return False, None


def _add_compliance_flags(spec, gherkin_lower: str, pw_lower: str, out: list[ComplianceGap]) -> None:
    combined = gherkin_lower + pw_lower
    checks = [
        (
            "COMPLIANCE_ALERT_SCHEDULE",
            lambda: all(x in combined for x in ["90", "30", "7"])
            and all(x in pw_lower for x in ["test_90", "test_30", "test_7"]),
            "HIGH",
            "90/30/7-day alerts must be asserted in both Gherkin and Playwright",
            "Add test_30_day_alert and test_7_day_alert Playwright tests with matching Gherkin",
        ),
        (
            "COMPLIANCE_EMBARKATION_BLOCK",
            lambda: "embarkation" in combined and "block" in combined and "test_block" in pw_lower,
            "HIGH",
            "Expired mandatory certificate must block embarkation in automated tests",
            "Scenario: block embarkation when mandatory certificate expired",
        ),
        (
            "COMPLIANCE_REPORTING_INTERVAL",
            lambda: "10" in combined and "minute" in combined,
            "MEDIUM",
            "Underway reporting interval must be validated",
            "Scenario: reject position report beyond 10-minute underway interval",
        ),
        (
            "DATA_INTEGRITY_AIS",
            lambda: "mmsi" in combined and "reject" in combined,
            "HIGH",
            "Invalid MMSI must be rejected with audit trail",
            "Scenario: reject invalid MMSI with integrity audit entry",
        ),
        (
            "SAFETY_CRITICAL_SILENT_FAILURE",
            lambda: ("stale" in combined or "delayed" in combined)
            and ("test_stale" in pw_lower or "delayed" in pw_lower),
            "HIGH",
            "Safety-critical failure paths (stale track / delayed alerts) need automation",
            "Scenario: stale track or delayed alert job still enforces block/alert",
        ),
    ]
    if spec.domain != "crew-cert":
        checks = [c for c in checks if c[0] != "COMPLIANCE_ALERT_SCHEDULE"]
    if spec.domain != "ais":
        checks = [c for c in checks if c[0] not in ("COMPLIANCE_REPORTING_INTERVAL", "DATA_INTEGRITY_AIS")]

    for tag, predicate, severity, message, suggestion in checks:
        if not predicate():
            if not any(g.tag == tag for g in out):
                out.append(
                    ComplianceGap(tag=tag, severity=severity, message=message, suggested_scenario=suggestion)
                )

    for hint in spec.compliance_hints:
        if hint.tag.startswith("COMPLIANCE") or hint.tag.startswith("SAFETY") or hint.tag.startswith("DATA"):
            if not any(g.tag == hint.tag for g in out):
                tag_present = hint.tag.lower().replace("_", " ")[:20] in combined
                if not tag_present and spec.domain == "crew-cert" and hint.tag == "SAFETY_CRITICAL_SILENT_FAILURE":
                    if "delayed" not in combined:
                        out.append(
                            ComplianceGap(
                                tag=hint.tag,
                                severity="HIGH",
                                message=hint.description,
                                suggested_scenario="Scenario: alert job delayed but embarkation still blocked when expired",
                            )
                        )


def _render_md(report: CoverageReport, playwright_results: dict | None) -> str:
    lines = [
        f"# Coverage Gap Report — {report.feature_title}",
        "",
        f"- **Domain:** {report.domain}",
        f"- **Coverage:** {report.coverage_percent}%",
        "",
    ]
    if playwright_results:
        lines.append(f"- **Playwright run:** {playwright_results.get('summary', 'n/a')}")
        lines.append("")
    lines.extend(
        [
            "## Requirement matrix",
            "",
            "| ID | Requirement | Covered | Compliance tags |",
            "|----|-------------|---------|-----------------|",
        ]
    )
    for row in report.rows:
        tags = ", ".join(row.compliance_tags) or "—"
        lines.append(
            f"| {row.requirement_id} | {row.title} | {'Yes' if row.covered else '**No**'} | {tags} |"
        )
    lines.extend(["", "## Gaps", ""])
    lines.extend(f"- {g}" for g in report.gaps) if report.gaps else lines.append("- None")
    lines.extend(["", "## Compliance flags", ""])
    if report.compliance_gaps:
        for g in report.compliance_gaps:
            lines.append(f"- **[{g.severity}] {g.tag}**: {g.message}")
            lines.append(f"  - Suggested: `{g.suggested_scenario}`")
    else:
        lines.append("- All compliance controls appear covered.")
    if report.edge_cases_missing:
        lines.extend(["", "## Untested edge cases (safety-critical)", ""])
        lines.extend(f"- {e}" for e in report.edge_cases_missing)
    return "\n".join(lines) + "\n"


def _render_html(report: CoverageReport, playwright_results: dict | None) -> str:
    pw_note = ""
    if playwright_results:
        pw_note = f"<p><strong>Playwright:</strong> {playwright_results.get('summary', 'n/a')}</p>"

    rows_html = "".join(
        f"<tr><td>{r.requirement_id}</td><td>{r.title}</td>"
        f"<td class=\"{'ok' if r.covered else 'gap'}\">{'Yes' if r.covered else 'No'}</td>"
        f"<td>{', '.join(r.compliance_tags) or '—'}</td></tr>"
        for r in report.rows
    )
    flags_html = "".join(
        f"<li class=\"flag\"><strong>[{g.severity}] {g.tag}</strong>: {g.message}"
        f"<br><em>Suggested: {g.suggested_scenario}</em></li>"
        for g in report.compliance_gaps
    ) or "<li>All compliance controls appear covered.</li>"
    gaps_html = "".join(f"<li>{g}</li>" for g in report.gaps) or "<li>None</li>"
    edge_html = "".join(f"<li class=\"gap\">{e}</li>" for e in report.edge_cases_missing) or "<li>None</li>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Coverage — {report.feature_title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 960px; }}
    .ok {{ color: #0a0; }} .gap {{ color: #c00; font-weight: bold; }}
    .flag {{ margin-bottom: 0.75rem; padding: 0.5rem; background: #fff5f5; border-left: 4px solid #c00; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    th {{ background: #f4f4f4; }}
    .banner {{ background: #e8f4fc; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <div class="banner">
    <strong>ThinkPalm Maritime QA</strong> — Coverage &amp; compliance gap report
  </div>
  <h1>Coverage Gap Report</h1>
  <p><strong>Feature:</strong> {report.feature_title}</p>
  <p><strong>Domain:</strong> {report.domain} &nbsp;|&nbsp; <strong>Coverage:</strong> {report.coverage_percent}%</p>
  {pw_note}
  <h2>Requirement matrix</h2>
  <table>
    <tr><th>ID</th><th>Requirement</th><th>Covered</th><th>Compliance</th></tr>
    {rows_html}
  </table>
  <h2>Gaps</h2>
  <ul>{gaps_html}</ul>
  <h2>Compliance flags</h2>
  <ul>{flags_html}</ul>
  <h2>Untested edge cases (safety-critical)</h2>
  <ul>{edge_html}</ul>
</body>
</html>
"""
