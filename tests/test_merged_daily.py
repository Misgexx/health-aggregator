from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from health_aggregator.time_normalization import SleepEvent, WorkoutEvent
from health_aggregator.daily_aggregation import DailyRecord, aggregate_daily


def make_sleep(utc_start: datetime, utc_end: datetime, tz: str = "America/Los_Angeles") -> SleepEvent:
    """
    Helper to create a SleepEvent from UTC datetimes.
    """
    utc_start = utc_start.replace(tzinfo=timezone.utc)
    utc_end = utc_end.replace(tzinfo=timezone.utc)
    local_tz = ZoneInfo(tz)

    return SleepEvent(
        raw_start=utc_start.isoformat(),
        raw_end=utc_end.isoformat(),
        start_utc=utc_start,
        end_utc=utc_end,
        start_local=utc_start.astimezone(local_tz),
        end_local=utc_end.astimezone(local_tz),
    )


def make_workout(
    utc_start: datetime,
    utc_end: datetime,
    calories: float = 100.0,
    tz: str = "America/Los_Angeles",
) -> WorkoutEvent:
    """
    Helper to construct a WorkoutEvent from UTC datetimes.
    """
    utc_start = utc_start.replace(tzinfo=timezone.utc)
    utc_end = utc_end.replace(tzinfo=timezone.utc)
    local_tz = ZoneInfo(tz)

    return WorkoutEvent(
        raw_start=utc_start.isoformat(),
        raw_end=utc_end.isoformat(),
        start_utc=utc_start,
        end_utc=utc_end,
        start_local=utc_start.astimezone(local_tz),
        end_local=utc_end.astimezone(local_tz),
        calories_burned=calories,
    )


def test_workout_crossing_midnight_maps_correct_day():
    """
    Workout 07:30 UTC → 00:30 local (PDT). It should be assigned to the *local* day of 00:30.
    """
    w = make_workout(
        datetime(2023, 10, 3, 7, 30),  # 00:30 local PDT
        datetime(2023, 10, 3, 8, 0),
        calories=250,
    )

    records = aggregate_daily([], [w], "America/Los_Angeles")
    assert len(records) == 1
    # local date: 2023-10-03
    assert records[0].day.isoformat() == "2023-10-03"
    assert records[0].total_calories_burned == 250.0
    assert records[0].workout_count == 1


def test_sleep_spanning_midnight_assigns_to_wake_day():
    """
    Sleep 22:00–04:00 local should be assigned to the *wake-up* day (04:00 local).
    """
    # 22:00 PDT (previous day) ~ 05:00 UTC
    start_utc = datetime(2023, 10, 2, 5, 0)
    # 04:00 PDT ~ 11:00 UTC
    end_utc = datetime(2023, 10, 2, 11, 0)

    s = make_sleep(start_utc, end_utc)
    records = aggregate_daily([s], [], "America/Los_Angeles")

    assert len(records) == 1
    # Wake-up local date is 2023-10-02
    assert records[0].day.isoformat() == "2023-10-02"
    # about 6h
    assert abs(records[0].total_sleep_hours - 6.0) < 0.5


def test_multiple_sleep_segments_sum_correctly():
    """
    Two sleep segments on the same wake-up day should sum their durations.
    """
    s1 = make_sleep(
        datetime(2023, 10, 3, 6),  # → local night
        datetime(2023, 10, 3, 10),
    )
    s2 = make_sleep(
        datetime(2023, 10, 3, 12),
        datetime(2023, 10, 3, 14),
    )

    records = aggregate_daily([s1, s2], [], "America/Los_Angeles")
    assert len(records) == 1

    total = records[0].total_sleep_hours
    # 4h + 2h = 6h
    assert abs(total - 6.0) < 0.5


def test_days_with_only_workouts_still_appear():
    """
    A day with workouts but no sleep should appear with zero sleep hours.
    """
    w = make_workout(
        datetime(2023, 10, 5, 15),
        datetime(2023, 10, 5, 16),
        calories=500,
    )

    records = aggregate_daily([], [w], "America/Los_Angeles")
    assert len(records) == 1

    r = records[0]
    assert r.day.isoformat() == "2023-10-05"
    assert abs(r.total_sleep_hours) < 0.01
    assert r.total_calories_burned == 500.0
    assert r.workout_count == 1


def test_days_with_only_sleep_still_appear():
    """
    A day that has sleep but no workouts should still appear.
    """
    s = make_sleep(
        datetime(2023, 10, 8, 7),
        datetime(2023, 10, 8, 10),
    )

    records = aggregate_daily([s], [], "America/Los_Angeles")
    assert len(records) == 1

    r = records[0]
    assert r.day.isoformat() == "2023-10-08"
    assert r.total_sleep_hours > 0.0
    assert r.total_calories_burned == 0.0
    assert r.workout_count == 0


def test_dst_transition_fall_back():
    """
    DST ends Nov 5, 2023 at 2 AM.
    06:00–14:00 UTC around that boundary should still yield a sensible duration (~8h).
    """
    s = make_sleep(
        datetime(2023, 11, 5, 6),
        datetime(2023, 11, 5, 14),
    )

    records = aggregate_daily([s], [], "America/Los_Angeles")
    assert len(records) == 1

    # Approximately 8 hours of sleep (allow small tolerance)
    assert abs(records[0].total_sleep_hours - 8.0) <= 1.0



def test_missing_or_empty_lists_produce_zero_days():
    records = aggregate_daily([], [], "America/Los_Angeles")
    assert records == []
