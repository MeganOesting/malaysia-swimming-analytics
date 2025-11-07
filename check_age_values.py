import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db')
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT a.age, a.birth_date FROM athletes a JOIN results r ON a.id = r.athlete_id WHERE r.meet_id = '079da452-f551-4806-906c-a960c85fb1c1' LIMIT 5").fetchall()
print([dict(r) for r in row])
conn.close()
