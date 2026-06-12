import json
from pathlib import Path

import httpx
import respx

from app.config import settings
from app.limitless_client.tournaments_api import fetch_tournaments

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_tournaments.json"


@respx.mock
def test_fetch_tournaments_returns_parsed_dtos():
    sample = json.loads(FIXTURE.read_text())
    route = respx.get(f"{settings.limitless_base_url}/api/tournaments").mock(
        return_value=httpx.Response(200, json=sample)
    )

    tournaments = fetch_tournaments(limit=1000)

    assert route.called
    request = route.calls.last.request
    assert request.url.params["limit"] == "1000"

    assert len(tournaments) == len(sample)
    assert tournaments[0].id == sample[0]["id"]
    assert tournaments[0].organizer_id == sample[0]["organizerId"]
