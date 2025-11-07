#!/usr/bin/env python3
"""
Extract Statistical Analysis tables from main database to separate statistical database.
This creates a clean statistical.db with only canada_on_track, usa_age_deltas, and usa_age_results tables.
"""
import sqlite3
import os
import shutil
from pathlib import Path

# Paths
script_dir = Path(__file__).parent
src_db = script_dir.parent / "database" / "malaysia_swimming.db"
dst_db = script_dir / "database" / "statistical.db"

def extract_statistical_tables():
    """Extract only statistical tables to new database"""
    
    # Ensure directory exists
    os.makedirs(dst_db.parent, exist_ok=True)
    
    # Connect to source database
    if not src_db.exists():
        print(f"Source database not found: {src_db}")
        return False
        
    src_conn = sqlite3.connect(str(src_db))
    src_cur = src_conn.cursor()
    
    # Create new database
    if dst_db.exists():
        print(f"Removing existing {dst_db}")
        dst_db.unlink()
    
    dst_conn = sqlite3.connect(str(dst_db))
    dst_cur = dst_conn.cursor()
    
    # Get list of statistical tables
    statistical_tables = ['canada_on_track', 'usa_age_deltas', 'usa_age_results', 'events']
    
    # Check which tables exist
    src_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in src_cur.fetchall()]
    
    print(f"Found tables in source: {existing_tables}")
    
    for table in statistical_tables:
        if table not in existing_tables:
            print(f"Warning: Table {table} not found in source database")
            continue
            
        # Get table schema
        src_cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        schema = src_cur.fetchone()
        if schema:
            dst_cur.execute(schema[0])
            print(f"Created table: {table}")
        
        # Copy data
        src_cur.execute(f"SELECT * FROM {table}")
        rows = src_cur.fetchall()
        
        # Get column names
        src_cur.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in src_cur.fetchall()]
        placeholders = ','.join(['?'] * len(columns))
        col_names = ','.join(columns)
        
        insert_sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        dst_cur.executemany(insert_sql, rows)
        
        # Copy indexes
        src_cur.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table}' AND sql IS NOT NULL")
        for idx_sql in src_cur.fetchall():
            if idx_sql[0]:
                dst_cur.execute(idx_sql[0])
                print(f"Created index for {table}")
        
        print(f"Copied {len(rows)} rows from {table}")
    
    dst_conn.commit()
    
    # Verify
    dst_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    dst_tables = [row[0] for row in dst_cur.fetchall()]
    print(f"\nTables in statistical database: {dst_tables}")
    
    # Count rows
    for table in statistical_tables:
        if table in dst_tables:
            dst_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = dst_cur.fetchone()[0]
            print(f"  {table}: {count} rows")
    
    src_conn.close()
    dst_conn.close()
    
    print(f"\n✅ Statistical database created: {dst_db}")
    return True

if __name__ == '__main__':
    extract_statistical_tables()




