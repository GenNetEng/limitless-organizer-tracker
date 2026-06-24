"""Unit tests for config_db module — allowlist, get/set config values."""
from datetime import datetime, timezone

import pytest

from app.config_db import (
    EDITABLE_CONFIG_KEYS,
    get_config_value,
    set_config_value,
)
from app.db.models import ConfigEntry


class TestEditableConfigKeys:
    """FR26: only the 8 non-sensitive AdminConfigOut fields are editable."""

    def test_contains_expected_keys(self):
        expected = {
            "application_status_check_interval_hours",
            "resubmit_times_utc",
            "tournament_ingest_interval_hours",
            "tournament_ingest_limit",
            "tournament_backfill_months",
            "organizer_scan_interval_hours",
            "organizer_scan_limit",
            "organizer_scan_start_id",
        }
        assert EDITABLE_CONFIG_KEYS == expected

    def test_excludes_sensitive_keys(self):
        sensitive = {
            "database_url",
            "redis_url",
            "limitless_username",
            "limitless_password",
            "discord_webhook_url",
        }
        assert sensitive.isdisjoint(EDITABLE_CONFIG_KEYS)

    def test_is_frozenset(self):
        assert isinstance(EDITABLE_CONFIG_KEYS, frozenset)


class TestConfigEntryModel:
    """ConfigEntry model structure."""

    def test_tablename(self):
        assert ConfigEntry.__tablename__ == "config_entries"

    def test_key_is_primary_key(self):
        key_col = ConfigEntry.__table__.c.key
        assert key_col.primary_key

    def test_has_value_column(self):
        assert "value" in ConfigEntry.__table__.c

    def test_has_updated_at_column(self):
        assert "updated_at" in ConfigEntry.__table__.c


class TestGetConfigValue:
    """get_config_value returns value for a key, or None if absent."""

    def test_returns_value_when_present(self, db_session):
        entry = ConfigEntry(
            key="tournament_ingest_limit",
            value="50",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        result = get_config_value(db_session, "tournament_ingest_limit")
        assert result == "50"

    def test_returns_none_when_absent(self, db_session):
        result = get_config_value(db_session, "tournament_ingest_limit")
        assert result is None

    def test_rejects_non_editable_key(self, db_session):
        with pytest.raises(ValueError, match="not an editable config key"):
            get_config_value(db_session, "database_url")


class TestSetConfigValue:
    """set_config_value upserts a config entry."""

    def test_inserts_new_entry(self, db_session):
        set_config_value(db_session, "tournament_ingest_limit", "100")
        db_session.commit()

        entry = db_session.get(ConfigEntry, "tournament_ingest_limit")
        assert entry is not None
        assert entry.value == "100"
        assert entry.updated_at is not None

    def test_updates_existing_entry(self, db_session):
        entry = ConfigEntry(
            key="organizer_scan_limit",
            value="10",
            updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        set_config_value(db_session, "organizer_scan_limit", "25")
        db_session.commit()

        updated = db_session.get(ConfigEntry, "organizer_scan_limit")
        assert updated.value == "25"
        assert updated.updated_at > datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_rejects_non_editable_key(self, db_session):
        with pytest.raises(ValueError, match="not an editable config key"):
            set_config_value(db_session, "database_url", "postgres://evil")
