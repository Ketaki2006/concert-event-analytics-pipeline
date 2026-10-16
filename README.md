# Concert & Event Analytics Pipeline

A small, beginner-friendly data engineering project. It generates a reproducible **synthetic** event dataset, cleans and validates it with Pandas, stores it in SQLite, and explores it in a Streamlit dashboard. No records represent real events, attendance, ticket sales, or revenue.

## What is included

- A seeded generator that creates 360 valid synthetic events plus a few deliberate data-quality problems for the report.
- A rerunnable ETL pipeline that extracts the CSV, reports missing/duplicate/invalid data, cleans records, derives date fields, writes a cleaned CSV, and upserts into SQLite.
- A dashboard with event, ticket, and revenue KPIs; city and genre filters; monthly charts; an event table; CSV download; and data-quality details.
- SQL examples and Pytest tests.

All paths are resolved from the project files, not from the terminal's current directory.

## Windows setup

Open PowerShell in the project folder (the folder containing this README). Install Python 3.10 or newer, then run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks environment activation, either permit it for this terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or skip activation and use `.\.venv\Scripts\python.exe` in place of `python` in the commands below.

## Generate data and run the pipeline

```powershell
python -m src.generate_data
python -m src.etl
```

The CSV is written to `data/raw/events.csv`. The ETL writes `data/processed/events.db`, `data/processed/clean_events.csv`, and `data/processed/data_quality_report.json`. Running the ETL again updates existing event IDs rather than inserting duplicate records.

## Run the dashboard

```powershell
python -m streamlit run dashboard/app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. Generate the data and run the ETL at least once before opening the dashboard.

## Run tests

```powershell
python -m pytest
```

Tests use temporary files and do not alter the project's generated database.

## Project layout

```text
concert-event-analytics-pipeline/
|-- dashboard/app.py
|-- data/
|   |-- raw/events.csv
|   `-- processed/                 # generated database, clean CSV, and report
|-- sql/analytics.sql
|-- src/
|   |-- etl.py
|   `-- generate_data.py
|-- tests/test_pipeline.py
|-- .gitignore
|-- README.md
`-- requirements.txt
```

## Data and cleaning notes

Every generated row is fictional, and the dashboard labels its data as synthetic. The generator uses a fixed random seed so regenerating `events.csv` produces the same dataset. It includes 360 valid events, two duplicate rows, and a handful of rows with missing or invalid values to make data-quality handling visible.

The ETL reports missing values before cleaning, removes exact duplicate rows, drops rows with missing required fields or invalid dates/numbers, fills missing venue names with `Unknown venue`, and derives year, month, and month label fields. SQLite's `event_id` primary key and an upsert make reruns safe. Revenue is a derived synthetic value (`tickets_sold * ticket_price`), not real-world sales.

## SQL examples

Open `sql/analytics.sql` in a SQLite client to see monthly, city, and genre analysis. The cleaned table is named `events`.