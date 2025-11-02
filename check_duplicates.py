import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check for duplicate athletes (same name)
cursor.execute("""
    SELECT name, COUNT(*) as count
    FROM athletes
    GROUP BY name
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 20
""")
duplicate_athletes = cursor.fetchall()
print("Duplicate athletes (same name, different IDs):")
for name, count in duplicate_athletes[:20]:
    print(f"  {name}: {count} records")

# Check total vs unique names
cursor.execute("SELECT COUNT(*) FROM athletes")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(DISTINCT name) FROM athletes")
unique_names = cursor.fetchone()[0]
print(f"\nTotal athlete records: {total}")
print(f"Unique athlete names: {unique_names}")
print(f"Duplicate athlete records: {total - unique_names}")

# Check SUKMA specifically
cursor.execute("""
    SELECT COUNT(*) FROM results
    WHERE meet_id IN (
        SELECT id FROM meets WHERE name = 'SUKMA 2024'
    )
""")
sukma_results = cursor.fetchone()[0]
print(f"\nSUKMA 2024 results: {sukma_results}")

# Check duplicate meets
cursor.execute("""
    SELECT name, meet_date, COUNT(*) as count
    FROM meets
    GROUP BY name, meet_date
    HAVING COUNT(*) > 1
    ORDER BY count DESC
""")
duplicate_meets = cursor.fetchall()
print(f"\nDuplicate meets (same name and date, different IDs): {len(duplicate_meets)}")
for name, date, count in duplicate_meets[:10]:
    print(f"  {name} ({date}): {count} records")

conn.close()




