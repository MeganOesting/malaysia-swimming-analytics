import sqlite3
import pathlib
import os
from datetime import datetime

paths = [
    pathlib.Path('malaysia_swimming.db'),
    pathlib.Path('database/malaysia_swimming.db'),
    pathlib.Path('times_database/database/malaysia_swimming.db'),
    pathlib.Path('times_database/src/database/malaysia_swimming.db'),
    pathlib.Path('statistical_analysis/database/malaysia_swimming.db')
]

def format_ts(ts):
    if ts is None:
        return 'n/a'
    return datetime.fromtimestamp(ts).isoformat(timespec='seconds')

for path in paths:
    resolved = path.resolve()
    print('=' * 80)
    print('Path:', resolved)
    if not resolved.exists():
        print('Status: MISSING')
        continue
    stat = resolved.stat()
    print('Size:', stat.st_size, 'bytes')
    print('Modified:', format_ts(stat.st_mtime))
    try:
        conn = sqlite3.connect(str(resolved))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print('Status: cannot open database ->', e)
        continue
    try:
        tables = [row['name'] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        print('Tables:', tables)
        if 'meets' in tables:
            rows = conn.execute("SELECT id, name, meet_type, meet_date, alias, created_at FROM meets ORDER BY created_at DESC LIMIT 5").fetchall()
            print('Sample meets:', [dict(row) for row in rows])
        if 'results' in tables:
            count = conn.execute('SELECT COUNT(*) AS c FROM results').fetchone()['c']
            print('Results count:', count)
    except Exception as e:
        print('Error inspecting database:', e)
    finally:
        conn.close()
