"""Reset and populate the events table with all course/stroke/gender combinations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


DATABASE = Path("malaysia_swimming.db")


COURSES = ("LCM", "SCM")
GENDERS = ("M", "F")

INDIVIDUAL_STROKES = {
    "Free": (50, 100, 200, 400, 800, 1500),
    "Back": (50, 100, 200),
    "Breast": (50, 100, 200),
    "Fly": (50, 100, 200),
}


def get_distances(course: str, stroke: str) -> tuple[int, ...]:
    if stroke == "IM":
        return (100, 200, 400) if course == "SCM" else (200, 400)
    if stroke == "Relay":
        raise ValueError("Relay stroke is handled separately")
    return INDIVIDUAL_STROKES[stroke]


def build_event_rows() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []

    for course in COURSES:
        for gender in GENDERS:
            for stroke in ("Free", "Back", "Breast", "Fly", "IM"):
                distances = get_distances(course, stroke)
                for distance in distances:
                    identifier = f"{course}_{stroke}_{distance}_{gender}"
                    rows.append(
                        {
                            "id": identifier,
                            "distance": int(distance),
                            "stroke": stroke,
                            "gender": gender,
                            "course": course,
                        }
                    )

    for course in COURSES:
        for gender in ("M", "F"):
            for distance, stroke in ((4, "200_Free"), (4, "100_Free"), (4, "100_Medley")):
                identifier = f"{course}_Relay_{distance}_{stroke}_{gender}"
                rows.append(
                    {
                        "id": identifier,
                        "distance": distance,
                        "stroke": stroke,
                        "gender": gender,
                        "course": course,
                    }
                )

        for distance, stroke in ((4, "100_Free"), (4, "100_Medley")):
            identifier = f"{course}_Relay_{distance}_{stroke}_X"
            rows.append(
                {
                    "id": identifier,
                    "distance": distance,
                    "stroke": stroke,
                    "gender": "X",
                    "course": course,
                }
            )

    return rows


def main() -> int:
    rows = build_event_rows()
    df = pd.DataFrame(rows)

    conn = sqlite3.connect(DATABASE)
    conn.executescript(
        """
        DROP TABLE IF EXISTS events;
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            distance INTEGER NOT NULL,
            stroke TEXT NOT NULL,
            gender TEXT NOT NULL,
            course TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    df.to_sql("events", conn, if_exists="append", index=False)
    conn.close()

    print(f"Populated events table with {len(df)} rows.")
    return len(df)


if __name__ == "__main__":
    main()

