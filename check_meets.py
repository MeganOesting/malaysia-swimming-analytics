"""Check meets in database"""
import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT name, meet_date, city, COUNT(DISTINCT r.id) as result_count 
    FROM meets m 
    LEFT JOIN results r ON m.id = r.meet_id 
    GROUP BY m.id, m.name, m.meet_date, m.city 
    ORDER BY m.meet_date, m.name
""")

print('Meets in database:')
print('=' * 100)
print(f'{"Meet Name":<55} | {"Date":<12} | {"City":<20} | {"Results":<8}')
print('-' * 100)

for row in cursor.fetchall():
    meet_name, meet_date, city, result_count = row
    print(f'{meet_name:<55} | {meet_date or "N/A":<12} | {city or "N/A":<20} | {result_count:<8}')

print('-' * 100)
cursor.execute("SELECT COUNT(*) FROM meets")
total = cursor.fetchone()[0]
print(f"\nTotal meets: {total}")

conn.close()


