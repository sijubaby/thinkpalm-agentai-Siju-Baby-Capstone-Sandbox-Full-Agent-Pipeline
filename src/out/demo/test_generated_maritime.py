"""Generated maritime QA tests — pytest-playwright."""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "crew_cert_dashboard.html"


@pytest.fixture
def open_fixture(page: Page):
    page.goto(FIXTURE.as_uri())


def test_90_day_alert_visible(open_fixture, page: Page):
    expect(page.get_by_test_id("alert-90")).to_be_visible()


def test_block_embarkation_when_expired(open_fixture, page: Page):
    page.get_by_test_id("crew-select").select_option("expired")
    page.get_by_test_id("sign-on-btn").click()
    expect(page.get_by_test_id("embarkation-blocked")).to_be_visible()


def test_pending_renewal_still_blocked(open_fixture, page: Page):
    page.get_by_test_id("crew-select").select_option("pending")
    page.get_by_test_id("sign-on-btn").click()
    expect(page.get_by_test_id("embarkation-blocked")).to_be_visible()

