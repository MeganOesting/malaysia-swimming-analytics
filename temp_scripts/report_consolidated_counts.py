"""Report row counts for registration, results, and rebuilt consolidated workbooks."""

from pathlib import Path

import pandas as pd


ROOT = Path("C:/Users/megan/OneDrive/Documents/Malaysia Swimming Analytics")

REG_PATH = ROOT / "data" / "manual_matching" / "consolidated_registration_subset.xlsx"
RES_PATH = ROOT / "data" / "manual_matching" / "consolidated_results_athlete_birthdat_fullname.xlsx"
MERGED_PATH = ROOT / "data" / "manual_matching" / "consolidated_athlete_ID_rebuilt.xlsx"


def load_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_excel(path)


def non_empty(series: pd.Series) -> int:
    return int(series.astype(str).str.strip().ne("").sum())


def main() -> None:
    reg_df = load_dataframe(REG_PATH)
    res_df = load_dataframe(RES_PATH)
    merged_df = load_dataframe(MERGED_PATH)

    print(f"registration subset rows: {len(reg_df)}")
    print(f"results workbook rows: {len(res_df)}")
    print(f"merged rows: {len(merged_df)}")
    if "BIRTHDATE" in merged_df.columns:
        print(
            f"merged rows with non-empty BIRTHDATE: {non_empty(merged_df['BIRTHDATE'])}"
        )
    if "Birthday_raw" in merged_df.columns:
        print(
            f"merged rows with non-empty Birthday_raw: {non_empty(merged_df['Birthday_raw'])}"
        )


if __name__ == "__main__":
    main()

