import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db')
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT a.birthdate, a.age FROM athletes a JOIN results r ON a.id = r.athlete_id WHERE r.meet_id = '079da452-f551-4806-906c-a960c85fb1c1' LIMIT 1").fetchone()
print(dict(row) if row else None)
conn.close()
