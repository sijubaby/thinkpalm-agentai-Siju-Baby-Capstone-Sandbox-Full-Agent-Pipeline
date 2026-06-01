from __future__ import annotations

from pathlib import Path

from maritime_qa.models import parsed_spec_from_dict

_CREW_FIXTURE = "tests/e2e/fixtures/crew_cert_dashboard.html"
_AIS_FIXTURE = "tests/e2e/fixtures/ais_monitoring.html"


def write_playwright(parsed_spec: dict, domain: str, output_path: str) -> dict:
    """Tool: generate pytest-playwright tests from parsed spec."""
    spec = parsed_spec_from_dict(parsed_spec)
    fixture = _CREW_FIXTURE if domain == "crew-cert" else _AIS_FIXTURE

    tests: list[str] = [
        '"""Generated maritime QA tests — pytest-playwright."""',
        "from pathlib import Path",
        "",
        "import pytest",
        "from playwright.sync_api import Page, expect",
        "",
        "",
        f"FIXTURE = Path(__file__).resolve().parent / \"fixtures\" / \"{'crew_cert_dashboard.html' if domain == 'crew-cert' else 'ais_monitoring.html'}\"",
        "",
        "",
        "@pytest.fixture",
        "def open_fixture(page: Page):",
        "    page.goto(FIXTURE.as_uri())",
        "",
    ]

    if domain == "crew-cert":
        tests.extend(_crew_tests())
    elif domain == "ais":
        tests.extend(_ais_tests())
    else:
        tests.extend(_generic_tests(spec.feature_title))

    content = "\n".join(tests) + "\n"
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "content": content, "fixture": fixture}


def _crew_tests() -> list[str]:
    return [
        "",
        "def test_90_day_alert_visible(open_fixture, page: Page):",
        "    expect(page.get_by_test_id(\"alert-90\")).to_be_visible()",
        "",
        "",
        "def test_block_embarkation_when_expired(open_fixture, page: Page):",
        "    page.get_by_test_id(\"crew-select\").select_option(\"expired\")",
        "    page.get_by_test_id(\"sign-on-btn\").click()",
        "    expect(page.get_by_test_id(\"embarkation-blocked\")).to_be_visible()",
        "",
        "",
        "def test_pending_renewal_still_blocked(open_fixture, page: Page):",
        "    page.get_by_test_id(\"crew-select\").select_option(\"pending\")",
        "    page.get_by_test_id(\"sign-on-btn\").click()",
        "    expect(page.get_by_test_id(\"embarkation-blocked\")).to_be_visible()",
        "",
    ]


def _ais_tests() -> list[str]:
    return [
        "",
        "def test_stale_track_alert(open_fixture, page: Page):",
        "    page.get_by_test_id(\"simulate-gap\").click()",
        "    expect(page.get_by_test_id(\"stale-alert\")).to_be_visible()",
        "",
        "",
        "def test_invalid_mmsi_rejected(open_fixture, page: Page):",
        "    page.get_by_test_id(\"mmsi-input\").fill(\"INVALID\")",
        "    page.get_by_test_id(\"submit-report\").click()",
        "    expect(page.get_by_test_id(\"reject-message\")).to_be_visible()",
        "",
    ]


def _generic_tests(title: str) -> list[str]:
    return [
        "",
        f"def test_feature_loaded(open_fixture, page: Page):",
        f"    expect(page.locator(\"h1\")).to_contain_text({title!r})",
        "",
    ]
