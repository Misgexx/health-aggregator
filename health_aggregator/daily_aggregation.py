from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List

from .time_normalization import SleepEvent, WorkoutEvent



@dataclass
class DailyRecord:
    day: date
    total_sleep_hours: float
    total_calories_burned: float
    workout_count: int



def _aggregate_sleep_by_day(sleep_events: List[SleepEvent]) -> Dict[date, float]:
    """
    Split sleep across midnight correctly.

    Example:
        10 PM → 4 AM (6 hours total)
        Should all map to wake-up day, but split if needed.

    Tests expect:
    - Sleep spanning midnight still yields total hours = end - start
    - Wake-up day = end_local.date()
    """
    result: Dict[date, float] = {}

    for e in sleep_events:

        # Compute duration in hours
        duration_seconds = (e.end_local - e.start_local).total_seconds()
        hours = duration_seconds / 3600.0

        # Assign entire sleep duration to wake-up day
        wake_day = e.end_local.date()

        result[wake_day] = result.get(wake_day, 0.0) + hours

    return result



def _aggregate_workouts_by_day(workouts: List[WorkoutEvent]) -> Dict[date, Dict[str, float]]:
    """
    Workouts assign to the start_local date, not the end date.

    This satisfies:
    - test_workout_crossing_midnight_maps_correct_day
    """
    result: Dict[date, Dict[str, float]] = {}

    for w in workouts:
        workout_day = w.start_local.date()

        if workout_day not in result:
            result[workout_day] = {"calories": 0.0, "count": 0}

        result[workout_day]["calories"] += w.calories_burned
        result[workout_day]["count"] += 1

    return result



def build_daily_records(
    sleep_events: List[SleepEvent],
    workout_events: List[WorkoutEvent],
) -> List[DailyRecord]:
    """
    Combine sleep and workout per-day aggregates.
    """
    sleep_by_day = _aggregate_sleep_by_day(sleep_events)
    workouts_by_day = _aggregate_workouts_by_day(workout_events)

    # union of all days in either dataset
    all_days = sorted(set(sleep_by_day.keys()) | set(workouts_by_day.keys()))

    daily_records: List[DailyRecord] = []

    for d in all_days:
        sleep_hours = sleep_by_day.get(d, 0.0)
        workout_info = workouts_by_day.get(d, {"calories": 0.0, "count": 0})

        daily_records.append(
            DailyRecord(
                day=d,
                total_sleep_hours=round(sleep_hours, 2),
                total_calories_burned=round(workout_info["calories"], 2),
                workout_count=int(workout_info["count"]),
            )
        )

    return daily_records


def aggregate_daily(
    sleep_events: List[SleepEvent],
    workout_events: List[WorkoutEvent],
    user_tz_str: str,
) -> List[DailyRecord]:
    """
    Tests call this as the main entrypoint.
    user_tz_str is unused because timestamps were already normalized.
    """
    return build_daily_records(sleep_events, workout_events)



if __name__ == "__main__":
    import json
    from pathlib import Path
    from .time_normalization import normalize_sleep_records, normalize_workout_records

    ROOT = Path(__file__).resolve().parents[1]
    data_dir = ROOT / "sample_data"

    with open(data_dir / "sleep.json", "r") as f:
        sleep_raw = json.load(f)
    with open(data_dir / "workouts.json", "r") as f:
        workout_raw = json.load(f)

    tz = "America/Los_Angeles"
    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workout_raw, tz)

    records = build_daily_records(sleep_events, workout_events)

    print("\nDaily records:")
    for r in records:
        print(r)
