from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import ConfigEntry

EDITABLE_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "application_status_check_interval_hours",
        "resubmit_times_utc",
        "tournament_ingest_interval_hours",
        "tournament_ingest_limit",
        "tournament_backfill_months",
        "organizer_scan_interval_hours",
        "organizer_scan_limit",
        "organizer_scan_start_id",
    }
)


def _validate_key(key: str) -> None:
    if key not in EDITABLE_CONFIG_KEYS:
        raise ValueError(f"'{key}' is not an editable config key")


def get_config_value(session: Session, key: str) -> str | None:
    _validate_key(key)
    entry = session.get(ConfigEntry, key)
    if entry is None:
        return None
    return entry.value


def set_config_value(session: Session, key: str, value: str) -> None:
    _validate_key(key)
    entry = session.get(ConfigEntry, key)
    if entry is None:
        entry = ConfigEntry(key=key, value=value, updated_at=datetime.now(timezone.utc))
        session.add(entry)
    else:
        entry.value = value
        entry.updated_at = datetime.now(timezone.utc)
