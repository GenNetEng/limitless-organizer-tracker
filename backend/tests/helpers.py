from contextlib import contextmanager

from app.db.session import task_session
from app.events import log_event
from app.scraper.session import AuthenticatedPageContext


@contextmanager
def fake_authenticated_page(page, session_refreshed=False):
    if session_refreshed:
        with task_session() as db_session:
            log_event(
                session=db_session,
                event_type="scraper.session_refreshed",
                source="session",
                message="Expired session detected and refreshed",
                severity="WARNING",
            )
            db_session.commit()
    yield AuthenticatedPageContext(page=page, session_refreshed=session_refreshed)
