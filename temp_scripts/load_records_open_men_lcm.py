"""Load national men’s open LCM records into the records table."""

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
    RecordRow("50m Freestyle", "22.91", "LEONG Bryan", "27 May 2023", "AP Race London International", "London, United Kingdom"),
    RecordRow("100m Freestyle", "49.54", "SIM Welson", "26 April 2019", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("200m Freestyle", "1:47.36", "SIM Welson", "24 August 2017", "Southeast Asian Games", "Kuala Lumpur, Malaysia"),
    RecordRow("400m Freestyle", "3:48.36", "KNIEW How Yean", "17 April 2024", "Australian Championships", "Gold Coast, Australia"),
    RecordRow("800m Freestyle", "8:01.30", "KNIEW How Yean", "19 April 2024", "Australian Championships", "Gold Coast, Australia"),
    RecordRow("1500m Freestyle", "15:21.92", "KNIEW How Yean", "10 December 2023", "Queensland Championships", "Brisbane, Australia"),
    RecordRow("50m Backstroke", "25.60", "TERN Jian Han", "7 April 2018", "Commonwealth Games", "Gold Coast, Australia"),
    RecordRow("100m Backstroke", "54.77", "LIM Alex", "21 July 2003", "World Championships", "Barcelona, Spain"),
    RecordRow("200m Backstroke", "2:00.80", "KNIEW How Yean", "12 June 2021", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("50m Breaststroke", "27.40", "GOH Andrew", "20 August 2024", "SUKMA", "Sarawak, Malaysia"),
    RecordRow("100m Breaststroke", "1:01.39", "GOH Andrew", "19 August 2024", "SUKMA", "Sarawak, Malaysia"),
    RecordRow("200m Breaststroke", "2:15.62", "CHIA Elvin", "11 August 1999", "Southeast Asian Games", "Bandar Seri Begawan, Brunei"),
    RecordRow("50m Butterfly", "24.08", "LEONG Bryan", "27 May 2024", "AP Race London International", "London, United Kingdom"),
    RecordRow("100m Butterfly", "52.78", "LEONG Bryan", "16 February 2024", "World Championships", "Doha, Qatar"),
    RecordRow("200m Butterfly", "1:58.99", "BEGO Daniel", "28 July 2009", "World Championships", "Rome, Italy"),
    RecordRow("200m Individual Medley", "2:03.77", "KNIEW How Yean", "12 March 2023", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("400m Individual Medley", "4:23.24", "TAN Khai Xin", "8 May 2023", "Southeast Asian Games", "Phnom Penh, Cambodia"),
)

RELAY_RECORDS = (
    (
        "LCM_Relay_4_100_Free_M",
        "3:20.61",
        [
            "LIM Yin Chuen",
            "CHAHAL Arvin Shuan Singh",
            "KNIEW How Yean",
            "NG Shin Jian",
        ],
        "10 May 2023",
        "Southeast Asian Games",
        "Phnom Penh, Cambodia",
    ),
    (
        "LCM_Relay_4_200_Free_M",
        "7:19.75",
        [
            "SIM Welson",
            "LIM Yin Chuen",
            "CHAHAL Arvin Shuan Singh",
            "KNIEW How Yean",
        ],
        "17 May 2022",
        "Southeast Asian Games",
        "Hanoi, Vietnam",
    ),
    (
        "LCM_Relay_4_100_Medley_M",
        "3:42.12",
        [
            "KNIEW How Yean",
            "GOH Andrew",
            "LEONG Bryan",
            "CHAHAL Arvin Shuan Singh",
        ],
        "8 May 2023",
        "Southeast Asian Games",
        "Phnom Penh, Cambodia",
    ),
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
    return f"LCM_{stroke}_{distance}_M"


def main() -> int:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM records WHERE category_type = 'open' AND category_value = 'M-LCM-N-I'"
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
        record_id = f"record_open_men_LCM_{stroke_label}_{distance}"

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
            ) VALUES (?, ?, 'open', 'M-LCM-N-I', NULL, NULL, ?, ?, ?, ?, NULL, ?, 0, 'national', 'MAS', 'open')
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
    existing_relay_ids = {
        row[0]
        for row in conn.execute(
            "SELECT id FROM records WHERE category_type='open' AND category_value='M-LCM-N-R'"
        )
    }

    for event_id, time_text, members, date_text, competition, location in RELAY_RECORDS:
        if event_id in existing_relay_ids:
            continue

        record_time_seconds = parse_time_to_seconds(time_text)
        record_time_string = time_text
        record_date = parse_date(date_text)

        athlete_ids = [ensure_athlete(conn, name) for name in members]
        primary_athlete = athlete_ids[0]
        lineup = "; ".join(
            f"{name} ({aid})" for name, aid in zip(members, athlete_ids)
        )

        notes = (
            f"Competition: {competition}; Location: {location}; Lineup: {lineup}"
        )
        record_id = f"record_open_men_LCM_relay_{event_id.split('_', 2)[2]}"

        conn.execute(
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
            ) VALUES (?, ?, 'open', 'M-LCM-N-R', NULL, NULL, ?, ?, ?, ?, NULL, ?, 1, 'national', 'MAS', 'open')
            """,
            (
                record_id,
                event_id,
                record_time_seconds,
                record_time_string,
                record_date,
                primary_athlete,
                notes,
            ),
        )

    conn.commit()
    conn.close()

    print(f"Inserted {rows_inserted} open men LCM records.")
    return rows_inserted


if __name__ == "__main__":
    main()
