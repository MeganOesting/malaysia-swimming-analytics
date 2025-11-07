import sqlite3
import pathlib

paths = [
    pathlib.Path('malaysia_swimming.db'),
    pathlib.Path('database/malaysia_swimming.db'),
    pathlib.Path('times_database/database/malaysia_swimming.db'),
    pathlib.Path('times_database/src/database/malaysia_swimming.db'),
    pathlib.Path('statistical_analysis/database/malaysia_swimming.db')
]

for path in paths:
    resolved = path.resolve()
    if not resolved.exists():
        print(f"{resolved}: missing")
        continue
    conn = sqlite3.connect(str(resolved))
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"{resolved}:")
    print("  tables:", tables)
    conn.close()
