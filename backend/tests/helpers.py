from contextlib import contextmanager


@contextmanager
def fake_authenticated_page(page):
    yield page
