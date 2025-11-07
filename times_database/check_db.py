import sqlite3
import pathlib

db = pathlib.Path('database/malaysia_swimming.db').resolve()
conn = sqlite3.connect(str(db))
print('DB path:', db)
print('tables:', [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")])
conn.close()
