#!/usr/bin/env python3
"""
Test Statistical Analysis Database Connection
"""
import sqlite3
import os
from pathlib import Path

# Database path
script_dir = Path(__file__).parent
db_path = script_dir.parent / "database" / "statistical.db"

print(f"Testing database: {db_path}")
print(f"Database exists: {db_path.exists()}")

if not db_path.exists():
    print("❌ Database not found!")
    exit(1)

try:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # List tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"\n✅ Tables found: {tables}")
    
    # Count rows in each table
    for table in ['canada_on_track', 'usa_age_deltas', 'usa_age_results', 'events']:
        if table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} rows")
    
    # Sample data
    print("\n✅ Sample data:")
    cur.execute("SELECT gender, event, age, track, time_text FROM canada_on_track LIMIT 3")
    for row in cur.fetchall():
        print(f"  Canada: {row}")
    
    cur.execute("SELECT gender, event, age_from, age_to, median_improvement FROM usa_age_deltas LIMIT 3")
    for row in cur.fetchall():
        print(f"  USA Delta: {row}")
    
    conn.close()
    print("\n✅ Database connection successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)




