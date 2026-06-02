from __future__ import annotations

from pathlib import Path

from maritime_qa.models import parsed_spec_from_dict


def write_gherkin(parsed_spec: dict, output_path: str) -> dict:
    """Tool: write Gherkin .feature file from parsed spec."""
    spec = parsed_spec_from_dict(parsed_spec)
    lines = [
        f"Feature: {spec.feature_title}",
        f"  Maritime domain: {spec.domain}",
        "",
    ]

    scenario_templates = _scenarios_for_domain(spec.domain)
    covered_ids = set()

    for req in spec.requirements:
        if req.edge_case:
            continue
        template = scenario_templates.get(req.id)
        if template:
            lines.extend(template)
            lines.append("")
            covered_ids.add(req.id)

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines).strip() + "\n"
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "content": content}


def _scenarios_for_domain(domain: str) -> dict[str, list[str]]:
    if domain == "crew-cert":
        return {
            "REQ-01": [
                "  Scenario: 90-day certificate expiry alert",
                "    Given a crew member with a mandatory certificate expiring in 90 days",
                "    When the daily compliance job runs",
                "    Then a 90-day alert is recorded on the certification dashboard",
            ],
            "REQ-02": [
                "  Scenario: 30-day certificate expiry alert",
                "    Given a crew member with a mandatory certificate expiring in 30 days",
                "    When the daily compliance job runs",
                "    Then a 30-day alert is recorded on the certification dashboard",
            ],
            "REQ-03": [
                "  Scenario: 7-day certificate expiry alert",
                "    Given a crew member with a mandatory certificate expiring in 7 days",
                "    When the daily compliance job runs",
                "    Then a 7-day alert is recorded on the certification dashboard",
            ],
            "REQ-04": [
                "  Scenario: Block embarkation when certificate expired",
                "    Given a crew member whose mandatory certificate is expired",
                "    When the administrator attempts sign-on",
                "    Then embarkation is blocked",
                "    And the block reason references expired certification",
            ],
            "REQ-05": [
                "  Scenario: Alerts visible on dashboard",
                "    Given active certification alerts exist",
                "    When the vessel administrator opens the crew certification dashboard",
                "    Then pending alerts are listed for the crew member",
            ],
            "REQ-06": [
                "  Scenario: Pending renewal does not unblock embarkation",
                "    Given a crew member with renewal status PENDING",
                "    When embarkation is requested",
                "    Then embarkation remains blocked",
            ],
        }
    if domain == "ais":
        return {
            "REQ-01": [
                "  Scenario: Underway position report within interval",
                "    Given a vessel is underway with 10-minute reporting configured",
                "    When a position report is received within 10 minutes",
                "    Then the track is updated without stale alert",
            ],
            "REQ-03": [
                "  Scenario: Stale track when reporting gap exceeded",
                "    Given a vessel with 10-minute reporting interval",
                "    When no position report is received for 20 minutes",
                "    Then a stale track alert is raised",
            ],
            "REQ-04": [
                "  Scenario: Reject invalid MMSI",
                "    Given an AIS report with an invalid MMSI",
                "    When the report is ingested",
                "    Then the report is rejected",
                "    And a data integrity event is logged",
            ],
        }
    if domain == "port-workflow":
        return {
            "REQ-01": [
                "  Scenario: Record port arrival at berth",
                "    Given a vessel approaching berth",
                "    When the master confirms arrival",
                "    Then actual arrival time and berth id are recorded",
            ],
            "REQ-02": [
                "  Scenario: Record port departure",
                "    Given a vessel in port with completed operations",
                "    When departure is confirmed",
                "    Then departure time is recorded and in-port status cleared",
            ],
            "REQ-03": [
                "  Scenario: Block departure without clearance",
                "    Given mandatory port clearance is missing",
                "    When departure is requested",
                "    Then departure is blocked",
            ],
        }
    return {}
