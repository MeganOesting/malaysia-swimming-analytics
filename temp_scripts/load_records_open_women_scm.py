"""Load national women’s open SCM records into the records table."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DATABASE = Path("malaysia_swimming.db")


@dataclass(frozen=True)
class RecordRow:
    event_label: str
    time_text: str
    athlete_name: str
    record_date_text: str
    competition: str
    location: str


RECORDS = (
    RecordRow("50m Freestyle", "25.58", "CHUI Lai Kwan", "31 October 2024", "World Cup Singapore", "Singapore"),
    RecordRow("100m Freestyle", "56.99", "KHEW Zi Xian", "5 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("200m Freestyle", "2:03.83", "KHOO Cai Lin", "5 November 2013", "World Cup", "Singapore, Singapore"),
    RecordRow("400m Freestyle", "4:19.65", "KHOO Cai Lin", "6 November 2013", "World Cup", "Singapore, Singapore"),
    RecordRow("800m Freestyle", "8:42.73", "KHOO Cai Lin", "5 November 2013", "World Cup", "Singapore, Singapore"),
    # 1500m freestyle intentionally left blank per instructions.
    RecordRow("50m Backstroke", "27.56", "CHONG Xin Lin", "4 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("100m Backstroke", "1:00.45", "CHONG Xin Lin", "19 October 2024", "World Cup Shanghai", "Shangahi, China"),
    RecordRow("200m Backstroke", "2:13.61", "CHONG Xin Lin", "7 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("50m Breaststroke", "31.06", "PHEE Pinq En", "20 October 2024", "World Cup Shanghai", "Shangahi, China"),
    RecordRow("100m Breaststroke", "1:06.86", "PHEE Pinq En", "5 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("200m Breaststroke", "2:27.38", "PHEE Pinq En", "4 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("50m Butterfly", "27.35", "HO Megan", "4 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("100m Butterfly", "1:01.31", "YAP Siew Hui", "5 November 2013", "World Cup", "Singapore, Singapore"),
    RecordRow("200m Butterfly", "2:16.71", "YAP Siew Hui", "5 November 2013", "World Cup", "Singapore, Singapore"),
    RecordRow("100m Individual Medley", "1:02.77", "CHONG Xin Lin", "7 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("200m Individual Medley", "2:16.67", "TAN Rouxin", "4 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("400m Individual Medley", "4:54.48", "TAN Rouxin", "6 July 2024", "Malaysia SCM Championships", "Kuala Lumpur, Malaysia"),
)


EVENT_MAP = {
    "Freestyle": "Free",
    "Backstroke": "Back",
    "Breaststroke": "Breast",
    "Butterfly": "Fly",
    "Individual Medley": "IM",
}


def normalize_name(value: str) -> str:
    return "".join(ch for ch in value.upper() if ch.isalpha())


def parse_time_to_seconds(time_text: str) -> float:
    parts = time_text.split(":")
    if len(parts) == 1:
        return float(parts[0])
    minutes = int(parts[0])
    seconds = float(parts[1])
    return minutes * 60 + seconds


def parse_date(text: str) -> str:
    dt = pd.to_datetime(text, dayfirst=False)
    return dt.strftime("%Y.%m.%d")


def ensure_athlete(conn: sqlite3.Connection, name: str) -> str:
    df = pd.read_sql_query("SELECT id, FULLNAME, NATION FROM athletes", conn)
    normalized_map = {
        normalize_name(row["FULLNAME"]): (row["id"], (row["NATION"] or "").strip().upper())
        for _, row in df.iterrows()
    }

    norm = normalize_name(name)
    if norm in normalized_map:
        athlete_id, nation = normalized_map[norm]
        if not nation:
            conn.execute("UPDATE athletes SET NATION = 'MAS' WHERE id = ?", (athlete_id,))
            nation = "MAS"
        if nation != "MAS":
            raise ValueError(
                f"Athlete {name} has NATION={nation}, cannot assign national/state record."
            )
        return athlete_id

    next_index = 0
    if not df.empty:
        ids = (
            df["id"].astype(str).str.extract(r"(\d+)$", expand=False).dropna().astype(int)
        )
        next_index = ids.max() + 1

    new_id = f"athlete_{next_index}"
    conn.execute(
        "INSERT INTO athletes (id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLENAME, SUFFIX, IC, NATION) VALUES (?, ?, '', '', '', '', '', '', 'MAS')",
        (new_id, name.strip()),
    )
    return new_id


def event_identifier(distance: int, stroke: str) -> str:
    return f"SCM_{stroke}_{distance}_F"


def main() -> int:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM records WHERE category_type = 'open' AND category_value = 'women_SCM'"
    )

    rows_inserted = 0

    for record in RECORDS:
        if not record.time_text.strip():
            continue

        distance_part, label = record.event_label.split("m ", 1)
        distance = int(distance_part)
        stroke_label = EVENT_MAP[label]

        event_id = event_identifier(distance, stroke_label)
        record_time_seconds = parse_time_to_seconds(record.time_text)
        record_time_string = record.time_text
        record_date = parse_date(record.record_date_text)
        athlete_id = ensure_athlete(conn, record.athlete_name)

        notes = f"Competition: {record.competition}; Location: {record.location}"
        record_id = f"record_open_women_SCM_{stroke_label}_{distance}"

        cursor.execute(
            """
            INSERT INTO records (
                id,
                event_id,
                category_type,
                category_value,
                min_day_age,
                max_day_age,
                record_time_seconds,
                record_time_string,
                record_date,
                athlete_id,
                meet_id,
                notes,
                is_relay,
                team_entity,
                team_name,
                age_basis
            ) VALUES (?, ?, 'open', 'F-SCM-N-I', NULL, NULL, ?, ?, ?, ?, NULL, ?, 0, NULL, NULL, 'open')
            """,
            (
                record_id,
                event_id,
                record_time_seconds,
                record_time_string,
                record_date,
                athlete_id,
                notes,
            ),
        )

        rows_inserted += 1

    conn.commit()
    conn.close()

    print(f"Inserted {rows_inserted} open women SCM records.")
    return rows_inserted


if __name__ == "__main__":
    main()

