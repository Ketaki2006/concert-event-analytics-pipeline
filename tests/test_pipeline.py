import sqlite3

import pandas as pd

from src.etl import clean_events, run_etl
from src.generate_data import create_synthetic_events


def test_generator_is_reproducible_and_has_over_300_valid_events():
    first = create_synthetic_events()
    second = create_synthetic_events()

    pd.testing.assert_frame_equal(first, second)
    assert len(first) >= 300
    assert first["data_source"].str.startswith("SYNTHETIC").all()


def test_cleaning_reports_issues_and_derives_fields():
    raw = create_synthetic_events()
    clean, report = clean_events(raw)

    assert report["source_rows"] > report["clean_rows"] >= 300
    assert report["duplicate_rows"] >= 1
    assert report["duplicate_event_ids"] >= 1
    assert report["invalid_rows"] >= 1
    assert {"year", "month", "month_label", "revenue", "occupancy_rate"}.issubset(clean.columns)
    assert clean["event_id"].is_unique
    assert clean["event_date"].notna().all()
    assert clean["tickets_sold"].between(0, clean["capacity"]).all()


def test_etl_rerun_does_not_duplicate_sqlite_rows(tmp_path):
    input_path = tmp_path / "events.csv"
    database_path = tmp_path / "events.db"
    clean_csv_path = tmp_path / "clean_events.csv"
    report_path = tmp_path / "quality.json"
    create_synthetic_events().to_csv(input_path, index=False)

    first_report = run_etl(input_path, database_path, clean_csv_path, report_path)
    second_report = run_etl(input_path, database_path, clean_csv_path, report_path)

    with sqlite3.connect(database_path) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert row_count == first_report["clean_rows"]
    assert second_report["database_rows"] == first_report["database_rows"]