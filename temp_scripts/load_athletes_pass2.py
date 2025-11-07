"""Second pass athlete loader for IC-only records matching criteria."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


WORKBOOK = Path(
    r"data/manual_matching/consolidated_athlete_ID.xlsx"
)
DATABASE = Path("malaysia_swimming.db")


def extract_year(text: str) -> int | None:
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 4:
        return None
    year = digits[:4]
    if not year.isdigit():
        return None
    try:
        return int(year)
    except ValueError:
        return None


def normalize_ic(raw: str) -> str:
    text = raw.strip()
    if text.endswith(".0") and text.replace(".0", "").isdigit():
        return text[:-2]
    return text


def main() -> int:
    df = pd.read_excel(WORKBOOK, dtype=str).fillna("")

    df["BIRTHDATE"] = df["BIRTHDATE"].str.strip()
    df["Birthday"] = df["Birthday"].str.strip()
    df["IC"] = df["IC"].astype(str).str.strip()
    df["Unnamed: 7"] = df["Unnamed: 7"].str.strip()

    df["birth_year"] = df["Birthday"].apply(extract_year)

    mask = (
        df["BIRTHDATE"].eq("")
        & df["Birthday"].ne("")
        & df["Unnamed: 7"].eq("12")
        & df["birth_year"].notna()
        & (df["birth_year"].between(1990, 2020, inclusive="both"))
    )

    subset = df.loc[
        mask,
        [
            "FULLNAME",
            "BIRTHDATE",
            "Birthday",
            "IC",
            "FIRSTNAME",
            "LASTNAME",
            "MIDDLENAME",
            "SUFFIX",
        ],
    ].copy()

    if subset.empty:
        print("No additional athletes matched pass 2 criteria.")
        return 0

    subset["BIRTHDATE"] = subset["Birthday"]
    subset["IC"] = subset["IC"].apply(normalize_ic)
    subset["FIRSTNAME"] = subset["FIRSTNAME"].str.strip()
    subset["LASTNAME"] = subset["LASTNAME"].str.strip()
    subset["MIDDLENAME"] = subset["MIDDLENAME"].str.strip()
    subset["SUFFIX"] = subset["SUFFIX"].str.strip()
    subset["FULLNAME"] = (
        subset["LASTNAME"].str.strip()
        + ", "
        + subset["FIRSTNAME"].str.strip()
        + subset["MIDDLENAME"].apply(lambda x: f" {x}" if x else "")
        + subset["SUFFIX"].apply(lambda x: f" {x}" if x else "")
    ).str.strip()
    subset["NATION"] = "MAS"

    subset = subset.drop(columns=["Birthday"])
    subset = subset.reset_index(drop=True)

    conn = sqlite3.connect(DATABASE)

    existing = pd.read_sql_query("SELECT id, FULLNAME, BIRTHDATE FROM athletes", conn)
    existing_keys = set(
        (row["FULLNAME"], row["BIRTHDATE"]) for _, row in existing.iterrows()
    )

    if existing.empty:
        start_index = 0
    else:
        numeric_parts = (
            existing["id"].astype(str).str.extract(r"(\d+)$", expand=False).dropna()
        )
        start_index = numeric_parts.astype(int).max() + 1 if not numeric_parts.empty else 0

    filtered_rows = []
    for _, row in subset.iterrows():
        key = (row["FULLNAME"], row["BIRTHDATE"])
        if key in existing_keys:
            continue
        filtered_rows.append(row)

    if not filtered_rows:
        conn.close()
        print("No new athletes to append in pass 2 (all duplicates).")
        return 0

    final_df = pd.DataFrame(filtered_rows)
    final_df.insert(0, "id", [f"athlete_{start_index + i}" for i in range(len(final_df))])

    final_df = final_df[[
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

    final_df.to_sql("athletes", conn, if_exists="append", index=False)
    conn.close()

    print(f"Appended {len(final_df)} athletes via pass 2.")
    return len(final_df)


if __name__ == "__main__":
    main()

