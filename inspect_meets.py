import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db')
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id,name,meet_type,alias,meet_date,location,city FROM meets ORDER BY created_at DESC LIMIT 5").fetchall()
for row in rows:
    print(dict(row))
conn.close()
