"""Create a reproducible, explicitly synthetic concert and event CSV."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw" / "events.csv"


def create_synthetic_events(valid_event_count: int = 360, seed: int = 42) -> pd.DataFrame:
    """Return valid fictional events plus deliberate quality-check examples."""
    if valid_event_count < 1:
        raise ValueError("valid_event_count must be at least 1")

    randomizer = random.Random(seed)
    cities = ["Seattle", "Austin", "Chicago", "Denver", "Nashville", "Boston"]
    genres = ["Rock", "Pop", "Jazz", "Electronic", "Country", "Comedy"]
    venues = ["Cedar Hall", "Riverside Arena", "Northstar Theater", "Juniper Pavilion"]
    start = pd.Timestamp("2024-01-01")
    rows: list[dict[str, object]] = []

    for index in range(valid_event_count):
        event_date = start + pd.Timedelta(days=randomizer.randrange(730))
        capacity = randomizer.randrange(250, 20001, 50)
        tickets_sold = randomizer.randrange(0, capacity + 1)
        rows.append(
            {
                "event_id": f"EVT-{index + 1:04d}",
                "event_name": f"{randomizer.choice(['Live', 'After Hours', 'Summer', 'City'])} "
                f"{randomizer.choice(['Sessions', 'Showcase', 'Festival', 'Night'])} {index + 1}",
                "event_date": event_date.strftime("%Y-%m-%d"),
                "city": randomizer.choice(cities),
                "venue": randomizer.choice(venues),
                "genre": randomizer.choice(genres),
                "capacity": capacity,
                "tickets_sold": tickets_sold,
                "ticket_price": round(randomizer.uniform(15, 180), 2),
                "data_source": "SYNTHETIC - GENERATED FOR EDUCATION",
            }
        )

    frame = pd.DataFrame(rows)
    frame = frame.sample(frac=1, random_state=seed).reset_index(drop=True)
    examples = [
        frame.iloc[[0]].copy(),  # exact duplicate
        frame.iloc[[1]].copy(),  # duplicate event ID with changed content
        frame.iloc[[2]].assign(event_id="QC-MISSING-CITY", city=pd.NA),
        frame.iloc[[3]].assign(event_id="QC-INVALID-DATE", event_date="not-a-date"),
        frame.iloc[[4]].assign(event_id="QC-INVALID-TICKETS", tickets_sold=-10),
        frame.iloc[[5]].assign(event_id="QC-INVALID-CAPACITY", capacity=0),
        frame.iloc[[6]].assign(event_id="QC-MISSING-VENUE", venue=pd.NA),
    ]
    examples[1].loc[:, "event_name"] = "Conflicting duplicate example"
    return pd.concat([frame, *examples], ignore_index=True)


def generate_csv(output_path: Path = DEFAULT_OUTPUT, valid_event_count: int = 360) -> Path:
    """Write the synthetic records to CSV and return the destination path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    create_synthetic_events(valid_event_count).to_csv(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=360, help="Number of valid events")
    args = parser.parse_args()
    path = generate_csv(args.output, args.count)
    print(f"Generated synthetic data: {path}")


if __name__ == "__main__":
    main()