#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL for Malaysia Swimming Analytics
"""

import sqlite3
import psycopg2
import os
from pathlib import Path
import uuid

def get_sqlite_connection():
    """Get SQLite database connection"""
    db_path = Path(__file__).parent.parent / "malaysia_swimming.db"
    return sqlite3.connect(str(db_path))

def get_postgres_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host="localhost",
        port="5432",
        database="malaysia_swimming",
        user="swimming_user",
        password="swimming_pass"
    )

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    print("Starting migration from SQLite to PostgreSQL...")
    
    # Connect to both databases
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Migrate meets
        print("Migrating meets...")
        sqlite_cursor.execute("SELECT id, name, meet_type, meet_date, location FROM meets")
        meets = sqlite_cursor.fetchall()
        
        for meet in meets:
            postgres_cursor.execute("""
                INSERT INTO meets (id, name, meet_type, meet_date, location)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, meet)
        
        # Migrate athletes
        print("Migrating athletes...")
        sqlite_cursor.execute("SELECT id, name, gender, birth_date, is_foreign, state_code FROM athletes")
        athletes = sqlite_cursor.fetchall()
        
        for athlete in athletes:
            postgres_cursor.execute("""
                INSERT INTO athletes (id, name, gender, birth_date, is_foreign, state_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, athlete)
        
        # Migrate events
        print("Migrating events...")
        sqlite_cursor.execute("SELECT id, distance, stroke, gender FROM events")
        events = sqlite_cursor.fetchall()
        
        for event in events:
            postgres_cursor.execute("""
                INSERT INTO events (id, distance, stroke, gender)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, event)
        
        # Migrate results
        print("Migrating results...")
        sqlite_cursor.execute("""
            SELECT id, meet_id, athlete_id, event_id, time_seconds, 
                   time_string, place, aqua_points, age
            FROM results
        """)
        results = sqlite_cursor.fetchall()
        
        for result in results:
            postgres_cursor.execute("""
                INSERT INTO results (id, meet_id, athlete_id, event_id, time_seconds,
                                   time_string, place, aqua_points, age)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, result)
        
        # Commit changes
        postgres_conn.commit()
        
        # Verify migration
        postgres_cursor.execute("SELECT COUNT(*) FROM meets")
        meet_count = postgres_cursor.fetchone()[0]
        postgres_cursor.execute("SELECT COUNT(*) FROM athletes")
        athlete_count = postgres_cursor.fetchone()[0]
        postgres_cursor.execute("SELECT COUNT(*) FROM results")
        result_count = postgres_cursor.fetchone()[0]
        postgres_cursor.execute("SELECT COUNT(*) FROM events")
        event_count = postgres_cursor.fetchone()[0]
        
        print(f"\nMigration completed successfully!")
        print(f"  Meets: {meet_count}")
        print(f"  Athletes: {athlete_count}")
        print(f"  Results: {result_count}")
        print(f"  Events: {event_count}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        postgres_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        postgres_conn.close()

if __name__ == "__main__":
    migrate_data()

