#!/usr/bin/env python3
"""Clear ALL data from the database (meets, results, athletes, events)"""

import sqlite3
from pathlib import Path

# Find database file
project_root = Path(__file__).parent
db_path = project_root / "malaysia_swimming.db"

if not db_path.exists():
    print(f"Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Show current counts
print('=' * 80)
print('Current database contents:')
print('=' * 80)

cursor.execute("SELECT COUNT(*) FROM meets")
meet_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM results")
result_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM athletes")
athlete_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM events")
event_count = cursor.fetchone()[0]

print(f'  Meets: {meet_count}')
print(f'  Results: {result_count}')
print(f'  Athletes: {athlete_count}')
print(f'  Events: {event_count}')
print('=' * 80)

# Ask for confirmation
response = input('\n⚠️  Are you sure you want to DELETE ALL DATA from the database? (type "yes" to confirm): ')
if response.lower() != 'yes':
    print('Operation cancelled.')
    conn.close()
    exit()

print('\nDeleting data...')
print('  Deleting results...')
cursor.execute('DELETE FROM results')
deleted_results = cursor.rowcount
print(f'    Deleted {deleted_results} results')

print('  Deleting meets...')
cursor.execute('DELETE FROM meets')
deleted_meets = cursor.rowcount
print(f'    Deleted {deleted_meets} meets')

print('  Deleting athletes...')
cursor.execute('DELETE FROM athletes')
deleted_athletes = cursor.rowcount
print(f'    Deleted {deleted_athletes} athletes')

print('  Deleting events...')
cursor.execute('DELETE FROM events')
deleted_events = cursor.rowcount
print(f'    Deleted {deleted_events} events')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM meets')
remaining_meets = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM results')
remaining_results = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM athletes')
remaining_athletes = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM events')
remaining_events = cursor.fetchone()[0]

print('\n' + '=' * 80)
print('Verification:')
print(f'  Remaining meets: {remaining_meets}')
print(f'  Remaining results: {remaining_results}')
print(f'  Remaining athletes: {remaining_athletes}')
print(f'  Remaining events: {remaining_events}')
print('=' * 80)

if (remaining_meets == 0 and remaining_results == 0 and 
    remaining_athletes == 0 and remaining_events == 0):
    print('\n✅ Database cleared successfully!')
    print('You can now start uploading meets through the admin portal.')
else:
    print('\n⚠️  Warning: Some data may remain. Check above counts.')

conn.close()


