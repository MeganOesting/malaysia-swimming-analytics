#!/usr/bin/env python3
"""Check what meets are in the database"""

import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT name, meet_type, meet_date, city, 
           (SELECT COUNT(*) FROM results WHERE meet_id = meets.id) as result_count
    FROM meets
    ORDER BY meet_date DESC, name
""")

print('\n' + '=' * 100)
print('Current meets in database:')
print('=' * 100)
print(f"{'Meet Name':<50} {'Alias':<12} {'Date':<12} {'City':<20} {'Results':<8}")
print('=' * 100)

meets = cursor.fetchall()
for row in meets:
    name = row[0] or "(no name)"
    alias = row[1] or "(none)"
    date = row[2] or ""
    city = row[3] or ""
    count = row[4] or 0
    print(f"{name:<50} {alias:<12} {date:<12} {city:<20} {count:<8}")

print('=' * 100)
print(f'Total: {len(meets)} meets')
print('=' * 100)

conn.close()












