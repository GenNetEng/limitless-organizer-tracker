from app.celery_app import celery_app, parse_resubmit_times


def test_parse_resubmit_times_parses_multiple_times():
    assert parse_resubmit_times("09:00,21:00") == [(9, 0), (21, 0)]


def test_parse_resubmit_times_strips_whitespace():
    assert parse_resubmit_times(" 09:00 , 21:00 ") == [(9, 0), (21, 0)]


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
