#!/usr/bin/env python3
"""
Test Times Database SQLite Connection
"""
import sqlite3
import os
from pathlib import Path

# Database path
script_dir = Path(__file__).parent
db_path = script_dir.parent / "database" / "malaysia_swimming.db"

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
    
    # Count rows in web app tables
    web_tables = ['athletes', 'meets', 'results', 'events', 'clubs']
    print("\n📊 Web Application Tables:")
    for table in web_tables:
        if table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table}: {count} rows")
        else:
            print(f"  {table}: ❌ Not found")
    
    # Check for statistical tables (shouldn't be here)
    stat_tables = ['canada_on_track', 'usa_age_deltas']
    if any(t in tables for t in stat_tables):
        print("\n⚠️  Warning: Statistical tables found in web app database!")
        print("   These should be in statistical_analysis/database/statistical.db")
    else:
        print("\n✅ No statistical tables in web app database (correct)")
    
    conn.close()
    print("\n✅ Database connection successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)




