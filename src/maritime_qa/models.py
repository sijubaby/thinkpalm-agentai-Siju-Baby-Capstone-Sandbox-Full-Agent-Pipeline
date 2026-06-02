from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Domain(str, Enum):
    CREW_CERT = "crew-cert"
    AIS = "ais"
    PORT_WORKFLOW = "port-workflow"


@dataclass
class Requirement:
    id: str
    title: str
    description: str
    compliance_tags: list[str] = field(default_factory=list)
    edge_case: bool = False


@dataclass
class ComplianceHint:
    tag: str
    description: str
    source_line: str | None = None


@dataclass
class ParsedSpec:
    feature_title: str
    domain: str
    actors: list[str]
    requirements: list[Requirement]
    compliance_hints: list[ComplianceHint]
    raw_spec_path: str | None = None


@dataclass
class CoverageRow:
    requirement_id: str
    title: str
    covered: bool
    test_reference: str | None = None
    compliance_tags: list[str] = field(default_factory=list)


@dataclass
class ComplianceGap:
    tag: str
    severity: str
    message: str
    suggested_scenario: str


@dataclass
class CoverageReport:
    feature_title: str
    domain: str
    rows: list[CoverageRow]
    gaps: list[str]
    compliance_gaps: list[ComplianceGap]
    coverage_percent: float
    edge_cases_missing: list[str]


@dataclass
class PipelineResult:
    run_id: str
    output_dir: str
    parsed_spec: ParsedSpec
    gherkin_path: str
    playwright_path: str
    report_md_path: str
    report_html_path: str


def parsed_spec_from_dict(data: dict[str, Any]) -> ParsedSpec:
    return ParsedSpec(
        feature_title=data["feature_title"],
        domain=data["domain"],
        actors=list(data.get("actors", [])),
        requirements=[
            Requirement(
                id=r["id"],
                title=r["title"],
                description=r["description"],
                compliance_tags=list(r.get("compliance_tags", [])),
                edge_case=bool(r.get("edge_case", False)),
            )
            for r in data.get("requirements", [])
        ],
        compliance_hints=[
            ComplianceHint(
                tag=h["tag"],
                description=h["description"],
                source_line=h.get("source_line"),
            )
            for h in data.get("compliance_hints", [])
        ],
        raw_spec_path=data.get("raw_spec_path"),
    )


def parsed_spec_to_dict(spec: ParsedSpec) -> dict[str, Any]:
    return {
        "feature_title": spec.feature_title,
        "domain": spec.domain,
        "actors": spec.actors,
        "requirements": [asdict(r) for r in spec.requirements],
        "compliance_hints": [asdict(h) for h in spec.compliance_hints],
        "raw_spec_path": spec.raw_spec_path,
    }
