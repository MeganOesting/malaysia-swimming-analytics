# -*- coding: utf-8 -*-
import os
import sqlite3
from typing import Optional

# Database path: Use database in same directory structure as script
# If script is in statistical_analysis/scripts/, database is in statistical_analysis/database/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if 'Statistical Analysis' in SCRIPT_DIR or 'statistical_analysis' in SCRIPT_DIR:
    # New structure: statistical_analysis/database/statistical.db
    DB_PATH = os.path.join(SCRIPT_DIR, '..', 'database', 'statistical.db')
else:
    # Old structure: ../database/malaysia_swimming.db (backward compatibility)
    DB_PATH = os.path.join('..', 'database', 'malaysia_swimming.db')


def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS canada_on_track (
               gender TEXT NOT NULL,
               event TEXT NOT NULL,
               age INTEGER NOT NULL,
               track INTEGER NOT NULL,
               time_text TEXT NOT NULL,
               time_seconds REAL NOT NULL,
               aqua_points REAL,
               PRIMARY KEY (gender, event, track, age)
           )'''
    )
    cur.execute('CREATE INDEX IF NOT EXISTS idx_canada_on_track_lookup ON canada_on_track (gender, event, age, track)')

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS usa_age_deltas (
               gender TEXT NOT NULL,
               event TEXT NOT NULL,
               age_from INTEGER NOT NULL,
               age_to INTEGER NOT NULL,
               sample_size INTEGER,
               median_improvement REAL,
               mean_improvement REAL,
               std_improvement REAL,
               q25_improvement REAL,
               q75_improvement REAL,
               analysis_date TEXT,
               PRIMARY KEY (gender, event, age_from, age_to)
           )'''
    )
    cur.execute('CREATE INDEX IF NOT EXISTS idx_usa_age_deltas_lookup ON usa_age_deltas (gender, event)')

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS usa_age_results (
               gender TEXT NOT NULL,
               event TEXT NOT NULL,
               age INTEGER NOT NULL,
               rank INTEGER NOT NULL,
               time_text TEXT NOT NULL,
               time_seconds REAL NOT NULL,
               season TEXT NOT NULL,
               aqua_points REAL,
               PRIMARY KEY (gender, event, age, rank, season)
           )'''
    )
    cur.execute('CREATE INDEX IF NOT EXISTS idx_usa_age_results_lookup ON usa_age_results (gender, event, age, season)')

    conn.commit()


def compute_aqua_points_lcm(time_seconds: Optional[float], base_seconds: Optional[float]) -> Optional[float]:
    """Compute AQUA points via cubic formula P = 1000 * (B / T)^3. Returns None if inputs invalid.
       base_seconds can be provided from a yearly base table; if not available, returns None.
    """
    if time_seconds is None or base_seconds is None:
        return None
    if time_seconds <= 0 or base_seconds <= 0:
        return None
    try:
        return 1000.0 * (base_seconds / time_seconds) ** 3
    except Exception:
        return None
