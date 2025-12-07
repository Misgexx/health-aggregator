from __future__ import annotations

import argparse
import json
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path
from typing import Any, Dict, List

from health_aggregator.time_normalization import (
    normalize_sleep_records,
    normalize_workout_records,
)
from health_aggregator.daily_aggregation import build_daily_records, DailyRecord
from health_aggregator.correlation import (
    compute_sleep_calories_correlation,
    CorrelationResult,
)



def load_json_file(path: Path, label: str) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"Error: {label} file not found at '{path}'.", file=sys.stderr)
        sys.exit(1)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: {label} file at '{path}' is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print(
            f"Error: expected {label} file at '{path}' to contain a JSON array of records.",
            file=sys.stderr,
        )
        sys.exit(1)

    return data


def print_daily_table(daily_records: List[DailyRecord]) -> None:
    if not daily_records:
        print("No daily records to display.")
        return

    print("\nPer-day summary (local dates):")
    print(f"{'Date':<12} {'Sleep(h)':>9} {'Calories':>10} {'Workouts':>10}")

    for r in daily_records:
        print(
            f"{r.day.isoformat():<12} "
            f"{r.total_sleep_hours:>9.2f} "
            f"{r.total_calories_burned:>10.2f} "
            f"{r.workout_count:>10d}"
        )


def print_correlation(result: CorrelationResult) -> None:
    print("\nCorrelation: sleep vs calories")
    print(f"Total days analyzed: {result.num_days_total}")
    print(f"Sleep threshold: {result.sleep_threshold_hours} hours")
    print(f"Days below threshold: {result.num_days_below_threshold}")

    if result.avg_calories_below_threshold is None:
        print("No days with sleep below threshold; metric is undefined.")
    else:
        print(
            f"Average calories on days with < {result.sleep_threshold_hours}h sleep: "
            f"{result.avg_calories_below_threshold}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Personal Health Data Aggregator: "
            "merge sleep (UTC) and workouts (local time) into daily records "
            "and compute a simple sleep/calories correlation."
        )
    )

    parser.add_argument(
        "--sleep",
        required=True,
        help="Path to sleep.json (timestamps in UTC).",
    )
    parser.add_argument(
        "--workouts",
        required=True,
        help="Path to workouts.json (timestamps in local time).",
    )
    parser.add_argument(
        "--timezone",
        default="America/Los_Angeles",
        help="IANA timezone for the user (default: America/Los_Angeles).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=6.0,
        help="Sleep threshold in hours for correlation (default: 6.0).",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write merged daily records as JSON.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError:
        print(
            f"Error: invalid timezone '{args.timezone}'. "
            "Please use a valid IANA timezone like 'America/Los_Angeles'.",
            file=sys.stderr,
        )
        sys.exit(1)

    sleep_path = Path(args.sleep)
    workouts_path = Path(args.workouts)
    user_tz = args.timezone
    threshold = args.threshold
    output_path = Path(args.output) if args.output else None
    
    # 1) Load raw JSON
    sleep_raw = load_json_file(sleep_path, "sleep")
    workouts_raw = load_json_file(workouts_path, "workouts")

    # 2) Normalize timestamps
    sleep_events = normalize_sleep_records(sleep_raw, user_tz)
    workout_events = normalize_workout_records(workouts_raw, user_tz)

    if not sleep_events:
        print(
            "Warning: no valid sleep records after normalization; "
            "sleep-based metrics may be meaningless.",
            file=sys.stderr,
        )
    if not workout_events:
        print(
            "Warning: no valid workout records after normalization; "
            "calorie metrics may be meaningless.",
            file=sys.stderr,
        )

    # 3) Build daily records
    daily_records = build_daily_records(sleep_events, workout_events)

    # 4) Compute correlation
    corr = compute_sleep_calories_correlation(daily_records, threshold)

    # 5) Print results
    print_daily_table(daily_records)
    print_correlation(corr)

    # 6) Optional JSON output
    if output_path is not None:
        serialized = [
            {
                "date": r.day.isoformat(),
                "total_sleep_hours": r.total_sleep_hours,
                "total_calories_burned": r.total_calories_burned,
                "workout_count": r.workout_count,
            }
            for r in daily_records
        ]
        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(serialized, f, indent=2)
            print(f"\nMerged daily records written to: {output_path}")
        except OSError as e:
            print(f"Error: failed to write output file '{output_path}': {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
