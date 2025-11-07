import sqlite3
import pathlib

path = pathlib.Path('malaysia_swimming.db').resolve()
conn = sqlite3.connect(str(path))
conn.row_factory = sqlite3.Row
print('Path:', path)
tables = [row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('Tables:', tables)
print('\nMeets columns:')
for row in conn.execute("PRAGMA table_info(meets)"):
    print(dict(row))
print('\nSample meets:')
for row in conn.execute("SELECT id, name, meet_type, meet_date, location FROM meets ORDER BY created_at DESC LIMIT 5"):
    print(dict(row))
conn.close()
