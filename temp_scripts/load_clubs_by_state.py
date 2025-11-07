"""Load club and state reference data from data/reference/Clubs_By_State.xlsx."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


DATABASE = Path("malaysia_swimming.db")
WORKBOOK = Path("data/reference/Clubs_By_State.xlsx")

STATE_NAME_OVERRIDES = {
    "WPKL": "Wilayah Persekutuan Kuala Lumpur",
    "NSE": "Negeri Sembilan",
    "PNG": "Pulau Pinang",
    "PRK": "Perak",
    "SBH": "Sabah",
    "SWK": "Sarawak",
    "PHG": "Pahang",
    "TRG": "Terengganu",
    "KED": "Kedah",
    "JHR": "Johor",
    "KEL": "Kelantan",
    "MLK": "Melaka",
    "SEL": "Selangor",
    "PER": "Perlis",
    "HKG": "Hong Kong",
    "MGL": "Mongolia",
}

EXCLUDED_SHEETS = set()

SHEET_NATION = {
    "HKG": "HKG",
    "MGL": "MGL",
}


def load_workbook() -> list[pd.DataFrame]:
    xl = pd.ExcelFile(WORKBOOK)
    frames = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        if df.empty:
            continue
        df = df.rename(str.lower, axis="columns")
        if "state_code" not in df.columns:
            df["state_code"] = sheet
        if "club_code" not in df.columns:
            df["club_code"] = df.get("club_name", "").str.upper().str.replace(" ", "")
        frames.append(df)
    return frames


def build_states(df_list: list[pd.DataFrame]) -> pd.DataFrame:
    state_codes = sorted({df["state_code"].iloc[0] for df in df_list})
    data = []
    for code in state_codes:
        name = STATE_NAME_OVERRIDES.get(code, code)
        data.append({"code": code, "name": name})
    return pd.DataFrame(data)


def build_clubs(df_list: list[pd.DataFrame]) -> pd.DataFrame:
    clubs = []
    for df in df_list:
        state_code = str(df["state_code"].iloc[0]).strip()
        nation = SHEET_NATION.get(state_code, "MAS")
        if state_code in SHEET_NATION:
            state_code_value = None
        else:
            state_code_value = state_code
        for _, row in df.iterrows():
            club_name = str(row.get("club_name") or "").strip()
            if not club_name:
                continue
            raw_code = row.get("club_code")
            code_text = str(raw_code).strip().upper() if raw_code is not None and str(raw_code).strip().upper() != "NAN" else ""
            if not code_text:
                code_text = club_name.upper().replace(" ", "")
            clubs.append(
                {
                    "club_code": code_text,
                    "club_name": club_name,
                    "state_code": state_code_value,
                    "nation": nation,
                }
            )
    club_df = pd.DataFrame(clubs).drop_duplicates(subset=["club_code"])
    return club_df


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS states (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            nation TEXT DEFAULT 'MAS'
        );

        CREATE TABLE IF NOT EXISTS clubs (
            club_code TEXT PRIMARY KEY,
            club_name TEXT NOT NULL,
            state_code TEXT,
            nation TEXT DEFAULT 'MAS',
            FOREIGN KEY(state_code) REFERENCES states(code)
        );
        """
    )


def main() -> None:
    frames = load_workbook()
    if not frames:
        print("No club data detected in workbook")
        return

    states_df = build_states(frames)
    clubs_df = build_clubs(frames)

    conn = sqlite3.connect(DATABASE)
    ensure_tables(conn)

    conn.execute("DELETE FROM clubs")
    conn.execute("DELETE FROM states")

    states_df.to_sql("states", conn, if_exists="append", index=False)
    clubs_df.to_sql("clubs", conn, if_exists="append", index=False)

    conn.commit()
    conn.close()

    print(f"Loaded {len(states_df)} states and {len(clubs_df)} clubs.")


if __name__ == "__main__":
    main()
