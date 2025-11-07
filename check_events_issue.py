import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM events')
total_events = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT event_id) FROM results')
unique_event_ids = cursor.fetchone()[0]

cursor.execute('SELECT MIN(event_id), MAX(event_id) FROM results')
min_max = cursor.fetchone()

print(f'Total events in events table: {total_events}')
print(f'Unique event_ids in results: {unique_event_ids}')
print(f'Min event_id: {min_max[0]}, Max event_id: {min_max[1]}')

cursor.execute('SELECT event_id, COUNT(*) as cnt FROM results GROUP BY event_id ORDER BY cnt DESC LIMIT 5')
print('\nTop 5 event_ids by usage:')
for row in cursor.fetchall():
    print(f'  event_id {row[0]}: {row[1]} results')

# Check if event_ids in results match events table
cursor.execute('SELECT COUNT(*) FROM results r LEFT JOIN events e ON r.event_id = e.id WHERE e.id IS NULL')
orphaned = cursor.fetchone()[0]
print(f'\nResults with event_ids not in events table: {orphaned}')

# Check if athlete_ids match
cursor.execute('SELECT COUNT(*) FROM results r LEFT JOIN athletes a ON r.athlete_id = a.id WHERE a.id IS NULL')
orphaned_athletes = cursor.fetchone()[0]
print(f'Results with athlete_ids not in athletes table: {orphaned_athletes}')

# Check if meet_ids match
cursor.execute('SELECT COUNT(*) FROM results r LEFT JOIN meets m ON r.meet_id = m.id WHERE m.id IS NULL')
orphaned_meets = cursor.fetchone()[0]
print(f'Results with meet_ids not in meets table: {orphaned_meets}')

conn.close()












