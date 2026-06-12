import httpx

from app.config import settings
from app.limitless_client.schemas import TournamentDTO


def fetch_tournaments(limit: int = 1000, client: httpx.Client | None = None) -> list[TournamentDTO]:
    """Fetch the most recent tournaments from the Limitless tournaments API."""
    owns_client = client is None
    client = client or httpx.Client(base_url=settings.limitless_base_url, timeout=30.0)
    try:
        response = client.get("/api/tournaments", params={"limit": limit})
        response.raise_for_status()
        return [TournamentDTO.model_validate(item) for item in response.json()]
    finally:
        if owns_client:
            client.close()
