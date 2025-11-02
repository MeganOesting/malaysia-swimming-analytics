#!/usr/bin/env python3
"""Clear all meets and their results from the database"""

import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# First, show what will be deleted
print('=' * 80)
print('Current meets and results:')
print('=' * 80)

cursor.execute("""
    SELECT m.id, m.name, m.meet_date, 
           COUNT(r.id) as result_count
    FROM meets m
    LEFT JOIN results r ON m.id = r.meet_id
    GROUP BY m.id, m.name, m.meet_date
    ORDER BY m.meet_date DESC
""")

meets_to_delete = cursor.fetchall()
total_results = 0
for meet in meets_to_delete:
    result_count = meet[3] or 0
    total_results += result_count
    print(f'  - {meet[1]} ({meet[2]}) - {result_count} results')

print('=' * 80)
print(f'Total meets to delete: {len(meets_to_delete)}')
print(f'Total results to delete: {total_results}')
print('=' * 80)

# Ask for confirmation
response = input('\nAre you sure you want to delete ALL meets and results? (yes/no): ')
if response.lower() != 'yes':
    print('Operation cancelled.')
    conn.close()
    exit()

print('\nDeleting results...')
cursor.execute('DELETE FROM results')
deleted_results = cursor.rowcount
print(f'  Deleted {deleted_results} results')

print('Deleting meets...')
cursor.execute('DELETE FROM meets')
deleted_meets = cursor.rowcount
print(f'  Deleted {deleted_meets} meets')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM meets')
remaining_meets = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM results')
remaining_results = cursor.fetchone()[0]

print('\n' + '=' * 80)
print('Verification:')
print(f'  Remaining meets: {remaining_meets}')
print(f'  Remaining results: {remaining_results}')
print('=' * 80)

if remaining_meets == 0 and remaining_results == 0:
    print('\n✅ Database cleared successfully!')
    print('You can now start uploading meets through the admin portal.')
else:
    print('\n⚠️  Warning: Some data may remain. Check above counts.')

conn.close()


