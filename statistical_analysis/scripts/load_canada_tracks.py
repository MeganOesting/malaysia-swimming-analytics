# -*- coding: utf-8 -*-
import os
import re
import sqlite3
import pandas as pd
from typing import Optional

from db_schema import get_conn, ensure_schema, compute_aqua_points_lcm
from events_catalog import normalize_event

# Handle both old and new folder structures
script_dir = os.path.dirname(os.path.abspath(__file__))
if 'statistical_analysis' in script_dir.lower():
    WORKBOOK = os.path.join('..', 'data', 'Malaysia On Track Statistical Analysis.xlsx')
else:
    WORKBOOK = 'Malaysia On Track Statistical Analysis.xlsx'
# Exact sheet name as provided
SHEET_EXACT = 'Canada On Track Table, SEA MEdal Age, World Top 10'


def to_seconds(val: object) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if s == '':
        return None
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            return float(s)
        except Exception:
            return None
    s = re.sub(r"[^0-9:\.]", "", s)
    parts = s.split(':')
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            m = int(parts[0]) if parts[0] else 0
            sec = float(parts[1])
            return m * 60 + sec
        if len(parts) == 3:
            h = int(parts[0]) if parts[0] else 0
            m = int(parts[1]) if parts[1] else 0
            sec = float(parts[2])
            return h * 3600 + m * 60 + sec
    except Exception:
        return None
    return None


def _read_sheet() -> pd.DataFrame:
    xls = pd.ExcelFile(WORKBOOK)
    if SHEET_EXACT in xls.sheet_names:
        return pd.read_excel(WORKBOOK, sheet_name=SHEET_EXACT, dtype={'Gender': str, 'Event': str})
    # Fallback: case-insensitive contains match for robustness
    for name in xls.sheet_names:
        if 'canada on track table' in name.lower():
            return pd.read_excel(WORKBOOK, sheet_name=name, dtype={'Gender': str, 'Event': str})
    raise ValueError(f"Worksheet named '{SHEET_EXACT}' not found and no fallback match available")


def load_canada_into_db() -> None:
    if not os.path.exists(WORKBOOK):
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK}")
    df = _read_sheet()
    # Expect columns: Gender, Event, Age, Track, Time
    required = ['Gender','Event','Age','Track','Time']
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Required column missing: {c}")

    conn = get_conn()
    ensure_schema(conn)

    rows = []
    for _, r in df.iterrows():
        gender = (r['Gender'] or '').strip()
        event_raw = (r['Event'] or '').strip()
        ok, event = normalize_event(event_raw)
        if not ok:
            continue  # skip non-canonical events
        try:
            age = int(r['Age'])
        except Exception:
            continue
        try:
            track = int(r['Track'])
        except Exception:
            continue
        time_text = str(r['Time']).strip()
        time_seconds = to_seconds(time_text)
        if time_seconds is None:
            continue
        aqua_points = None  # Placeholder until base times are wired
        rows.append((gender, event, age, track, time_text, time_seconds, aqua_points))

    with conn:
        conn.executemany(
            '''INSERT OR REPLACE INTO canada_on_track
               (gender, event, age, track, time_text, time_seconds, aqua_points)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            rows
        )
    conn.close()
    print(f"Inserted/updated {len(rows)} canada_on_track rows")


if __name__ == '__main__':
    load_canada_into_db()
