# -*- coding: utf-8 -*-
import os
import pandas as pd

RESULTS_CSV = 'MOT_Delta_Analysis_Results.csv'
INDEX_CSV = 'MOT_Delta_Index.csv'
# Handle both old and new folder structures
script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    DELTA_BASE = os.path.join('data', 'Delta Data')
else:
    DELTA_BASE = 'Delta Data'


def make_folder_name(gender: str, event: str, age_from: str, age_to: str) -> str:
    return f"{gender} {event} {age_from} to {age_to}"


def main() -> None:
    if not os.path.exists(RESULTS_CSV):
        print(f"Results file not found: {RESULTS_CSV}")
        return

    df = pd.read_csv(RESULTS_CSV, encoding='utf-8')

    # Build paths
    folder_names = df.apply(lambda r: make_folder_name(str(r['gender']), str(r['event']), str(r['age_from']), str(r['age_to'])), axis=1)
    delta_paths = folder_names.apply(lambda n: os.path.join(DELTA_BASE, n))
    csv_paths = folder_names.apply(lambda n: os.path.join(DELTA_BASE, n, f"{n} Athlete_Improvement_Data.csv"))
    report_paths = folder_names.apply(lambda n: os.path.join(DELTA_BASE, n, f"{n} Improvement Analysis Report.txt"))

    index_df = df.copy()
    index_df['delta_folder_path'] = delta_paths
    index_df['csv_path'] = csv_paths
    index_df['report_path'] = report_paths

    index_df.to_csv(INDEX_CSV, index=False, encoding='utf-8')
    print(f"Wrote index: {INDEX_CSV}")


if __name__ == '__main__':
    main()
