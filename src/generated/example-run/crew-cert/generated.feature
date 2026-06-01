Feature: Crew Certification Expiry Monitoring and Alerts
  Maritime domain: crew-cert

  Scenario: 90-day certificate expiry alert
    Given a crew member with a mandatory certificate expiring in 90 days
    When the daily compliance job runs
    Then a 90-day alert is recorded on the certification dashboard

  Scenario: 30-day certificate expiry alert
    Given a crew member with a mandatory certificate expiring in 30 days
    When the daily compliance job runs
    Then a 30-day alert is recorded on the certification dashboard

  Scenario: 7-day certificate expiry alert
    Given a crew member with a mandatory certificate expiring in 7 days
    When the daily compliance job runs
    Then a 7-day alert is recorded on the certification dashboard

  Scenario: Block embarkation when certificate expired
    Given a crew member whose mandatory certificate is expired
    When the administrator attempts sign-on
    Then embarkation is blocked
    And the block reason references expired certification

  Scenario: Alerts visible on dashboard
    Given active certification alerts exist
    When the vessel administrator opens the crew certification dashboard
    Then pending alerts are listed for the crew member

  Scenario: Pending renewal does not unblock embarkation
    Given a crew member with renewal status PENDING
    When embarkation is requested
    Then embarkation remains blocked
