from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .daily_aggregation import DailyRecord
from .time_normalization import normalize_sleep_records, normalize_workout_records


@dataclass
class CorrelationResult:
    sleep_threshold_hours: float
    num_days_below_threshold: int
    avg_calories_below_threshold: Optional[float]
    num_days_total: int


def compute_sleep_calories_correlation(
    daily_records: List[DailyRecord],
    sleep_threshold_hours: float = 6.0,
) -> CorrelationResult:
    """
    Compute:
      - how many days had sleep < threshold
      - average calories burned on those days

    Returns None for avg_calories_below_threshold if there are no such days.
    """
    below = [
        r.total_calories_burned
        for r in daily_records
        if r.total_sleep_hours < sleep_threshold_hours
    ]

    num_below = len(below)
    avg_below: Optional[float]

    if num_below == 0:
        avg_below = None
    else:
        avg_below = round(sum(below) / num_below, 2)

    return CorrelationResult(
        sleep_threshold_hours=sleep_threshold_hours,
        num_days_below_threshold=num_below,
        avg_calories_below_threshold=avg_below,
        num_days_total=len(daily_records),
    )



if __name__ == "__main__":
    import json
    from pathlib import Path
    from .daily_aggregation import build_daily_records

    ROOT = Path(__file__).resolve().parents[1]
    data_dir = ROOT / "sample_data"

    with open(data_dir / "sleep.json", "r") as f:
        sleep_raw = json.load(f)
    with open(data_dir / "workouts.json", "r") as f:
        workout_raw = json.load(f)

    tz = "America/Los_Angeles"

    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workout_raw, tz)
    daily_records = build_daily_records(sleep_events, workout_events)

    print("Daily records:")
    for r in daily_records:
        print(r)

    result = compute_sleep_calories_correlation(daily_records, sleep_threshold_hours=6.0)

    print("\nCorrelation result:")
    print(result)

    if result.avg_calories_below_threshold is None:
        print("No days with sleep below threshold.")
    else:
        print(
            f"Average calories on days with < {result.sleep_threshold_hours}h sleep: "
            f"{result.avg_calories_below_threshold}"
        )
