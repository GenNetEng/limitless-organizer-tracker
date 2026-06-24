import json
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.db.models import ApplicationStatus, EventLog
from app.scraper.parsing import ApplicationStatusResult
from app.scraper.resubmit import ResubmitResult
from app.scraper.session import AuthenticatedPageContext
from app.tasks.resubmit_tasks import resubmit_application_task
from app.tasks.status_tasks import record_status_check, run_application_status_check


@contextmanager
def _fake_authenticated_page(page_content="<html></html>", session_refreshed=False, content_raises=False):
    page = MagicMock()
    if content_raises:
        page.content.side_effect = RuntimeError("browser crashed")
    else:
        page.content.return_value = page_content
    yield AuthenticatedPageContext(page=page, session_refreshed=session_refreshed)


@contextmanager
def _fake_task_session(session):
    yield session


class TestResubmitTaskScraperDebug:
    def test_includes_debug_html_on_success(self, db_session):
        with (
            patch("app.tasks.resubmit_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.resubmit_tasks.resubmit_application") as mock_resubmit,
            patch("app.tasks.resubmit_tasks.post_resubmission_notice") as mock_discord,
            patch("app.tasks.resubmit_tasks.task_session") as mock_ts,
            patch("app.tasks.resubmit_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page("<html>debug</html>")
            mock_resubmit.return_value = ResubmitResult(success=True, server_response={"ok": True})
            mock_discord.return_value = MagicMock(status_code=200)
            mock_ts.return_value = _fake_task_session(db_session)
            mock_settings.scraper_debug = True
            mock_settings.discord_webhook_url = "https://example.com"

            resubmit_application_task()

        event = db_session.query(EventLog).filter_by(event_type="scraper.resubmit").one()
        details = json.loads(event.details)
        assert details["debug_page_html"] == "<html>debug</html>"

    def test_excludes_debug_html_when_disabled(self, db_session):
        with (
            patch("app.tasks.resubmit_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.resubmit_tasks.resubmit_application") as mock_resubmit,
            patch("app.tasks.resubmit_tasks.post_resubmission_notice") as mock_discord,
            patch("app.tasks.resubmit_tasks.task_session") as mock_ts,
            patch("app.tasks.resubmit_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page("<html>debug</html>")
            mock_resubmit.return_value = ResubmitResult(success=True, server_response={"ok": True})
            mock_discord.return_value = MagicMock(status_code=200)
            mock_ts.return_value = _fake_task_session(db_session)
            mock_settings.scraper_debug = False
            mock_settings.discord_webhook_url = "https://example.com"

            resubmit_application_task()

        event = db_session.query(EventLog).filter_by(event_type="scraper.resubmit").one()
        details = json.loads(event.details)
        assert "debug_page_html" not in details

    def test_debug_html_truncated_to_20000_chars(self, db_session):
        long_html = "x" * 25000
        with (
            patch("app.tasks.resubmit_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.resubmit_tasks.resubmit_application") as mock_resubmit,
            patch("app.tasks.resubmit_tasks.post_resubmission_notice") as mock_discord,
            patch("app.tasks.resubmit_tasks.task_session") as mock_ts,
            patch("app.tasks.resubmit_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page(long_html)
            mock_resubmit.return_value = ResubmitResult(success=True, server_response={"ok": True})
            mock_discord.return_value = MagicMock(status_code=200)
            mock_ts.return_value = _fake_task_session(db_session)
            mock_settings.scraper_debug = True
            mock_settings.discord_webhook_url = "https://example.com"

            resubmit_application_task()

        event = db_session.query(EventLog).filter_by(event_type="scraper.resubmit").one()
        details = json.loads(event.details)
        assert len(details["debug_page_html"]) == 20000

    def test_includes_debug_html_alongside_failure_html(self, db_session):
        with (
            patch("app.tasks.resubmit_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.resubmit_tasks.resubmit_application") as mock_resubmit,
            patch("app.tasks.resubmit_tasks.post_resubmission_notice") as mock_discord,
            patch("app.tasks.resubmit_tasks.task_session") as mock_ts,
            patch("app.tasks.resubmit_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page("<html>current state</html>")
            mock_resubmit.return_value = ResubmitResult(
                success=False,
                failure_stage="page_load_failed",
                page_html="<html>failure snapshot</html>",
            )
            mock_discord.return_value = MagicMock(status_code=200)
            mock_ts.return_value = _fake_task_session(db_session)
            mock_settings.scraper_debug = True
            mock_settings.discord_webhook_url = "https://example.com"

            resubmit_application_task()

        event = db_session.query(EventLog).filter_by(event_type="scraper.resubmit").one()
        details = json.loads(event.details)
        assert details["page_html"] == "<html>failure snapshot</html>"
        assert details["debug_page_html"] == "<html>current state</html>"

    def test_task_succeeds_when_page_content_throws(self, db_session):
        with (
            patch("app.tasks.resubmit_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.resubmit_tasks.resubmit_application") as mock_resubmit,
            patch("app.tasks.resubmit_tasks.post_resubmission_notice") as mock_discord,
            patch("app.tasks.resubmit_tasks.task_session") as mock_ts,
            patch("app.tasks.resubmit_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page(content_raises=True)
            mock_resubmit.return_value = ResubmitResult(success=True, server_response={"ok": True})
            mock_discord.return_value = MagicMock(status_code=200)
            mock_ts.return_value = _fake_task_session(db_session)
            mock_settings.scraper_debug = True
            mock_settings.discord_webhook_url = "https://example.com"

            event_id = resubmit_application_task()

        assert event_id is not None
        event = db_session.query(EventLog).filter_by(event_type="scraper.resubmit").one()
        details = json.loads(event.details)
        assert "debug_page_html" not in details


class TestRecordStatusCheckScraperDebug:
    def test_includes_debug_html_when_provided(self, db_session):
        result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending")
        timestamp = datetime(2026, 6, 23, 9, 0, tzinfo=timezone.utc)

        record_status_check(db_session, result, timestamp, debug_page_html="<html>debug</html>")

        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert details["debug_page_html"] == "<html>debug</html>"

    def test_excludes_debug_html_when_not_provided(self, db_session):
        result = ApplicationStatusResult(status=ApplicationStatus.PENDING, raw_text="Pending")
        timestamp = datetime(2026, 6, 23, 9, 0, tzinfo=timezone.utc)

        record_status_check(db_session, result, timestamp)

        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert "debug_page_html" not in details


class TestRunStatusCheckScraperDebug:
    def test_captures_debug_html_when_enabled(self, db_session):
        with (
            patch("app.tasks.status_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.status_tasks.check_application_status") as mock_check,
            patch("app.tasks.status_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page("<html>status debug</html>")
            mock_check.return_value = ApplicationStatusResult(
                status=ApplicationStatus.PENDING, raw_text="Pending"
            )
            mock_settings.scraper_debug = True

            run_application_status_check(db_session)

        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert details["debug_page_html"] == "<html>status debug</html>"

    def test_excludes_debug_html_when_disabled(self, db_session):
        with (
            patch("app.tasks.status_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.status_tasks.check_application_status") as mock_check,
            patch("app.tasks.status_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page("<html>status debug</html>")
            mock_check.return_value = ApplicationStatusResult(
                status=ApplicationStatus.PENDING, raw_text="Pending"
            )
            mock_settings.scraper_debug = False

            run_application_status_check(db_session)

        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert "debug_page_html" not in details

    def test_debug_html_truncated_to_20000_chars(self, db_session):
        long_html = "y" * 25000
        with (
            patch("app.tasks.status_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.status_tasks.check_application_status") as mock_check,
            patch("app.tasks.status_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page(long_html)
            mock_check.return_value = ApplicationStatusResult(
                status=ApplicationStatus.PENDING, raw_text="Pending"
            )
            mock_settings.scraper_debug = True

            run_application_status_check(db_session)

        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert len(details["debug_page_html"]) == 20000

    def test_status_check_succeeds_when_page_content_throws(self, db_session):
        with (
            patch("app.tasks.status_tasks.authenticated_page") as mock_auth,
            patch("app.tasks.status_tasks.check_application_status") as mock_check,
            patch("app.tasks.status_tasks.settings") as mock_settings,
        ):
            mock_auth.return_value = _fake_authenticated_page(content_raises=True)
            mock_check.return_value = ApplicationStatusResult(
                status=ApplicationStatus.PENDING, raw_text="Pending"
            )
            mock_settings.scraper_debug = True

            check, changed = run_application_status_check(db_session)

        assert check is not None
        event = db_session.query(EventLog).filter_by(event_type="scraper.status_check").one()
        details = json.loads(event.details)
        assert "debug_page_html" not in details
