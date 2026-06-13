from pathlib import Path
from unittest.mock import MagicMock

from app.config import settings
from app.db.models import ApplicationStatus
from app.scraper.application_status import check_application_status

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "html"


def test_check_application_status_navigates_to_application_page_and_parses_result(monkeypatch):
    monkeypatch.setattr(settings, "limitless_application_id", "69256ff752eafbbc81177f6a")

    page = MagicMock()
    page.content.return_value = (FIXTURE_DIR / "application_pending.html").read_text()

    result = check_application_status(page)

    page.goto.assert_called_once_with(
        f"{settings.limitless_base_url}/user/application/69256ff752eafbbc81177f6a"
    )
    page.wait_for_load_state.assert_called_once_with("networkidle")
    assert result.status == ApplicationStatus.PENDING
