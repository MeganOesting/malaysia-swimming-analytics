import sqlite3
conn = sqlite3.connect('malaysia_swimming.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, name, meet_type, alias, meet_date, city FROM meets ORDER BY created_at DESC LIMIT 5').fetchall()
for row in rows:
    print(dict(row))
conn.close()
