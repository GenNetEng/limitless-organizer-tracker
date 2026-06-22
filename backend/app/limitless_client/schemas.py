from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TournamentDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    game: str = "unknown"
    format: str | None = None
    date: datetime
    players: int
    organizer_id: int = Field(alias="organizerId")
