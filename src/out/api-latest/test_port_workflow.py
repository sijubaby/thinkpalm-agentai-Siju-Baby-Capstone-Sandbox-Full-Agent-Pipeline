"""Generated maritime QA tests — pytest-playwright."""
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "ais_monitoring.html"


@pytest.fixture
def open_fixture(page: Page):
    page.goto(FIXTURE.as_uri())


def test_feature_loaded(open_fixture, page: Page):
    expect(page.locator("h1")).to_contain_text('Port Arrival and Departure Workflow')

