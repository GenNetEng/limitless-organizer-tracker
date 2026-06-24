from contextlib import contextmanager

from app.scraper.session import AuthenticatedPageContext


@contextmanager
def fake_authenticated_page(page, session_refreshed=False):
    yield AuthenticatedPageContext(page=page, session_refreshed=session_refreshed)
