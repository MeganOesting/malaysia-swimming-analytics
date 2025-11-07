import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check total results
cursor.execute("SELECT COUNT(*) FROM results")
total = cursor.fetchone()[0]
print(f"Total results: {total}")

# Check results by meet
cursor.execute("""
    SELECT m.name, COUNT(r.id) as result_count
    FROM meets m
    LEFT JOIN results r ON m.id = r.meet_id
    GROUP BY m.id, m.name
    ORDER BY result_count DESC
""")
print("\nResults by meet:")
for name, count in cursor.fetchall():
    if count > 0:
        print(f"  {name}: {count} results")

# Check SEAG specifically
cursor.execute("""
    SELECT COUNT(DISTINCT r.athlete_id) as athletes,
           COUNT(r.id) as results
    FROM results r
    WHERE r.meet_id IN (
        SELECT id FROM meets 
        WHERE name LIKE '%47th%' OR name LIKE '%Southeast Asian%'
    )
""")
seag_data = cursor.fetchone()
print(f"\nSEAG (47th Southeast Asian):")
print(f"  Unique athletes: {seag_data[0]}")
print(f"  Total results: {seag_data[1]}")

# Check for duplicate results
cursor.execute("""
    SELECT meet_id, athlete_id, event_id, COUNT(*) as count
    FROM results
    GROUP BY meet_id, athlete_id, event_id
    HAVING COUNT(*) > 1
    LIMIT 10
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"\n⚠️ Found duplicate results (same athlete, same event, same meet):")
    for dup in duplicates[:10]:
        print(f"  Meet: {dup[0][:8]}..., Athlete: {dup[1][:8]}..., Event: {dup[2][:8]}..., Count: {dup[3]}")
else:
    print("\n✅ No duplicate results found")

conn.close()














