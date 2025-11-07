import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db')
conn = sqlite3.connect(str(db))
rows = conn.execute("PRAGMA table_info(athletes)").fetchall()
for row in rows:
    print(row)
conn.close()
