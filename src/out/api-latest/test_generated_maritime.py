"""Generated maritime QA tests — pytest-playwright."""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ais_monitoring.html"


@pytest.fixture
def open_fixture(page: Page):
    page.goto(FIXTURE.as_uri())


def test_stale_track_alert(open_fixture, page: Page):
    page.get_by_test_id("simulate-gap").click()
    expect(page.get_by_test_id("stale-alert")).to_be_visible()


def test_invalid_mmsi_rejected(open_fixture, page: Page):
    page.get_by_test_id("mmsi-input").fill("INVALID")
    page.get_by_test_id("submit-report").click()
    expect(page.get_by_test_id("reject-message")).to_be_visible()

