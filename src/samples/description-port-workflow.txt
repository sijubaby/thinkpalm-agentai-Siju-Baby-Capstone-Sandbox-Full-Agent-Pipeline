# Feature: Port Arrival and Departure Workflow

## Domain
Maritime fleet management — port operations module

## Actors
- Vessel master
- Port agent
- Fleet operations centre

## Business rules
1. On **arrival** at berth, the system shall record actual arrival time and berth identifier.
2. On **departure**, the system shall record departure time and clear in-port status.
3. **Departure shall be blocked** if mandatory port clearance documentation is missing or expired.
4. All arrival/departure events shall be available for regulatory audit export.

## Edge cases
- Arrival recorded before berth assignment confirmed
- Duplicate departure submission from master and agent
- Clearance expires while vessel still in port

## Compliance notes
- **COMPLIANCE_EMBARKATION_BLOCK**: Departure blocked without valid port clearance.
- **SAFETY_CRITICAL_SILENT_FAILURE**: System must not allow departure without recording clearance check.
