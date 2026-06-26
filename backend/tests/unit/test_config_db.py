"""Unit tests for config_db module — allowlist, get/set/effective config values."""
from datetime import datetime, timezone

import pytest

from app.config_db import (
    EDITABLE_CONFIG_KEYS,
    get_config_value,
    get_effective_config,
    get_effective_value,
    set_config_value,
)
from app.db.models import ConfigEntry


class TestEditableConfigKeys:
    """FR26: only the 9 non-sensitive AdminConfigOut fields are editable."""

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
            "display_timezone",
            "scraper_debug",
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


class TestGetEffectiveValue:
    """FR27: get_effective_value returns DB override or settings default, type-coerced."""

    def test_returns_settings_default_when_no_db_entry(self, db_session):
        from app.config import settings

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == settings.tournament_ingest_limit
        assert isinstance(result, int)

    def test_returns_db_override_as_int(self, db_session):
        entry = ConfigEntry(
            key="tournament_ingest_limit",
            value="42",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == 42
        assert isinstance(result, int)

    def test_falls_back_to_default_for_non_numeric_db_value(self, db_session):
        from app.config import settings

        entry = ConfigEntry(
            key="tournament_ingest_limit",
            value="abc",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == settings.tournament_ingest_limit

    def test_falls_back_to_default_for_empty_db_value(self, db_session):
        from app.config import settings

        entry = ConfigEntry(
            key="tournament_ingest_limit",
            value="",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == settings.tournament_ingest_limit

    def test_returns_db_override_as_str(self, db_session):
        entry = ConfigEntry(
            key="resubmit_times_utc",
            value="14:00,20:00",
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(entry)
        db_session.commit()

        result = get_effective_value(db_session, "resubmit_times_utc")
        assert result == "14:00,20:00"
        assert isinstance(result, str)

    def test_rejects_non_editable_key(self, db_session):
        with pytest.raises(ValueError, match="not an editable config key"):
            get_effective_value(db_session, "database_url")


class TestGetEffectiveConfig:
    """FR27: get_effective_config merges DB entries over settings defaults."""

    def test_returns_all_editable_keys_with_defaults(self, db_session):
        result = get_effective_config(db_session)
        assert set(result.keys()) == EDITABLE_CONFIG_KEYS

    def test_values_match_settings_when_no_db_entries(self, db_session):
        from app.config import settings

        result = get_effective_config(db_session)
        assert result["tournament_ingest_limit"] == settings.tournament_ingest_limit
        assert result["resubmit_times_utc"] == settings.resubmit_times_utc

    def test_db_entries_override_settings_defaults(self, db_session):
        db_session.add(ConfigEntry(
            key="tournament_ingest_limit",
            value="99",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.add(ConfigEntry(
            key="organizer_scan_limit",
            value="200",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_config(db_session)
        assert result["tournament_ingest_limit"] == 99
        assert result["organizer_scan_limit"] == 200

    def test_non_overridden_keys_keep_settings_defaults(self, db_session):
        from app.config import settings

        db_session.add(ConfigEntry(
            key="tournament_ingest_limit",
            value="99",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_config(db_session)
        assert result["tournament_backfill_months"] == settings.tournament_backfill_months


# --- Phase 44 (#113): bool coercion — bool subclasses int ---


class TestBoolCoercion:
    """Fix: isinstance(True, int) is True, so bool must be checked before int."""

    def test_get_effective_value_returns_bool_true_from_db(self, db_session):
        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="true",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "scraper_debug")
        assert result is True
        assert isinstance(result, bool)

    def test_get_effective_value_returns_bool_false_from_db(self, db_session):
        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="false",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "scraper_debug")
        assert result is False
        assert isinstance(result, bool)

    def test_get_effective_value_coerces_1_to_true(self, db_session):
        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="1",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "scraper_debug")
        assert result is True
        assert isinstance(result, bool)

    def test_get_effective_value_coerces_0_to_false(self, db_session):
        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="0",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "scraper_debug")
        assert result is False
        assert isinstance(result, bool)

    def test_get_effective_value_falls_back_for_invalid_bool(self, db_session):
        from app.config import settings

        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="maybe",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "scraper_debug")
        assert result == settings.scraper_debug

    def test_get_effective_config_coerces_bool_key(self, db_session):
        db_session.add(ConfigEntry(
            key="scraper_debug",
            value="true",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_config(db_session)
        assert result["scraper_debug"] is True
        assert isinstance(result["scraper_debug"], bool)

    def test_int_keys_still_coerce_correctly(self, db_session):
        """Ensure the bool fix doesn't break int coercion."""
        db_session.add(ConfigEntry(
            key="tournament_ingest_limit",
            value="42",
            updated_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        result = get_effective_value(db_session, "tournament_ingest_limit")
        assert result == 42
        assert isinstance(result, int)
        assert not isinstance(result, bool)
