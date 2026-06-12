from pathlib import Path

import pytest

from app.db.models import ApplicationStatus
from app.scraper.parsing import parse_status_html

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


@pytest.mark.parametrize(
    ("fixture_name", "expected_status", "expected_substring"),
    [
        ("org_settings_pending.html", ApplicationStatus.PENDING, "Pending"),
        ("org_settings_approved.html", ApplicationStatus.APPROVED, "Approved"),
        ("org_settings_rejected.html", ApplicationStatus.REJECTED, "Rejected"),
        ("org_settings_expired.html", ApplicationStatus.EXPIRED, "Expired"),
    ],
)
def test_parse_status_html_detects_known_statuses(fixture_name, expected_status, expected_substring):
    html = (FIXTURE_DIR / fixture_name).read_text()

    result = parse_status_html(html)

    assert result.status == expected_status
    assert expected_substring in result.raw_text


def test_parse_status_html_returns_unknown_when_no_application_exists():
    html = (FIXTURE_DIR / "org_settings_no_application.html").read_text()

    result = parse_status_html(html)

    assert result.status == ApplicationStatus.UNKNOWN
    assert result.raw_text == ""
