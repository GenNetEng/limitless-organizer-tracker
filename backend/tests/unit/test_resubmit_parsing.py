from pathlib import Path

import pytest

from app.scraper.parsing import parse_resubmit_result

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


@pytest.mark.parametrize(
    ("fixture_name", "expected_success"),
    [
        ("application_resubmit_success.html", True),
        ("application_resubmit_failure.html", False),
    ],
)
def test_parse_resubmit_result_detects_outcome(fixture_name, expected_success):
    html = (FIXTURE_DIR / fixture_name).read_text()

    assert parse_resubmit_result(html) is expected_success


def test_parse_resubmit_result_defaults_to_failure_when_no_result_element():
    html = (FIXTURE_DIR / "application_pending.html").read_text()

    assert parse_resubmit_result(html) is False


def test_parse_resubmit_result_treats_hidden_page3_as_failure():
    html = """
    <div class="page3 alert success" style="display: none">
      Thanks for submitting an organizer application!
    </div>
    """

    assert parse_resubmit_result(html) is False
