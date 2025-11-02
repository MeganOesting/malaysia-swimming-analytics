#!/usr/bin/env python3
"""
Remove statistical analysis tables from Times Database.
These tables now live in statistical_analysis/database/statistical.db
"""
import sqlite3
from pathlib import Path

# Database path
script_dir = Path(__file__).parent
db_path = script_dir.parent / "database" / "malaysia_swimming.db"

print(f"Cleaning up database: {db_path}")
print(f"Database exists: {db_path.exists()}")

if not db_path.exists():
    print("❌ Database not found!")
    exit(1)

# Tables to remove (statistical analysis tables)
statistical_tables = ['canada_on_track', 'usa_age_deltas', 'usa_age_results']

try:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    # Check which tables exist
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cur.fetchall()]
    
    print(f"\nTables before cleanup: {existing_tables}")
    
    # Remove statistical tables
    removed = []
    for table in statistical_tables:
        if table in existing_tables:
            # Drop indexes first
            cur.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
            indexes = [row[0] for row in cur.fetchall()]
            for idx in indexes:
                if idx and not idx.startswith('sqlite_'):
                    cur.execute(f"DROP INDEX IF EXISTS {idx}")
                    print(f"  Dropped index: {idx}")
            
            # Drop table
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            removed.append(table)
            print(f"  ✅ Removed table: {table}")
        else:
            print(f"  ⚠️  Table not found (already removed?): {table}")
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    remaining_tables = [row[0] for row in cur.fetchall()]
    
    print(f"\nTables after cleanup: {remaining_tables}")
    
    # Check if any statistical tables remain
    remaining_stat = [t for t in statistical_tables if t in remaining_tables]
    if remaining_stat:
        print(f"\n⚠️  Warning: Some statistical tables still present: {remaining_stat}")
    else:
        print(f"\n✅ All statistical tables removed successfully!")
        print(f"   These tables now live in: statistical_analysis/database/statistical.db")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ Cleanup complete!")




