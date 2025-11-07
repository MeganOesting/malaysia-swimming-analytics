"""Inspect missing athlete aliases for a meet file."""

from collections import Counter
from pathlib import Path
import sqlite3

import pandas as pd

from scripts.convert_meets_to_sqlite_simple import (
    ConversionValidationError,
    process_meet_file_simple,
)


def analyze_missing_aliases(meet_file: Path) -> None:
    meet_info = {
        "id": "temporary",
        "name": meet_file.stem,
        "meet_date": "2024-01-01",
        "location": "Unknown",
    }

    try:
        process_meet_file_simple(meet_file, meet_info)
        print("Meet processed successfully; no missing aliases detected.")
        return
    except ConversionValidationError as exc:
        missing = exc.details.get("missing_athletes", [])
        nation_mismatches = exc.details.get("nation_mismatches", [])

    print(f"Missing athletes reported: {len(missing)}")
    if nation_mismatches:
        print(f"Nation mismatches reported: {len(nation_mismatches)}")

    counter = Counter()
    for entry in missing:
        counter[entry["full_name"]] += 1

    print("\nTop missing names:")
    for name, count in counter.most_common(25):
        print(f"  {name}: {count} occurrences")

    conn = sqlite3.connect("malaysia_swimming.db")
    try:
        alias_df = pd.read_sql_query(
            "SELECT alias_fullname, athlete_id FROM athlete_aliases", conn
        )
    finally:
        conn.close()

    alias_set = {name.lower(): athlete_id for name, athlete_id in alias_df.values}

    missing_aliases = sorted(
        name for name in counter if name.lower() not in alias_set
    )
    if missing_aliases:
        output_file = Path("temp_scripts/missing_aliases.txt")
        output_file.write_text("\n".join(missing_aliases), encoding="utf-8")
        print(
            f"\nNames not present in alias table: {len(missing_aliases)}"
            f" (written to {output_file})"
        )
    else:
        print("\nAll missing names already exist in alias table.")


if __name__ == "__main__":
    meet_path = Path("meets/active/2024-25/SUKMA_2024_Men.xls")
    if not meet_path.exists():
        raise SystemExit(f"Meet file not found: {meet_path}")
    analyze_missing_aliases(meet_path)

