from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
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
        "display_timezone",
        "scraper_debug",
    }
)

_BOOL_TRUTHY = frozenset({"true", "1", "yes"})


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
    now = datetime.now(timezone.utc)
    entry = session.get(ConfigEntry, key)
    if entry is None:
        entry = ConfigEntry(key=key, value=value, updated_at=now)
        session.add(entry)
    else:
        entry.value = value
        entry.updated_at = now


def get_effective_value(session: Session, key: str) -> str | int | bool:
    _validate_key(key)
    db_entry = session.get(ConfigEntry, key)
    default = getattr(settings, key)
    if db_entry is None:
        return default
    if isinstance(default, bool):
        if db_entry.value.lower() in _BOOL_TRUTHY:
            return True
        if db_entry.value.lower() in ("false", "0", "no"):
            return False
        return default
    if isinstance(default, int):
        try:
            return int(db_entry.value)
        except (ValueError, TypeError):
            return default
    return db_entry.value


def get_effective_config(session: Session) -> dict:
    rows = session.execute(select(ConfigEntry)).scalars().all()
    overrides = {row.key: row.value for row in rows if row.key in EDITABLE_CONFIG_KEYS}
    result = {}
    for key in EDITABLE_CONFIG_KEYS:
        default = getattr(settings, key)
        if key in overrides:
            if isinstance(default, bool):
                val = overrides[key].lower()
                if val in _BOOL_TRUTHY:
                    result[key] = True
                elif val in ("false", "0", "no"):
                    result[key] = False
                else:
                    result[key] = default
            elif isinstance(default, int):
                try:
                    result[key] = int(overrides[key])
                except (ValueError, TypeError):
                    result[key] = default
            else:
                result[key] = overrides[key]
        else:
            result[key] = default
    return result
