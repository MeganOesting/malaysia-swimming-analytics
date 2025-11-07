import sqlite3
import pathlib

db_path = pathlib.Path('malaysia_swimming.db').resolve()
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
print('DB path:', db_path)
print('\nresults columns:')
for row in conn.execute('PRAGMA table_info(results)'):
    print(f"  {row['name']} ({row['type']})")
print('\nmeets columns:')
for row in conn.execute('PRAGMA table_info(meets)'):
    print(f"  {row['name']} ({row['type']})")
conn.close()
