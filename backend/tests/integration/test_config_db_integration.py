"""Integration tests for config_db — exercises real DB round-trips."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.config_db import (
    get_config_value,
    get_effective_config,
    get_effective_value,
    set_config_value,
)
from app.db.models import ConfigEntry


class TestConfigEntryRoundTrip:
    """Verify ConfigEntry persists and queries correctly via SQLite."""

    def test_insert_and_query(self, db_session):
        now = datetime.now(timezone.utc)
        entry = ConfigEntry(key="resubmit_times_utc", value="14:00,20:00", updated_at=now)
        db_session.add(entry)
        db_session.commit()

        result = db_session.execute(
            select(ConfigEntry).where(ConfigEntry.key == "resubmit_times_utc")
        ).scalar_one()
        assert result.value == "14:00,20:00"
        assert result.updated_at is not None

    def test_primary_key_prevents_duplicate_keys(self, db_session):
        now = datetime.now(timezone.utc)
        db_session.add(ConfigEntry(key="organizer_scan_limit", value="10", updated_at=now))
        db_session.commit()

        db_session.add(ConfigEntry(key="organizer_scan_limit", value="20", updated_at=now))
        with pytest.raises(Exception):
            db_session.commit()


class TestSetThenGet:
    """Integration: set_config_value followed by get_config_value."""

    def test_set_then_get_returns_stored_value(self, db_session):
        set_config_value(db_session, "tournament_backfill_months", "6")
        db_session.commit()

        result = get_config_value(db_session, "tournament_backfill_months")
        assert result == "6"

    def test_set_overwrites_then_get_returns_latest(self, db_session):
        set_config_value(db_session, "organizer_scan_start_id", "1000")
        db_session.commit()

        set_config_value(db_session, "organizer_scan_start_id", "2000")
        db_session.commit()

        result = get_config_value(db_session, "organizer_scan_start_id")
        assert result == "2000"

    def test_all_editable_keys_can_be_stored(self, db_session):
        from app.config_db import EDITABLE_CONFIG_KEYS

        for key in EDITABLE_CONFIG_KEYS:
            set_config_value(db_session, key, "test_value")
        db_session.commit()

        for key in EDITABLE_CONFIG_KEYS:
            assert get_config_value(db_session, key) == "test_value"


class TestEffectiveConfigRoundTrip:
    """FR27: set_config_value → get_effective_value round-trip via real DB."""

    def test_set_then_effective_returns_db_value(self, db_session):
        set_config_value(db_session, "tournament_ingest_limit", "42")
        db_session.commit()

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == 42

    def test_effective_config_reflects_partial_overrides(self, db_session):
        from app.config import settings

        set_config_value(db_session, "organizer_scan_limit", "200")
        db_session.commit()

        result = get_effective_config(db_session)
        assert result["organizer_scan_limit"] == 200
        assert result["tournament_ingest_limit"] == settings.tournament_ingest_limit
