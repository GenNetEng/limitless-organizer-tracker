from app.celery_app import _hourly_schedule, celery_app, parse_resubmit_times


def test_parse_resubmit_times_parses_multiple_times():
    assert parse_resubmit_times("09:00,21:00") == [(9, 0), (21, 0)]


def test_parse_resubmit_times_strips_whitespace():
    assert parse_resubmit_times(" 09:00 , 21:00 ") == [(9, 0), (21, 0)]


def test_parse_resubmit_times_empty_string_returns_no_times():
    assert parse_resubmit_times("") == []


def test_parse_resubmit_times_skips_blank_entries():
    assert parse_resubmit_times("09:00,,21:00,") == [(9, 0), (21, 0)]


def test_hourly_schedule_treats_zero_interval_as_hourly():
    assert _hourly_schedule(0).hour == _hourly_schedule(1).hour


def test_hourly_schedule_treats_negative_interval_as_hourly():
    assert _hourly_schedule(-1).hour == _hourly_schedule(1).hour


def test_beat_schedule_includes_status_check_task():
    schedule = celery_app.conf.beat_schedule

    assert "check-application-status" in schedule
    assert (
        schedule["check-application-status"]["task"]
        == "app.tasks.status_tasks.check_application_status_task"
    )


def test_beat_schedule_includes_one_entry_per_resubmit_time():
    schedule = celery_app.conf.beat_schedule

    resubmit_entries = {
        name: entry for name, entry in schedule.items() if name.startswith("resubmit-application-")
    }

    assert len(resubmit_entries) == 2
    assert all(
        entry["task"] == "app.tasks.resubmit_tasks.resubmit_application_task"
        for entry in resubmit_entries.values()
    )


def test_beat_schedule_includes_tournament_ingestion_task():
    schedule = celery_app.conf.beat_schedule

    assert "ingest-tournaments" in schedule
    assert (
        schedule["ingest-tournaments"]["task"]
        == "app.tasks.tournament_tasks.ingest_tournaments_task"
    )
