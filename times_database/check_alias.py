import sqlite3
from src.web.routers.admin import get_database_connection, ensure_meet_alias_column

conn = get_database_connection()
print('Using DB:', conn.execute('PRAGMA database_list').fetchall())
print('ensure_meet_alias_column ->', ensure_meet_alias_column(conn))
print('columns:', conn.execute('PRAGMA table_info(meets)').fetchall())
conn.close()
