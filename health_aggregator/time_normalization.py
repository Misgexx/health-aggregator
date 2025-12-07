from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from dateutil import parser
from zoneinfo import ZoneInfo
import sys



@dataclass
class SleepEvent:
    raw_start: str
    raw_end: str
    start_utc: datetime
    end_utc: datetime
    start_local: datetime
    end_local: datetime


@dataclass
class WorkoutEvent:
    raw_start: str
    raw_end: str
    start_utc: datetime
    end_utc: datetime
    start_local: datetime
    end_local: datetime
    calories_burned: float



def parse_utc_timestamp(raw: str) -> datetime:
    """
    Parse timestamps like '2023-10-01T06:30:00Z' or '2023-10-01T06:30:00+00:00'.
    Always returns a UTC-aware datetime.
    """
    dt = parser.isoparse(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def parse_local_timestamp(raw: str, user_tz: ZoneInfo) -> datetime:
    """
    Parses timestamps like:
      '2023-10-01 15:00:00 PDT'
      '2023-10-01 15:00:00'
      '2023-10-01 15:00'

    Removes timezone abbreviations & forces the provided user timezone.
    """
    parts = raw.rsplit(" ", 1)

    # If the right side looks like a TZ abbrev (PST, PDT, UTC, GMT)
    if len(parts) == 2 and parts[1].upper().endswith(("PST", "PDT", "UTC", "GMT")):
        dt_str = parts[0]
    else:
        dt_str = raw

    naive = parser.parse(dt_str)
    return naive.replace(tzinfo=user_tz)


def normalize_sleep_records(
    raw_records: List[Dict[str, Any]],
    user_tz_str: str,
) -> List[SleepEvent]:

    user_tz = ZoneInfo(user_tz_str)
    normalized: List[SleepEvent] = []

    for idx, rec in enumerate(raw_records):
        try:
            raw_start = rec.get("start_time")
            raw_end = rec.get("end_time")

            if not raw_start or not raw_end:
                print(f"Warning: sleep record {idx} missing fields, skipping.", file=sys.stderr)
                continue

            start_utc = parse_utc_timestamp(raw_start)
            end_utc = parse_utc_timestamp(raw_end)

            if end_utc < start_utc:
                print(f"Warning: sleep record {idx} end < start, skipping.", file=sys.stderr)
                continue

            start_local = start_utc.astimezone(user_tz)
            end_local = end_utc.astimezone(user_tz)

            normalized.append(
                SleepEvent(
                    raw_start=raw_start,
                    raw_end=raw_end,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    start_local=start_local,
                    end_local=end_local,
                )
            )

        except Exception as e:
            print(f"Warning: failed to parse sleep record {idx}: {e}", file=sys.stderr)

    return normalized



def normalize_workout_records(
    raw_records: List[Dict[str, Any]],
    user_tz_str: str,
) -> List[WorkoutEvent]:

    user_tz = ZoneInfo(user_tz_str)
    normalized: List[WorkoutEvent] = []

    for idx, rec in enumerate(raw_records):

        raw_start = rec.get("start_time")
        raw_end = rec.get("end_time")

        
        if not raw_start or not raw_end:
            print(f"Warning: workout record {idx} missing start/end, skipping.", file=sys.stderr)
            continue

        try:
            # Local conversion
            start_local = parse_local_timestamp(raw_start, user_tz)
            end_local = parse_local_timestamp(raw_end, user_tz)

            # Convert to UTC
            start_utc = start_local.astimezone(timezone.utc)
            end_utc = end_local.astimezone(timezone.utc)

            if end_utc < start_utc:
                print(f"Warning: workout record {idx} end < start, skipping.", file=sys.stderr)
                continue

            # Calories
            calories_raw = rec.get("calories_burned", 0)
            try:
                calories = float(calories_raw)
            except Exception:
                print(f"Warning: invalid calories in workout record {idx}, skipping.", file=sys.stderr)
                continue

            normalized.append(
                WorkoutEvent(
                    raw_start=raw_start,
                    raw_end=raw_end,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    start_local=start_local,
                    end_local=end_local,
                    calories_burned=calories,
                )
            )

        except Exception as e:
            print(f"Warning: failed to parse workout record {idx}: {e}", file=sys.stderr)

    return normalized


def pretty_print_sleep(events):
    print("\nNormalized Sleep Events:")
    for e in events:
        duration_hours = (e.end_local - e.start_local).total_seconds() / 3600.0
        print(
            f"\nStart (raw):    {e.raw_start}\n"
            f"End (raw):      {e.raw_end}\n"
            f"Start (UTC):    {e.start_utc}\n"
            f"End   (UTC):    {e.end_utc}\n"
            f"Start (local):  {e.start_local}\n"
            f"End   (local):  {e.end_local}\n"
            f"Duration (hrs): {duration_hours:.2f}"
        )
    print("\n" + "-" * 60)


def pretty_print_workouts(events):
    print("\nNormalized Workout Events:")
    for w in events:
        print(
            f"\nStart (raw):    {w.raw_start}\n"
            f"End (raw):      {w.raw_end}\n"
            f"Start (UTC):    {w.start_utc}\n"
            f"End   (UTC):    {w.end_utc}\n"
            f"Start (local):  {w.start_local}\n"
            f"End   (local):  {w.end_local}\n"
            f"Calories:       {w.calories_burned}"
        )
    print("\n" + "-" * 60)


if __name__ == "__main__":
    # Optional manual check for normalized events
    import json
    from pathlib import Path

    DATA_DIR = Path(__file__).resolve().parents[1] / "sample_data"
    sleep_path = DATA_DIR / "sleep.json"
    workouts_path = DATA_DIR / "workouts.json"

    with open(sleep_path, "r", encoding="utf-8") as f:
        sleep_raw = json.load(f)

    with open(workouts_path, "r", encoding="utf-8") as f:
        workouts_raw = json.load(f)

    tz = "America/Los_Angeles"

    sleep_events = normalize_sleep_records(sleep_raw, tz)
    workout_events = normalize_workout_records(workouts_raw, tz)

    pretty_print_sleep(sleep_events)
    pretty_print_workouts(workout_events)

