"""Merge registration and results workbooks into a unified athlete dataset."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


ROOT = Path(".")

REGISTRATION_PATH = ROOT / "data" / "manual_matching" / "consolidated_registration_subset.xlsx"
RESULTS_PATH = ROOT / "data" / "manual_matching" / "consolidated_results_athlete_birthdat_fullname.xlsx"
OUTPUT_PATH = ROOT / "data" / "manual_matching" / "consolidated_athlete_ID_rebuilt.xlsx"


def clean_birthdate(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace("/", ".").replace("-", ".")


def normalize_ic(value: str) -> tuple[str, int]:
    text = str(value or "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    digits_only = re.sub(r"\D", "", text)
    return digits_only, len(digits_only)


def build_fullname(last: str, first: str, middle: str = "", suffix: str = "") -> str:
    parts = [str(last or "").strip(), ", ", str(first or "").strip()]
    middle = str(middle or "").strip()
    suffix = str(suffix or "").strip()
    if middle:
        parts.append(f" {middle}")
    if suffix:
        parts.append(f" {suffix}")
    return "".join(parts).strip()


def load_registration() -> pd.DataFrame:
    df = pd.read_excel(REGISTRATION_PATH, dtype=str).fillna("")
    df.columns = [col.strip() for col in df.columns]

    df["FULLNAME"] = df.apply(
        lambda row: build_fullname(
            row.get("LASTNAME", ""),
            row.get("FIRSTNAME", ""),
            row.get("MIDDLENAME", ""),
            row.get("SUFFIX", ""),
        ),
        axis=1,
    )

    df["BIRTHDATE"] = df["Birthday"].apply(clean_birthdate)
    df.rename(columns={"Birthday": "Birthday_raw"}, inplace=True)

    ic_series = (
        df["IC"].astype(str)
        if "IC" in df.columns
        else pd.Series(["" for _ in range(len(df))], index=df.index)
    )
    df["IC_NORMALIZED"], df["IC_DIGIT_COUNT"] = zip(*ic_series.apply(normalize_ic))

    df["SOURCE_FILE"] = "registration_subset"
    return df


def load_results() -> pd.DataFrame:
    df = pd.read_excel(RESULTS_PATH, dtype=str).fillna("")
    df.columns = [col.strip() for col in df.columns]

    if "BIRTHDATE" not in df.columns:
        raise ValueError("Results workbook missing BIRTHDATE column")

    df["BIRTHDATE"] = df["BIRTHDATE"].apply(clean_birthdate)
    if "Birthday" in df.columns:
        df["Birthday_raw"] = df["Birthday"].apply(clean_birthdate)
    else:
        df["Birthday_raw"] = ""

    ic_series = (
        df["IC"].astype(str)
        if "IC" in df.columns
        else pd.Series(["" for _ in range(len(df))], index=df.index)
    )
    df["IC_NORMALIZED"], df["IC_DIGIT_COUNT"] = zip(*ic_series.apply(normalize_ic))

    for col in ["FIRSTNAME", "LASTNAME", "MIDDLENAME", "SUFFIX"]:
        if col not in df.columns:
            df[col] = ""

    if "FULLNAME" not in df.columns or df["FULLNAME"].str.strip().eq("").all():
        df["FULLNAME"] = df.apply(
            lambda row: build_fullname(
                row.get("LASTNAME", ""),
                row.get("FIRSTNAME", ""),
                row.get("MIDDLENAME", ""),
                row.get("SUFFIX", ""),
            ),
            axis=1,
        )

    df["SOURCE_FILE"] = df.get("SOURCE_FILE", "results")
    df["SOURCE_SHEET"] = df.get("SOURCE_SHEET", "")
    return df


def merge_datasets(reg_df: pd.DataFrame, res_df: pd.DataFrame) -> pd.DataFrame:
    full_df = pd.concat([reg_df, res_df], ignore_index=True, sort=False)

    for col in ["FULLNAME", "FIRSTNAME", "LASTNAME", "MIDDLENAME", "SUFFIX"]:
        full_df[col] = full_df[col].astype(str).str.strip()

    full_df["BIRTHDATE"] = full_df["BIRTHDATE"].apply(clean_birthdate)
    full_df["Birthday_raw"] = full_df["Birthday_raw"].apply(clean_birthdate)

    # If BIRTHDATE is missing but a Birthday_raw value exists, use that value.
    full_df.loc[full_df["BIRTHDATE"].eq(""), "BIRTHDATE"] = full_df.loc[
        full_df["BIRTHDATE"].eq(""), "Birthday_raw"
    ]

    full_df["BIRTHDATE_MATCH"] = (
        (full_df["BIRTHDATE"].ne(""))
        & (full_df["Birthday_raw"].ne(""))
        & (full_df["BIRTHDATE"] == full_df["Birthday_raw"])
    ).astype(int)

    full_df["KEY"] = (
        full_df["FULLNAME"].str.lower().str.replace(" ", "", regex=False)
        + "|"
        + full_df["BIRTHDATE"].str.replace(" ", "", regex=False)
    )

    deduped = (
        full_df.sort_values(
            by=["BIRTHDATE_MATCH", "IC_DIGIT_COUNT", "SOURCE_FILE"],
            ascending=[False, False, True],
        )
        .drop_duplicates(subset=["KEY"], keep="first")
        .drop(columns=["KEY"])
        .reset_index(drop=True)
    )

    return deduped


def main() -> None:
    if not REGISTRATION_PATH.exists():
        raise SystemExit(f"Registration file not found: {REGISTRATION_PATH}")
    if not RESULTS_PATH.exists():
        raise SystemExit(f"Results file not found: {RESULTS_PATH}")

    reg_df = load_registration()
    res_df = load_results()

    merged = merge_datasets(reg_df, res_df)

    merged.to_excel(OUTPUT_PATH, index=False)
    print(f"Wrote consolidated dataset to {OUTPUT_PATH}")
    print(f"Total rows: {len(merged)}")


if __name__ == "__main__":
    main()

