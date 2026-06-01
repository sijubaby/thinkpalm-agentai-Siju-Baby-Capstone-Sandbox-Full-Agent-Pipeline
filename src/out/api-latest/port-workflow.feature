Feature: Port Arrival and Departure Workflow
  Maritime domain: port-workflow

  Scenario: Record port arrival at berth
    Given a vessel approaching berth
    When the master confirms arrival
    Then actual arrival time and berth id are recorded

  Scenario: Record port departure
    Given a vessel in port with completed operations
    When departure is confirmed
    Then departure time is recorded and in-port status cleared

  Scenario: Block departure without clearance
    Given mandatory port clearance is missing
    When departure is requested
    Then departure is blocked
