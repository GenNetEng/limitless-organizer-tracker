from pathlib import Path

import pytest

from app.scraper.parsing import parse_resubmit_result

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


@pytest.mark.parametrize(
    ("fixture_name", "expected_success"),
    [
        ("org_settings_resubmit_success.html", True),
        ("org_settings_resubmit_failure.html", False),
    ],
)
def test_parse_resubmit_result_detects_outcome(fixture_name, expected_success):
    html = (FIXTURE_DIR / fixture_name).read_text()

    assert parse_resubmit_result(html) is expected_success


def test_parse_resubmit_result_defaults_to_failure_when_no_result_element():
    html = (FIXTURE_DIR / "org_settings_pending.html").read_text()

    assert parse_resubmit_result(html) is False


def test_parse_resubmit_result_treats_unsuccessful_as_failure():
    html = """
    <div class="resubmit-result">Your resubmission was unsuccessful.</div>
    """

    assert parse_resubmit_result(html) is False
