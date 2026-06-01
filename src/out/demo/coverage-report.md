# Coverage Gap Report — Crew Certification Expiry Monitoring and Alerts

- **Domain:** crew-cert
- **Coverage:** 44.4%

## Requirement matrix

| ID | Requirement | Covered | Compliance tags |
|----|-------------|---------|-----------------|
| REQ-01 | 90-day expiry alert | Yes | COMPLIANCE_ALERT_SCHEDULE |
| REQ-02 | 30-day expiry alert | **No** | COMPLIANCE_ALERT_SCHEDULE |
| REQ-03 | 7-day expiry alert | **No** | COMPLIANCE_ALERT_SCHEDULE |
| REQ-04 | Block embarkation when expired | Yes | COMPLIANCE_EMBARKATION_BLOCK, SAFETY_CRITICAL_SILENT_FAILURE |
| REQ-05 | Dashboard visibility | Yes | — |
| REQ-06 | Pending renewal status | Yes | — |
| REQ-07 | Earliest expiry scheduling | **No** | — |
| REQ-08 | Timezone midnight expiry | **No** | — |
| REQ-09 | Delayed alert job | **No** | SAFETY_CRITICAL_SILENT_FAILURE |

## Gaps

- REQ-02: 30-day expiry alert — no automated requirement coverage
- REQ-03: 7-day expiry alert — no automated requirement coverage
- REQ-07: Earliest expiry scheduling — no automated edge case coverage
- REQ-08: Timezone midnight expiry — no automated edge case coverage
- REQ-09: Delayed alert job — no automated edge case coverage

## Compliance flags

- **[HIGH] COMPLIANCE_ALERT_SCHEDULE**: 90/30/7-day alerts must be asserted in both Gherkin and Playwright
  - Suggested: `Add test_30_day_alert and test_7_day_alert Playwright tests with matching Gherkin`
- **[HIGH] SAFETY_CRITICAL_SILENT_FAILURE**: Safety-critical failure paths (stale track / delayed alerts) need automation
  - Suggested: `Scenario: stale track or delayed alert job still enforces block/alert`

## Untested edge cases (safety-critical)

- REQ-07: Earliest expiry scheduling
- REQ-08: Timezone midnight expiry
- REQ-09: Delayed alert job
