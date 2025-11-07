import sqlite3
import pathlib

path = pathlib.Path('database/malaysia_swimming.db').resolve()
conn = sqlite3.connect(str(path))
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT id, name, meet_date, location, created_at FROM meets ORDER BY created_at DESC').fetchall()
print('DB path:', path)
print('Total meets:', len(rows))
for row in rows:
    print(dict(row))
