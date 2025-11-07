# -*- coding: utf-8 -*-
import os
import pandas as pd

import compare_deltas_canada as cdc

def main() -> None:
    df_raw = cdc.try_load_canada_table()
    if df_raw is None:
        print("Canada workbook not found or unreadable.")
        return
    df = cdc.normalize_canada(df_raw)
    if df is None or df.empty:
        print("Could not normalize Canada table.")
        return

    # Expect wide with track columns after normalization
    # Standard track column name
    track_col = 'Track 1 (Early)'
    if track_col not in df.columns:
        # Try alternative labels present
        for c in df.columns:
            if isinstance(c, str) and 'Track 1' in c:
                track_col = c
                break
        if track_col not in df.columns:
            print("Track 1 column not found in normalized table.")
            print("Available columns:", list(df.columns))
            return

    sel = df[(df['gender'].astype(str).str.strip().str.upper() == 'F') &
             (df['event'].astype(str).str.strip().strupper() == '50 FREE')]
    if sel.empty:
        # Try case variant
        sel = df[(df['gender'].astype(str).str.strip().str.upper() == 'F') &
                 (df['event'].astype(str).str.strip().str.lower() == '50 free')]
    if sel.empty:
        print("No rows found for F 50 Free.")
        return

    # Find earliest age with a non-null Track 1 value
    sel = sel[['age', track_col]].dropna(subset=[track_col]).sort_values('age')
    if sel.empty:
        print("No Track 1 values available for F 50 Free.")
        return

    start_age = int(sel.iloc[0]['age'])
    t_start = float(sel.iloc[0][track_col])

    # Next age
    next_row = sel[sel['age'] == start_age + 1]
    if not next_row.empty:
        t_next = float(next_row.iloc[0][track_col])
        print(f"Track 1 starts at age {start_age}: time={t_start:.2f}s; next age {start_age+1}: time={t_next:.2f}s")
    else:
        print(f"Track 1 starts at age {start_age}: time={t_start:.2f}s; next age {start_age+1}: time not available")

if __name__ == '__main__':
    main()
