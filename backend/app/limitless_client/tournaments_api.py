import httpx

from app.config import settings
from app.limitless_client.schemas import TournamentDTO


def fetch_tournaments(
    limit: int = 1000, page: int | None = None, client: httpx.Client | None = None
) -> list[TournamentDTO]:
    """Fetch a page of tournaments from the Limitless tournaments API, newest first.

    `page` defaults to the API's first page when omitted.
    """
    owns_client = client is None
    client = client or httpx.Client(base_url=settings.limitless_base_url, timeout=30.0)
    try:
        params = {"limit": limit}
        if page is not None:
            params["page"] = page
        response = client.get("/api/tournaments", params=params)
        response.raise_for_status()
        return [TournamentDTO.model_validate(item) for item in response.json()]
    finally:
        if owns_client:
            client.close()
