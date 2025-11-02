import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM meets')
count = cursor.fetchone()[0]
print(f'Meets in database: {count}')

cursor.execute('SELECT id, name, meet_date FROM meets LIMIT 10')
print('\nSample meets:')
for row in cursor.fetchall():
    print(f'  {row[0][:20]}... | {row[1]} | {row[2]}')

conn.close()
