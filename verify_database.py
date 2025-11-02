#!/usr/bin/env python3
"""Quick verification script for the Malaysian swimming database"""

import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

print('=== VERIFYING DATABASE ===\n')

# Check athletes table structure
cursor.execute('PRAGMA table_info(athletes)')
cols = [(row[1], row[2]) for row in cursor.fetchall()]
print('Athletes table columns:')
for col, dtype in cols:
    print(f'  {col}: {dtype}')

# Count athletes
cursor.execute('SELECT COUNT(*) FROM athletes')
total = cursor.fetchone()[0]
print(f'\nTotal athletes: {total}')

# Count athletes with birth_date
cursor.execute("SELECT COUNT(*) FROM athletes WHERE birth_date IS NOT NULL AND birth_date != ''")
with_birthdate = cursor.fetchone()[0]
print(f'Athletes with birth_date: {with_birthdate} ({with_birthdate/total*100:.1f}%)')

# Sample athletes with birth_date
cursor.execute("SELECT name, gender, birth_date, age FROM athletes WHERE birth_date IS NOT NULL AND birth_date != '' LIMIT 5")
print('\nSample athletes with birth_date:')
for row in cursor.fetchall():
    print(f'  {row[0]} ({row[1]}), born: {row[2]}, age: {row[3]}')

# Count results
cursor.execute('SELECT COUNT(*) FROM results')
print(f'\nTotal results: {cursor.fetchone()[0]}')

cursor.execute('SELECT COUNT(DISTINCT athlete_id) FROM results')
print(f'Unique athletes with results: {cursor.fetchone()[0]}')

# Meets with athlete counts
cursor.execute("""
    SELECT m.name, m.meet_date, COUNT(DISTINCT r.athlete_id) as athletes 
    FROM meets m 
    JOIN results r ON m.id = r.meet_id 
    GROUP BY m.id 
    ORDER BY m.meet_date
""")
print('\nMeets with athlete counts:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}, {row[2]} athletes')

conn.close()
print('\n✅ Database verification complete!')




