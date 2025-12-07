from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from health_aggregator.time_normalization import (
    SleepEvent,
    WorkoutEvent,
    normalize_sleep_records,
    normalize_workout_records,
)
from health_aggregator.daily_aggregation import (
    DailyRecord,
    build_daily_records,
)


def test_build_daily_records_aggregates_correctly():
    # Sleep: 4.5h on Oct 3, 5h on Oct 5
    sleep_raw = [
        {
            "start_time": "2023-10-03T05:45:00Z",
            "end_time": "2023-10-03T10:15:00Z",
        },
        {
            "start_time": "2023-10-05T06:00:00Z",
            "end_time": "2023-10-05T11:00:00Z",
        },
    ]

    # Workouts: one on Oct 3, two on Oct 5
    workouts_raw = [
        {
            "start_time": "2023-10-03 23:15:00 PDT",
            "end_time": "2023-10-04 00:30:00 PDT",
            "calories_burned": 300,
        },
        {
            "start_time": "2023-10-05 06:45:00 PDT",
            "end_time": "2023-10-05 07:15:00 PDT",
            "calories_burned": 180,
        },
        {
            "start_time": "2023-10-05 23:50:00 PDT",
            "end_time": "2023-10-06 00:20:00 PDT",
            "calories_burned": 500,
        },
    ]

    tz = "America/Los_Angeles"
    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workouts_raw, tz)

    records = build_daily_records(sleep_events, workout_events)
    by_day = {r.day.isoformat(): r for r in records}

    # Oct 3: 4.5h sleep, 300 calories, 1 workout
    d3 = by_day["2023-10-03"]
    assert abs(d3.total_sleep_hours - 4.5) < 0.1
    assert abs(d3.total_calories_burned - 300.0) < 0.1
    assert d3.workout_count == 1

    # Oct 5: 5h sleep, 680 calories, 2 workouts
    d5 = by_day["2023-10-05"]
    assert abs(d5.total_sleep_hours - 5.0) < 0.1
    assert abs(d5.total_calories_burned - 680.0) < 0.1
    assert d5.workout_count == 2


def test_day_with_only_sleep_appears_with_zero_workouts():
    sleep_raw = [
        {
            "start_time": "2023-10-08T07:00:00Z",
            "end_time": "2023-10-08T11:00:00Z",
        }
    ]
    workouts_raw = []

    tz = "America/Los_Angeles"
    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workouts_raw, tz)

    records = build_daily_records(sleep_events, workout_events)
    assert len(records) == 1

    r = records[0]
    assert r.workout_count == 0
    assert abs(r.total_calories_burned) < 0.01
    assert r.total_sleep_hours > 0.0


def test_day_with_only_workouts_appears_with_zero_sleep():
    sleep_raw = []
    workouts_raw = [
        {
            "start_time": "2023-10-09 10:00:00 PDT",
            "end_time": "2023-10-09 11:00:00 PDT",
            "calories_burned": 400,
        }
    ]

    tz = "America/Los_Angeles"
    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workouts_raw, tz)

    records = build_daily_records(sleep_events, workout_events)
    assert len(records) == 1

    r = records[0]
    assert abs(r.total_sleep_hours) < 0.01
    assert abs(r.total_calories_burned - 400.0) < 0.1
    assert r.workout_count == 1
