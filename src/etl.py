"""Clean synthetic events and load them into an idempotent SQLite table."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "events.csv"
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "processed" / "events.db"
DEFAULT_CLEAN_CSV = PROJECT_ROOT / "data" / "processed" / "clean_events.csv"
DEFAULT_REPORT = PROJECT_ROOT / "data" / "processed" / "data_quality_report.json"
REQUIRED_COLUMNS = [
    "event_id", "event_name", "event_date", "city", "genre", "capacity",
    "tickets_sold", "ticket_price", "data_source",
]


def clean_events(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    """Validate and clean source rows, returning clean data and a quality report."""
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")

    report: dict[str, object] = {
        "synthetic_data": True,
        "source_rows": int(len(raw)),
        "missing_values_by_column": {
            str(column): int(count)
            for column, count in raw.isna().sum().items()
            if int(count) > 0
        },
    }

    data = raw.copy()
    exact_duplicate_mask = data.duplicated(keep="first")
    report["duplicate_rows"] = int(exact_duplicate_mask.sum())
    data = data.loc[~exact_duplicate_mask].copy()

    duplicate_id_mask = data["event_id"].duplicated(keep="first")
    report["duplicate_event_ids"] = int(duplicate_id_mask.sum())
    data = data.loc[~duplicate_id_mask].copy()

    data["event_date"] = pd.to_datetime(data["event_date"], errors="coerce")
    numeric_columns = ["capacity", "tickets_sold", "ticket_price"]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    required_missing = data[REQUIRED_COLUMNS].isna().any(axis=1)
    invalid_date = data["event_date"].isna()
    invalid_capacity = data["capacity"].le(0)
    invalid_tickets = data["tickets_sold"].lt(0) | data["tickets_sold"].gt(data["capacity"])
    invalid_price = data["ticket_price"].lt(0)
    invalid_mask = required_missing | invalid_date | invalid_capacity | invalid_tickets | invalid_price
    report["invalid_rows"] = int(invalid_mask.sum())
    report["invalid_row_ids"] = [str(value) for value in data.loc[invalid_mask, "event_id"].tolist()]
    data = data.loc[~invalid_mask].copy()

    data["venue"] = data["venue"].fillna("Unknown venue")
    data["event_date"] = data["event_date"].dt.strftime("%Y-%m-%d")
    data["capacity"] = data["capacity"].astype(int)
    data["tickets_sold"] = data["tickets_sold"].astype(int)
    data["ticket_price"] = data["ticket_price"].round(2)
    dates = pd.to_datetime(data["event_date"])
    data["year"] = dates.dt.year
    data["month"] = dates.dt.month
    data["month_label"] = dates.dt.strftime("%Y-%m")
    data["revenue"] = (data["tickets_sold"] * data["ticket_price"]).round(2)
    data["occupancy_rate"] = (data["tickets_sold"] / data["capacity"]).round(4)

    report["clean_rows"] = int(len(data))
    report["removed_rows"] = int(report["source_rows"]) - len(data)
    return data.reset_index(drop=True), report


def load_to_sqlite(events: pd.DataFrame, database_path: Path) -> int:
    """Create the events table and upsert records by stable event ID."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_name TEXT NOT NULL,
                event_date TEXT NOT NULL,
                city TEXT NOT NULL,
                venue TEXT NOT NULL,
                genre TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                tickets_sold INTEGER NOT NULL,
                ticket_price REAL NOT NULL,
                data_source TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                month_label TEXT NOT NULL,
                revenue REAL NOT NULL,
                occupancy_rate REAL NOT NULL
            )"""
        )
        columns = list(events.columns)
        column_sql = ", ".join(f'"{column}"' for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        updates = ", ".join(
            f'"{column}" = excluded."{column}"' for column in columns if column != "event_id"
        )
        connection.executemany(
            f"INSERT INTO events ({column_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT(event_id) DO UPDATE SET {updates}",
            events.itertuples(index=False, name=None),
        )
        return int(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])


def run_etl(
    input_path: Path = DEFAULT_INPUT,
    database_path: Path = DEFAULT_DATABASE,
    clean_csv_path: Path = DEFAULT_CLEAN_CSV,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, object]:
    """Run extract, clean, report, and load steps using explicit or default paths."""
    raw = pd.read_csv(input_path)
    clean, report = clean_events(raw)
    clean_csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(clean_csv_path, index=False)
    report["database_rows"] = load_to_sqlite(clean, database_path)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    report = run_etl(input_path=args.input, database_path=args.database)
    print(
        "ETL complete: "
        f"{report['clean_rows']} clean rows loaded; "
        f"{report['duplicate_rows']} exact duplicates, "
        f"{report['invalid_rows']} invalid rows."
    )


if __name__ == "__main__":
    main()