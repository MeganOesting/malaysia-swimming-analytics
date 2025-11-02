#!/usr/bin/env python3
"""Check meets table structure and identify admin-uploaded meets"""

import sqlite3
from datetime import datetime

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check table structure
print('\n' + '=' * 80)
print('Meets table structure:')
print('=' * 80)
cursor.execute('PRAGMA table_info(meets)')
for row in cursor.fetchall():
    print(f'  {row[1]:20s} {row[2]:15s} {"NOT NULL" if row[3] else "NULL"} {"PRIMARY KEY" if row[5] else ""}')

# Get all meets with all available columns
print('\n' + '=' * 100)
print('All meets in database (with all columns):')
print('=' * 100)

# Get column names
cursor.execute('PRAGMA table_info(meets)')
columns = [row[1] for row in cursor.fetchall()]
print(f'Columns: {", ".join(columns)}')

# Fetch meets
cursor.execute("""
    SELECT *
    FROM meets
    ORDER BY meet_date DESC
""")

meets = cursor.fetchall()
for idx, meet in enumerate(meets, 1):
    print(f'\n--- Meet #{idx} ---')
    for col, val in zip(columns, meet):
        if val is not None:
            print(f'  {col:20s}: {val}')

print('\n' + '=' * 100)
print(f'Total: {len(meets)} meets')
print('=' * 100)

conn.close()


