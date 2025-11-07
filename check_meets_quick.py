import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM meets')
total = cursor.fetchone()[0]
print(f'Total meets in database: {total}')

if total > 0:
    cursor.execute('SELECT id, name, meet_date, meet_type FROM meets ORDER BY meet_date DESC LIMIT 10')
    print('\nRecent meets:')
    for row in cursor.fetchall():
        print(f'  {row[0][:8]}... | {row[1]} | {row[2]} | Alias: {row[3]}')

conn.close()












