import sqlite3
import pathlib

path = pathlib.Path('malaysia_swimming.db').resolve()
print('DB:', path)
conn = sqlite3.connect(str(path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
info = cursor.execute('PRAGMA table_info(meets)').fetchall()
print('Columns:')
for col in info:
    print(col)
rows = cursor.execute('SELECT id, name, meet_type, meet_date, location, created_at FROM meets ORDER BY created_at DESC LIMIT 5').fetchall()
print('Sample rows:')
for row in rows:
    print(dict(row))
conn.close()
