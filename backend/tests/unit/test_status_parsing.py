from pathlib import Path

import pytest

from app.db.models import ApplicationStatus
from app.scraper.parsing import parse_status_html

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


@pytest.mark.parametrize(
    ("fixture_name", "expected_status", "expected_substring"),
    [
        ("application_pending.html", ApplicationStatus.PENDING, "pending"),
        ("application_approved.html", ApplicationStatus.APPROVED, "approved"),
        ("application_rejected.html", ApplicationStatus.REJECTED, "rejected"),
        ("application_expired.html", ApplicationStatus.EXPIRED, "expired"),
    ],
)
def test_parse_status_html_detects_known_statuses(fixture_name, expected_status, expected_substring):
    html = (FIXTURE_DIR / fixture_name).read_text()

    result = parse_status_html(html)

    assert result.status == expected_status
    assert expected_substring in result.raw_text


def test_parse_status_html_returns_unknown_when_no_application_exists():
    html = (FIXTURE_DIR / "application_unrecognized.html").read_text()

    result = parse_status_html(html)

    assert result.status == ApplicationStatus.UNKNOWN
    assert result.raw_text == ""


def test_parse_status_html_captures_review_note_when_present():
    html = (FIXTURE_DIR / "application_rejected.html").read_text()

    result = parse_status_html(html)

    assert result.review_note is not None
    assert "rejected" in result.review_note.lower()


def test_parse_status_html_review_note_is_none_when_response_empty():
    html = (FIXTURE_DIR / "application_pending.html").read_text()

    result = parse_status_html(html)

    assert result.review_note is None
