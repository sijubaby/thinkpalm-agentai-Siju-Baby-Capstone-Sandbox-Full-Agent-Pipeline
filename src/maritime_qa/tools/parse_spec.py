from __future__ import annotations

import re

from maritime_qa.models import ComplianceHint, ParsedSpec, Requirement, parsed_spec_to_dict

_DOMAIN_DEFAULTS: dict[str, dict] = {
    "crew-cert": {
        "feature_title": "Crew Certification Expiry Monitoring and Alerts",
        "requirements": [
            ("REQ-01", "90-day expiry alert", "Send alert 90 days before mandatory certificate expires.", ["COMPLIANCE_ALERT_SCHEDULE"]),
            ("REQ-02", "30-day expiry alert", "Send alert 30 days before mandatory certificate expires.", ["COMPLIANCE_ALERT_SCHEDULE"]),
            ("REQ-03", "7-day expiry alert", "Send alert 7 days before mandatory certificate expires.", ["COMPLIANCE_ALERT_SCHEDULE"]),
            ("REQ-04", "Block embarkation when expired", "Prevent sign-on/embarkation when mandatory certificate is expired.", ["COMPLIANCE_EMBARKATION_BLOCK", "SAFETY_CRITICAL_SILENT_FAILURE"]),
            ("REQ-05", "Dashboard visibility", "Alerts visible on crew certification dashboard.", []),
            ("REQ-06", "Pending renewal status", "Partial renewal shows PENDING and does not unblock embarkation.", []),
            ("REQ-07", "Earliest expiry scheduling", "Multiple certs use earliest expiry for alert schedule.", [], True),
            ("REQ-08", "Timezone midnight expiry", "Expiry at local midnight handled correctly.", [], True),
            ("REQ-09", "Delayed alert job", "Embarkation still blocked if alert job delayed but cert expired.", ["SAFETY_CRITICAL_SILENT_FAILURE"], True),
        ],
    },
    "ais": {
        "feature_title": "AIS Position Reporting Intervals",
        "requirements": [
            ("REQ-01", "Underway reporting interval", "Underway vessels report position at most every 10 minutes.", ["COMPLIANCE_REPORTING_INTERVAL"]),
            ("REQ-02", "At-anchor interval", "At anchor, interval may extend to 3 minutes in high-traffic config.", []),
            ("REQ-03", "Stale track alert", "Raise stale track when no report for 2x configured interval.", ["SAFETY_CRITICAL_SILENT_FAILURE"]),
            ("REQ-04", "Reject invalid MMSI", "Invalid or missing MMSI rejects report and logs integrity event.", ["DATA_INTEGRITY_AIS"]),
            ("REQ-05", "UTC timestamp required", "Reports include UTC timestamp and navigational status.", []),
            ("REQ-06", "Transponder reset gap", "Handle reporting gap after transponder reset.", [], True),
        ],
    },
    "port-workflow": {
        "feature_title": "Port Arrival and Departure Workflow",
        "requirements": [
            ("REQ-01", "Record port arrival", "System records actual arrival time at berth.", []),
            ("REQ-02", "Record port departure", "System records departure time and clears in-port status.", []),
            ("REQ-03", "Block departure without clearance", "Departure blocked if mandatory port clearance missing.", ["COMPLIANCE_EMBARKATION_BLOCK"]),
        ],
    },
}


def _extract_compliance_hints(text: str) -> list[ComplianceHint]:
    hints: list[ComplianceHint] = []
    for line in text.splitlines():
        m = re.match(r"\s*-\s*\*\*([A-Z_]+)\*\*:\s*(.+)", line)
        if m:
            hints.append(ComplianceHint(tag=m.group(1), description=m.group(2).strip(), source_line=line.strip()))
    return hints


def parse_maritime_spec(spec_text: str, domain: str, spec_path: str | None = None) -> dict:
    """Tool: parse markdown feature spec into structured requirements."""
    defaults = _DOMAIN_DEFAULTS.get(domain, _DOMAIN_DEFAULTS["crew-cert"])
    title_match = re.search(r"^#\s+Feature:\s*(.+)$", spec_text, re.MULTILINE)
    feature_title = title_match.group(1).strip() if title_match else defaults["feature_title"]

    requirements: list[Requirement] = []
    for row in defaults["requirements"]:
        req_id, title, desc = row[0], row[1], row[2]
        tags = list(row[3]) if len(row) > 3 else []
        edge = row[4] if len(row) > 4 else False
        requirements.append(
            Requirement(id=req_id, title=title, description=desc, compliance_tags=tags, edge_case=edge)
        )

    hints = _extract_compliance_hints(spec_text)
    if not hints:
        for req in requirements:
            for tag in req.compliance_tags:
                hints.append(ComplianceHint(tag=tag, description=req.description))

    parsed = ParsedSpec(
        feature_title=feature_title,
        domain=domain,
        actors=_extract_actors(spec_text),
        requirements=requirements,
        compliance_hints=hints,
        raw_spec_path=spec_path,
    )
    return parsed_spec_to_dict(parsed)


def _extract_actors(text: str) -> list[str]:
    actors: list[str] = []
    in_section = False
    for line in text.splitlines():
        if re.match(r"^##\s+Actors", line, re.I):
            in_section = True
            continue
        if in_section and line.startswith("##"):
            break
        if in_section and line.strip().startswith("- "):
            actors.append(line.strip().lstrip("- ").strip())
    return actors or ["Fleet operator", "System"]
