# Feature: AIS Position Reporting Intervals

## Domain
Maritime fleet management — AIS telemetry module

## Actors
- Shore fleet operator
- Onboard AIS transponder interface
- Compliance monitoring service

## Business rules
1. Underway vessels shall report position at intervals not exceeding **10 minutes**.
2. At anchor, reporting interval may extend to **3 minutes** when configured for high-traffic areas.
3. If no position report is received for **2× the configured interval**, the system shall raise a **stale track** alert.
4. Invalid or missing **MMSI** shall reject the report and log a data integrity event.
5. Position reports shall include UTC timestamp and navigational status.

## Edge cases
- GPS drift causing duplicate positions within same minute
- Transponder reset during passage — gap in reporting
- Shore-side clock skew vs onboard UTC

## Compliance notes
- **DATA_INTEGRITY_AIS**: Invalid MMSI must be rejected with audit log.
- **COMPLIANCE_REPORTING_INTERVAL**: Underway 10-minute maximum interval must be enforced.
- **SAFETY_CRITICAL_SILENT_FAILURE**: Stale track alert must fire when reporting gap exceeds threshold.
