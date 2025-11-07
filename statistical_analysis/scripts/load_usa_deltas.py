# -*- coding: utf-8 -*-
import os
import sqlite3
import pandas as pd
from typing import List

from db_schema import get_conn, ensure_schema
from events_catalog import normalize_event

RESULTS_CSV = 'MOT_Delta_Analysis_Results.csv'


def load_usa_deltas_into_db() -> None:
    if not os.path.exists(RESULTS_CSV):
        raise FileNotFoundError(f"Results CSV not found: {RESULTS_CSV}")
    df = pd.read_csv(RESULTS_CSV, encoding='utf-8')

    needed = ['gender','event','age_from','age_to','sample_size','median_improvement','mean_improvement','std_improvement','q25_improvement','q75_improvement','analysis_date']
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Required column missing in results: {c}")

    rows: List[tuple] = []
    for _, r in df.iterrows():
        gender = str(r['gender']).strip()
        ok, event = normalize_event(str(r['event']))
        if not ok:
            continue
        try:
            age_from = int(r['age_from'])
            age_to = int(r['age_to'])
        except Exception:
            continue
        vals = (
            gender,
            event,
            age_from,
            age_to,
            int(r['sample_size']) if pd.notna(r['sample_size']) else None,
            float(r['median_improvement']) if pd.notna(r['median_improvement']) else None,
            float(r['mean_improvement']) if pd.notna(r['mean_improvement']) else None,
            float(r['std_improvement']) if pd.notna(r['std_improvement']) else None,
            float(r['q25_improvement']) if pd.notna(r['q25_improvement']) else None,
            float(r['q75_improvement']) if pd.notna(r['q75_improvement']) else None,
            str(r['analysis_date']) if pd.notna(r['analysis_date']) else None,
        )
        rows.append(vals)

    conn = get_conn()
    ensure_schema(conn)
    with conn:
        conn.executemany(
            '''INSERT OR REPLACE INTO usa_age_deltas
               (gender, event, age_from, age_to, sample_size, median_improvement, mean_improvement, std_improvement, q25_improvement, q75_improvement, analysis_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            rows
        )
    conn.close()
    print(f"Inserted/updated {len(rows)} usa_age_deltas rows")


if __name__ == '__main__':
    load_usa_deltas_into_db()
