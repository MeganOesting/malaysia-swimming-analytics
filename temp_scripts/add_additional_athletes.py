"""Append additional athletes based on IC-only records from consolidated workbook."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


WORKBOOK_PATH = Path(
    r"data/manual_matching/consolidated_athlete_ID.xlsx"
)
DATABASE_PATH = Path("malaysia_swimming.db")


def extract_birth_year(text: str) -> int | None:
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 4:
        return None
    year = digits[:4]
    if not year.isdigit():
        return None
    try:
        value = int(year)
    except ValueError:
        return None
    return value


def normalize_ic(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.endswith(".0") and text.replace(".0", "").isdigit():
        return text[:-2]
    return text


def main() -> int:
    df = pd.read_excel(WORKBOOK_PATH, dtype=str).fillna("")

    df["BIRTHDATE"] = df["BIRTHDATE"].str.strip()
    df["Birthday"] = df["Birthday"].str.strip()
    df["IC"] = df["IC"].str.strip()
    df["Unnamed: 7"] = df["Unnamed: 7"].str.strip()

    df["birth_year"] = df["Birthday"].apply(extract_birth_year)

    mask = (
        df["BIRTHDATE"].eq("")
        & df["IC"].ne("")
        & df["Birthday"].ne("")
        & df["Unnamed: 7"].eq("12")
        & df["birth_year"].notna()
        & (df["birth_year"] > 1990)
    )

    subset = df.loc[
        mask,
        [
            "FULLNAME",
            "BIRTHDATE",
            "Birthday",
            "FIRSTNAME",
            "LASTNAME",
            "MIDDLENAME",
            "SUFFIX",
            "IC",
        ],
    ].copy()

    if subset.empty:
        print("No additional athletes matched criteria.")
        return 0

    subset["BIRTHDATE"] = subset["Birthday"].where(subset["Birthday"].ne(""), subset["BIRTHDATE"])
    subset["IC"] = subset["IC"].apply(normalize_ic)
    subset["NATION"] = "MAS"

    conn = sqlite3.connect(DATABASE_PATH)

    existing = pd.read_sql_query("SELECT id FROM athletes", conn)
    if existing.empty:
        start_index = 0
    else:
        indices = (
            existing["id"].astype(str).str.extract(r"(\d+)$", expand=False).dropna()
        )
        if indices.empty:
            start_index = 0
        else:
            start_index = indices.astype(int).max() + 1

    subset = subset.reset_index(drop=True)
    subset.insert(0, "id", [f"athlete_{start_index + i}" for i in range(len(subset))])

    subset = subset[[
        "id",
        "FULLNAME",
        "BIRTHDATE",
        "FIRSTNAME",
        "LASTNAME",
        "MIDDLENAME",
        "SUFFIX",
        "IC",
        "NATION",
    ]]

    subset.to_sql("athletes", conn, if_exists="append", index=False)

    conn.close()

    print(f"Appended {len(subset)} additional athletes.")
    return len(subset)


if __name__ == "__main__":
    main()


