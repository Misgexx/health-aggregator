# Personal Health Data Aggregator (CLI)

This project provides a command-line tool that processes separate **sleep** and **workout** datasets, normalizes their timestamps, merges them into daily summaries, and computes cross-day metrics such as the relationship between sleep duration and calories burned.

The CLI is built for **messy, real-world data**, including missing fields, invalid timestamps, mixed time formats, midnight crossings, and Daylight Savings time boundaries.

---

## 1. Problem Addressed

Sleep records are provided in **UTC**, while workout records are provided in **local time**, often inconsistently formatted.

The tool solves this by:

- **Normalizing all timestamps reliably**
- **Merging both datasets into a unified daily table**
- **Computing metrics** over the merged dataset
- **Exporting results** to console and JSON
- Structuring the logic into small, testable modules

---

## 2. Design Summary

### Timestamp Normalization

- Sleep events include **start_time** and **end_time**, always in **UTC**.
- Workout events include a single **local timestamp**; an artificial **1-hour duration** is added to define their end time.

Each normalized event includes:

- Raw timestamp  
- UTC timestamp  
- Local timestamp  
- For workouts: derived local start/end window and calories

The project uses:

- `dateutil` for robust timestamp parsing
- `zoneinfo` for accurate timezone conversions and DST handling

---

### Daily Aggregation

After normalization:

- Sleep duration is measured in **seconds**, then converted to **hours**, and attributed to the **wake-up day** (`end_local.date()`).
- Workouts are grouped by their **local start date**.
- Sleep duration uses Python’s built-in `datetime` arithmetic for precision.

Each merged day is represented as a `DailyRecord` containing:

- `date`
- `total_sleep_hours`
- `total_calories`
- `workout_count`

Days appear in the output even if they contain only sleep data or only workout data.

---

### Correlation Calculation

Computed daily metrics include:

- Total sleep hours  
- Total calories burned  
- Workout count  
- Average calories burned on days where sleep falls below a user-defined threshold (default **6 hours**)  
- Count of days below the sleep threshold  
- Total number of valid days included in the analysis  

All metrics operate on the finalized merged dataset for consistency.

---

## 3. CLI Usage

Run the program:

    python main.py \
      --sleep sample_data/sleep.json \
      --workouts sample_data/workouts.json \
      --timezone "America/Los_Angeles" \
      --output merged_daily.json

### Arguments

| Flag         | Description                                                  |
|--------------|--------------------------------------------------------------|
| `--sleep`    | Path to sleep JSON file                                      |
| `--workouts`| Path to workouts JSON file                                    |
| | `--timezone` | User’s timezone ([IANA](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) format) |
| `--threshold`| Sleep threshold in hours                                     |
| `--output`   | Optional output JSON path                                    |

The CLI prints a full daily summary with correlation metrics and optionally writes the merged dataset to disk.

### Default Timezone

If not specified, the tool uses:

    America/Los_Angeles

This ensures consistent test behavior, but users should supply their correct timezone for real data.

---

## 4. Approach & Technical Reasoning

### Parsing & Timezones

`dateutil.parser` handles:

- ISO timestamps  
- Mixed formats  
- Timestamps with or without timezone abbreviations  
- Ambiguous local times  

`zoneinfo` is used for:

- Assigning the user’s timezone to local timestamps
- Converting UTC → local reliably
- Handling DST transitions without manual offset logic

---

### Handling Imperfect Input

The tool avoids crashing on malformed data:

- Invalid or incomplete records are **skipped with a warning**
- Missing numerical fields receive **safe defaults**

This makes the tool suitable for messy, device-exported data rather than curated academic datasets.

---

### Precision Decisions

Sleep duration is computed with standard `datetime` arithmetic and stored directly in **hours**, matching all other sleep metrics in the pipeline.

---

### Modular Structure

| Module                 | Purpose                                             |
|------------------------|-----------------------------------------------------|
| `time_normalization.py`| Converts raw records into timezone-aware events     |
| `daily_aggregation.py` | Merges sleep & workouts into daily totals           |
| `correlation.py`       | Computes statistics                                 |
| `main.py`              | CLI interface, file loading, output formatting      |

This architecture keeps logic clear, testable, and maintainable.

---

## 5. Methodology

### Python Libraries Used

- **datetime** — Safe duration math and timestamp handling  
- **zoneinfo** — Correct timezone rules and DST handling  
- **pathlib** — Cross-platform file path handling  
- **typing** — Type hints for clarity and maintainability  

---

### Testing

Custom unit tests cover:

- Midnight crossings  
- DST transitions  
- Invalid timestamps  
- Missing fields  
- Aggregation correctness  

Additional testing included stress-testing with intentionally messy datasets that resemble exported device logs.

---

### AI Assistance

AI tools were used during early planning and experimentation:

- ChatGPT and Claude were used to brainstorm approaches, draft initial code structures, and refine handling of edge cases.
- A key design decision was how to attribute overnight sleep (e.g., **10 PM → 8 AM**):
  - Start date  
  - Wake-up day  
  - Split across both  

After reviewing how major health apps behave and considering how people interpret daily sleep, overnight sleep is attributed to the **wake-up day**. This avoids confusing splits across dates and aligns with how sleep impacts the following day.

Copilot was used occasionally for in-editor suggestions and debugging assistance, but all logic decisions, timezone handling rules, and aggregation behaviors were designed and implemented manually.

---

### Verification

Correctness was validated by:

- Creating sample datasets that intentionally contain:
  - Invalid timestamps
  - Missing fields
  - Local timestamps without timezone abbreviations
  - DST fall-back scenarios
  - Midnight-spanning workouts and sleep windows
- Writing automated tests that assert:
  - Wake-day assignment
  - Correct handling of local/UTC conversions
  - Daily merging logic
  - Stable behavior across DST transitions
  - Non-crashing behavior for malformed input
- Running CLI executions to confirm end-to-end consistency

All tests pass successfully.

---

## 6. Output Structure

When `--output` is provided, the generated JSON takes the form:

    [
      {
        "date": "2023-10-01",
        "total_sleep_hours": 8.0,
        "total_calories_burned": 350.0,
        "workout_count": 1
      }
    ]
