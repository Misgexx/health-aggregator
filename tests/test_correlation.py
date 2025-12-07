from datetime import date

from health_aggregator.daily_aggregation import DailyRecord
from health_aggregator.correlation import compute_sleep_calories_correlation


def test_correlation_basic():
    records = [
        DailyRecord(day=date(2023, 10, 1), total_sleep_hours=8.0, total_calories_burned=350.0, workout_count=1),
        DailyRecord(day=date(2023, 10, 2), total_sleep_hours=5.0, total_calories_burned=400.0, workout_count=1),
        DailyRecord(day=date(2023, 10, 3), total_sleep_hours=4.0, total_calories_burned=200.0, workout_count=1),
    ]

    result = compute_sleep_calories_correlation(records, sleep_threshold_hours=6.0)

    # days below threshold: Oct 2 and Oct 3
    assert result.num_days_below_threshold == 2
    assert result.num_days_total == 3
    assert result.avg_calories_below_threshold == (400.0 + 200.0) / 2
