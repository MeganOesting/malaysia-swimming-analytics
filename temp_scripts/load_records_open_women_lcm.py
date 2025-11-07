"""Load national women’s open LCM records into the records table."""

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
    RecordRow("50m Freestyle", "25.82", "CHUI Lai Kwan", "11 June 2015", "Southeast Asian Games", "Singapore"),
    RecordRow("100m Freestyle", "57.56", "LOO Yie Bing", "4 June 2022", "Malaysian Age Group Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("200m Freestyle", "2:03.22", "KHOO Cai Lin", "17 May 2013", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("400m Freestyle", "4:10.75", "KHOO Cai Lin", "11 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("800m Freestyle", "8:45.36", "KHOO Cai Lin", "12 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("1500m Freestyle", "17:07.64", "GOH Chia Tong", "18 May 2022", "Southeast Asian Games", "Hanoi, Vietnam"),
    RecordRow("50m Backstroke", "29.32", "CHONG Xin Ling", "13 June 2024", "Singapore National Championships", "Singapore"),
    RecordRow("100m Backstroke", "1:03.91", "CHUI Lai Kwan", "12 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("200m Backstroke", "2:17.39", "LEW Yih Wey", "7 December 2007", "Southeast Asian Games", "Nakhon Ratchasima, Thailand"),
    RecordRow("50m Breaststroke", "31.40", "PHEE Jing En", "6 December 2019", "Southeast Asian Games", "New Clark City, Philippines"),
    RecordRow("100m Breaststroke", "1:08.40", "PHEE Jing En", "25 July 2021", "Olympic Games", "Tokyo, Japan"),
    RecordRow("200m Breaststroke", "2:27.80", "SIOW Yi Ting", "13 August 2008", "Olympic Games", "Bejing, China"),
    RecordRow("50m Butterfly", "27.45", "LIEW Marellyn", "3 May 2008", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
    RecordRow("100m Butterfly", "1:01.04", "LIEW Marellyn", "12 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("200m Butterfly", "2:14.30", "KHOO Cai Lin", "10 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("200m Individual Medley", "2:14.57", "SIOW Yi Ting", "10 December 2009", "Southeast Asian Games", "Vientiane, Laos"),
    RecordRow("400m Individual Medley", "4:50.52", "LEW Yih Wey", "11 December 2009", "Malaysia Open Championships", "Kuala Lumpur, Malaysia"),
)


RELAY_RECORDS = (
    (
        "LCM_Relay_4_100_Free_F",
        "3:51.40",
        [
            "LEUNG Chii Lin",
            "CHUI Lai Kwan",
            "SIOW Yi Ting",
            "KHOO Cai Lin",
        ],
        "11 December 2009",
        "Southeast Asian Games",
        "Vientiane, Laos",
    ),
    (
        "LCM_Relay_4_200_Free_F",
        "8:27.13",
        [
            "KHOO Cai Lin",
            "GAN Heidi",
            "LEW Yih Wey",
            "ONG Ming Xiu",
        ],
        "7 December 2007",
        "Southeast Asian Games",
        "Nakhon Ratchasima, Thailand",
    ),
    (
        "LCM_Relay_4_100_Medley_F",
        "4:13.18",
        [
            "CHUI Lai Kwan",
            "SIOW Yi Ting",
            "LIEW Marellyn",
            "KHOO Cai Lin",
        ],
        "13 December 2009",
        "Southeast Asian Games",
        "Vientiane, Laos",
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
    return f"LCM_{stroke}_{distance}_F"


def main() -> int:
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM records WHERE category_type = 'open' AND category_value = 'F-LCM-N-I'"
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
        record_id = f"record_open_women_LCM_{stroke_label}_{distance}"

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
            ) VALUES (?, ?, 'open', 'F-LCM-N-I', NULL, NULL, ?, ?, ?, ?, NULL, ?, 0, 'national', 'MAS', 'open')
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
            "SELECT id FROM records WHERE category_type='open' AND category_value='F-LCM-N-R'"
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
        record_id = f"record_open_women_LCM_relay_{event_id.split('_', 2)[2]}"

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
            ) VALUES (?, ?, 'open', 'F-LCM-N-R', NULL, NULL, ?, ?, ?, ?, NULL, ?, 1, 'national', 'MAS', 'open')
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

    print(f"Inserted {rows_inserted} open women LCM records.")
    return rows_inserted


if __name__ == "__main__":
    main()
