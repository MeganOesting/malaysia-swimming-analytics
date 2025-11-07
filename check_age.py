import sqlite3
import pathlib

db = pathlib.Path('malaysia_swimming.db')
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT day_age, year_age FROM results WHERE meet_id = '079da452-f551-4806-906c-a960c85fb1c1' AND day_age IS NOT NULL ORDER BY created_at LIMIT 5").fetchall()
print('sample with day_age:', [dict(r) for r in rows])
rows2 = conn.execute("SELECT day_age, year_age FROM results WHERE meet_id = '079da452-f551-4806-906c-a960c85fb1c1' AND year_age IS NOT NULL ORDER BY created_at LIMIT 5").fetchall()
print('sample with year_age:', [dict(r) for r in rows2])
conn.close()
