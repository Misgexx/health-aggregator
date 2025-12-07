# tests/test_time_normalization.py

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from health_aggregator.time_normalization import (
    SleepEvent,
    WorkoutEvent,
    normalize_sleep_records,
    normalize_workout_records,
    parse_utc_timestamp,
    parse_local_timestamp,
)


def test_parse_utc_timestamp_returns_aware_utc():
    raw = "2023-10-01T06:30:00Z"
    dt = parse_utc_timestamp(raw)
    assert dt.tzinfo is not None
    assert dt.tzinfo == timezone.utc
    assert dt.isoformat() == "2023-10-01T06:30:00+00:00"


def test_parse_local_timestamp_with_pdt_abbrev():
    user_tz = ZoneInfo("America/Los_Angeles")
    raw = "2023-10-02 21:30:00 PDT"
    dt = parse_local_timestamp(raw, user_tz)
    # local time should be exactly what we passed in
    assert dt.year == 2023
    assert dt.month == 10
    assert dt.day == 2
    assert dt.hour == 21
    assert dt.minute == 30
    assert dt.tzinfo == user_tz


def test_parse_local_timestamp_without_abbrev():
    user_tz = ZoneInfo("America/Los_Angeles")
    raw = "2023-10-02 22:00:00"
    dt = parse_local_timestamp(raw, user_tz)
    # still interpreted as local time in the given timezone
    assert dt.year == 2023
    assert dt.month == 10
    assert dt.day == 2
    assert dt.hour == 22
    assert dt.minute == 0
    assert dt.tzinfo == user_tz


def test_normalize_sleep_records_basic():
    sleep_raw = [
        {"start_time": "2023-10-01T06:30:00Z", "end_time": "2023-10-01T14:30:00Z"}
    ]
    events = normalize_sleep_records(sleep_raw, "America/Los_Angeles")
    assert len(events) == 1

    e = events[0]
    assert isinstance(e, SleepEvent)
    # 8 hours
    duration = (e.end_local - e.start_local).total_seconds() / 3600.0
    assert abs(duration - 8.0) < 0.1


def test_sleep_end_before_start_is_skipped():
    sleep_raw = [
        {"start_time": "2023-10-02T10:00:00Z", "end_time": "2023-10-02T06:00:00Z"}
    ]
    events = normalize_sleep_records(sleep_raw, "America/Los_Angeles")
    # invalid: end < start, so no events
    assert len(events) == 0


def test_normalize_workout_records_basic():
    workouts_raw = [
        {
            "start_time": "2023-10-03 23:15:00 PDT",
            "end_time": "2023-10-04 00:30:00 PDT",
            "calories_burned": 300,
        }
    ]
    events = normalize_workout_records(workouts_raw, "America/Los_Angeles")
    assert len(events) == 1

    w = events[0]
    assert isinstance(w, WorkoutEvent)
    assert w.calories_burned == 300.0
    # duration ≈ 1.25h
    duration = (w.end_local - w.start_local).total_seconds() / 3600.0
    assert abs(duration - 1.25) < 0.1


def test_workout_missing_calories_defaults_to_zero():
    workouts_raw = [
        {
            "start_time": "2023-10-02 10:00:00 PDT",
            "end_time": "2023-10-02 10:30:00 PDT",
        }
    ]
    events = normalize_workout_records(workouts_raw, "America/Los_Angeles")
    assert len(events) == 1
    assert events[0].calories_burned == 0.0


def test_workout_without_timezone_abbrev_parses_as_local():
    workouts_raw = [
        {
            "start_time": "2023-10-02 22:00:00",
            "end_time": "2023-10-02 23:00:00",
            "calories_burned": 300,
        }
    ]
    events = normalize_workout_records(workouts_raw, "America/Los_Angeles")
    assert len(events) == 1

    w = events[0]
    # should be treated as America/Los_Angeles local time
    assert w.start_local.tzinfo == ZoneInfo("America/Los_Angeles")
    assert w.start_local.hour == 22
    assert w.start_local.minute == 0


def test_workout_invalid_calories_skipped():
    workouts_raw = [
        {
            "start_time": "2023-10-03 10:00:00 PDT",
            "end_time": "2023-10-03 11:00:00 PDT",
            "calories_burned": "???",
        }
    ]
    events = normalize_workout_records(workouts_raw, "America/Los_Angeles")
    # invalid calories → skip
    assert len(events) == 0
