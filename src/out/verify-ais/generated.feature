Feature: AIS Position Reporting Intervals
  Maritime domain: ais

  Scenario: Underway position report within interval
    Given a vessel is underway with 10-minute reporting configured
    When a position report is received within 10 minutes
    Then the track is updated without stale alert

  Scenario: Stale track when reporting gap exceeded
    Given a vessel with 10-minute reporting interval
    When no position report is received for 20 minutes
    Then a stale track alert is raised

  Scenario: Reject invalid MMSI
    Given an AIS report with an invalid MMSI
    When the report is ingested
    Then the report is rejected
    And a data integrity event is logged
