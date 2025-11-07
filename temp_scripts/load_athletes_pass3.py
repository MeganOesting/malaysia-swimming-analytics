"""Third pass athlete loader: MATCH flag but column H != 12."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


WORKBOOK = Path(
    r"data/manual_matching/consolidated_athlete_ID.xlsx"
)
DATABASE = Path("malaysia_swimming.db")


def build_fullname(last: str, first: str, middle: str, suffix: str) -> str:
    parts = [
        last.strip(),
        ", ",
        first.strip(),
    ]
    if middle.strip():
        parts.append(f" {middle.strip()}")
    if suffix.strip():
        parts.append(f" {suffix.strip()}")
    return "".join(parts).strip()


def main() -> int:
    df = pd.read_excel(WORKBOOK, dtype=str).fillna("")

    df["Unnamed: 5"] = df["Unnamed: 5"].str.strip()
    df["Unnamed: 7"] = df["Unnamed: 7"].str.strip()
    df["BIRTHDATE"] = df["BIRTHDATE"].str.strip()
    df["Birthday"] = df["Birthday"].str.strip()

    mask = (
        df["Unnamed: 5"].eq("MATCH")
        & df["Unnamed: 7"].ne("12")
        & df["BIRTHDATE"].ne("")
        & df["BIRTHDATE"].eq(df["Birthday"])
    )

    subset = df.loc[
        mask,
        [
            "FULLNAME",
            "BIRTHDATE",
            "FIRSTNAME",
            "LASTNAME",
            "MIDDLENAME",
            "SUFFIX",
        ],
    ].copy()

    subset["FIRSTNAME"] = subset["FIRSTNAME"].str.strip()
    subset["LASTNAME"] = subset["LASTNAME"].str.strip()
    subset["MIDDLENAME"] = subset["MIDDLENAME"].str.strip()
    subset["SUFFIX"] = subset["SUFFIX"].str.strip()

    subset["CALCED_FULLNAME"] = subset.apply(
        lambda row: build_fullname(
            row["LASTNAME"],
            row["FIRSTNAME"],
            row["MIDDLENAME"],
            row["SUFFIX"],
        ),
        axis=1,
    )

    subset["FINAL_FULLNAME"] = subset["CALCED_FULLNAME"].where(
        subset["CALCED_FULLNAME"].ne(""), subset["FULLNAME"].str.strip()
    )

    subset = subset.drop(columns=["FULLNAME", "CALCED_FULLNAME"])
    subset.rename(columns={"FINAL_FULLNAME": "FULLNAME"}, inplace=True)

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
        print("No pass 3 athletes to append (all duplicates).")
        return 0

    final_df = pd.DataFrame(filtered_rows)
    final_df.insert(0, "id", [f"athlete_{start_index + i}" for i in range(len(final_df))])
    final_df["NATION"] = "MAS"
    final_df["IC"] = ""

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

    print(f"Appended {len(final_df)} athletes via pass 3.")
    return len(final_df)


if __name__ == "__main__":
    main()


