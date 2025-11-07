"""First pass athlete loader: MATCH flag + column H == 12."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


WORKBOOK = Path(
    r"data/manual_matching/consolidated_athlete_ID.xlsx"
)
DATABASE = Path("malaysia_swimming.db")


def normalize_ic(raw: str) -> str:
    text = raw.strip()
    if text.endswith(".0") and text.replace(".0", "").isdigit():
        return text[:-2]
    return text


def main() -> int:
    df = pd.read_excel(WORKBOOK, dtype=str).fillna("")

    mask = (df["Unnamed: 5"].str.strip() == "MATCH") & (df["Unnamed: 7"].str.strip() == "12")

    subset = df.loc[mask, ["FULLNAME", "BIRTHDATE", "IC", "FIRSTNAME", "LASTNAME", "MIDDLENAME", "SUFFIX", "Unnamed: 8"]].copy()

    subset["FULLNAME"] = subset["FULLNAME"].str.strip()
    subset["BIRTHDATE"] = subset["BIRTHDATE"].str.strip()
    subset["IC"] = subset["IC"].apply(normalize_ic)
    subset["NATION"] = subset["Unnamed: 8"].str.strip()

    subset = subset.drop(columns=["Unnamed: 8"])
    subset = subset.reset_index(drop=True)

    subset.insert(0, "id", [f"athlete_{i}" for i in range(len(subset))])

    cols = [
        "id",
        "FULLNAME",
        "BIRTHDATE",
        "FIRSTNAME",
        "LASTNAME",
        "MIDDLENAME",
        "SUFFIX",
        "IC",
        "NATION",
    ]

    conn = sqlite3.connect(DATABASE)
    subset[cols].to_sql("athletes", conn, if_exists="append", index=False)
    conn.close()

    print(f"Loaded {len(subset)} athletes from MATCH + col H == 12 filter.")
    return len(subset)


if __name__ == "__main__":
    main()


