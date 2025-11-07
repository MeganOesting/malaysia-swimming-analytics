import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db').resolve()
conn = sqlite3.connect(str(db))
print('columns:', conn.execute('PRAGMA table_info(meets)').fetchall())
rows = conn.execute('SELECT id, name, meet_type, meet_date, location, created_at FROM meets ORDER BY created_at DESC LIMIT 5').fetchall()
for row in rows:
    print(row)
conn.close()
