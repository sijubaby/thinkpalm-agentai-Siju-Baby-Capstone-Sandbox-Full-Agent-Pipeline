# Coverage Gap Report — AIS Position Reporting Intervals

- **Domain:** ais
- **Coverage:** 50.0%

## Requirement matrix

| ID | Requirement | Covered | Compliance tags |
|----|-------------|---------|-----------------|
| REQ-01 | Underway reporting interval | **No** | COMPLIANCE_REPORTING_INTERVAL |
| REQ-02 | At-anchor interval | **No** | — |
| REQ-03 | Stale track alert | Yes | SAFETY_CRITICAL_SILENT_FAILURE |
| REQ-04 | Reject invalid MMSI | Yes | DATA_INTEGRITY_AIS |
| REQ-05 | UTC timestamp required | **No** | — |
| REQ-06 | Transponder reset gap | Yes | — |

## Gaps

- REQ-01: Underway reporting interval — no automated requirement coverage
- REQ-02: At-anchor interval — no automated requirement coverage
- REQ-05: UTC timestamp required — no automated requirement coverage

## Compliance flags

- **[HIGH] COMPLIANCE_EMBARKATION_BLOCK**: Expired mandatory certificate must block embarkation in automated tests
  - Suggested: `Scenario: block embarkation when mandatory certificate expired`
