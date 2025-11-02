import sqlite3

conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()

print('=== DATABASE SCHEMA VERIFICATION ===')
print()

# Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(f'  {table[0]}')
print()

# Check results table structure
cursor.execute("PRAGMA table_info(results)")
columns = cursor.fetchall()
print('Results table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')
print()

# Check meets table structure
cursor.execute("PRAGMA table_info(meets)")
columns = cursor.fetchall()
print('Meets table columns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')
print()

# Sample data from results table
cursor.execute("SELECT * FROM results LIMIT 5")
sample_results = cursor.fetchall()
print('Sample results data:')
for result in sample_results:
    print(f'  {result}')
print()

# Check meet_id references
cursor.execute("SELECT DISTINCT meet_id FROM results LIMIT 10")
meet_ids = cursor.fetchall()
print('Meet IDs in results:')
for meet_id in meet_ids:
    print(f'  {meet_id[0]}')
print()

conn.close()



