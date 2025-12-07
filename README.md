Personal Health Data Aggregator (CLI)

This project provides a command-line tool that processes separate sleep and workout datasets, normalizes their timestamps, merges them into daily summaries, and computes cross-day metrics such as the relationship between sleep duration and calories burned.

The CLI is built specifically to operate on messy, real-world-style data, which may include missing fields, invalid timestamps, mixed time formats, midnight crossings, and Daylight Savings boundaries.

1. Problem Addressed

Sleep records are provided in UTC, while workout records are provided in local time, often with inconsistent formatting.
The goal is to:

Normalize all timestamps reliably

Merge the two datasets into a single daily table

Compute metrics over the merged dataset

Produce output in both console and JSON formats

The logic is implemented in small, testable modules.

2. Design Summary
Timestamp Normalization

Sleep events include start_time and end_time, always in UTC.
Workout events include a single local timestamp. To properly support duration-based metrics, workout events were extended to include a derived end_time based on a default 1-hour duration.

Normalization outputs each event with:

raw timestamp

UTC timestamp

local timestamp

(workouts) a start/end local window and calories

The project uses the dateutil library to parse a wide range of timestamp formats, the built-in zoneinfo library provides accurate timezone conversions, automatically applying the correct rules for daylight-saving transitions.

Daily Aggregation

After normalization:

Sleep duration is measured in seconds and ultimately attributed to the wake-up day (based on end_local.date()).

Workouts are grouped by the local start date.

Sleep duration is computed using Python’s built-in datetime arithmetic and stored directly in hours.
This keeps the aggregation logic consistent with the rest of the program, which expresses all sleep metrics in hours.

The final merged dataset consists of DailyRecord objects including:

date

total sleep hours

total calories

workout count

The aggregator merges sleep and workout data by calendar day, and a day is included even if it contains only sleep data or only workout data.
Correlation Calculation

The tool computes summary metrics over the merged per-day dataset.

Total sleep hours per day.
Total calories burned per day.
Workout count per day.
Average calories burned on days where sleep falls below a user-defined threshold (default = 6 hours).
Number of days below the sleep threshold.
Total number of days included in the analysis, reflecting how many valid merged daily entries were produced.


All calculations use the finalized daily aggregation, ensuring consistency.

3. CLI Usage

Run the program as follows:

python main.py \
  --sleep sample_data/sleep.json \
  --workouts sample_data/workouts.json \
  --timezone "America/Los_Angeles" \
  --output merged_daily.json

Arguments
Flag	Description
--sleep	Path to sleep JSON file
--workouts	Path to workouts JSON file
--timezone — User's timezone (IANA format): https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
--threshold	Sleep threshold in hours
--output	Optional output JSON path


The CLI prints a full daily summary plus correlation metrics and—if requested—writes the merged dataset to disk.

Default Timezone**

If no timezone is provided, the tool uses `"America/Los_Angeles"` as the default.  
This ensures consistent behavior for testing and examples, but users should always specify their own timezone when running real data.
4. Approach & Technical Reasoning
Parsing and Timezones

Timestamp parsing is performed with dateutil.parser, which handles:

ISO formats

timestamps with or without timezone abbreviations

ambiguous local times

zoneinfo is used to assign the user’s timezone to local timestamps and convert UTC → local.
This eliminates the need for hand-rolled offset calculations, especially around DST transitions.

Handling Imperfect Input

The code intentionally avoids failing on malformed data.
Invalid or incomplete records are skipped with a warning, and missing numerical values are set to safe defaults.
This makes the tool suitable for datasets that resemble exported device logs, not curated academic data.

Precision Decisions

Sleep duration is computed using Python’s built-in datetime arithmetic and stored directly in hours.
This keeps the aggregation logic consistent with the rest of the program, which expresses all sleep metrics in hours.


Modular Structure

Each stage is encapsulated:

Module	Purpose
time_normalization.py	Converts raw records into timezone-aware events
daily_aggregation.py	Merges sleep & workout events into daily totals
correlation.py	Performs statistical computations
main.py	CLI, file loading, and output formatting

This separation keeps logic readable and testable.

5. Methodology

Python libraries Used

datetime — Handles timestamp parsing and duration calculations safely.

zoneinfo — Applies the correct IANA timezone rules, including DST transitions, when converting times.

pathlib — Provides reliable cross-platform file path handling for reading and writing data files.

typing — Supplies type hints that make the code easier to understand and maintain.


Testing: custom unit tests covering midnight crossings, DST, invalid timestamps, missing fields, and aggregation rules

AI Assistance:
ChatGPT was used for brainstorming approaches, drafting initial code structures, and refining edge-case handling. It was also used to help generate sample sleep and 
workout datasets for stress-testing the normalization and aggregation logic. 
I used ChatGPT and Claude during early planning to explore alternative interpretations of sleep and workout attribution rules, particularly for events that cross midnight. For example, when evaluating whether a sleep window from 10 PM → 8 AM should be assigned to the day it began, the wake-up day, or both, I reviewed how real health apps behave and compared reasoning suggested by the models. Major health platforms assign overnight sleep to the wake-up day because splitting sleep across two dates or attaching it to the start date produces confusing and misleading summaries, especially when sleep crosses midnight. It also aligns with how sleep affects the following day in real life and how most fitness platforms interpret overnight rest. It then led me to ultimately chose the wake-up day.

Copilot was used occasionally for in-editor suggestions and debugging assistance, but all logic decisions, timezone handling rules, and aggregation behaviors were designed 
and implemented manually.

Verification

I validated correctness by:

Creating sample datasets that intentionally contain:

Invalid timestamps

Missing fields

Local timestamps without timezone abbreviations

DST fall-back scenarios

Midnight-spanning workouts and sleep windows

Writing automated tests that assert:

Wake-day assignment

Correct handling of local/UTC conversions

Daily merging logic

Stable behavior across DST transitions

Non-crashing behavior for malformed input

Running CLI executions to confirm end-to-end consistency.

All tests pass successfully.

6. Output Structure

The generated JSON file (if --output is provided) contains:

[
  {
    "date": "2023-10-01",
    "total_sleep_hours": 8.0,
    "total_calories_burned": 350.0,
    "workout_count": 1
  },
  ...
]
