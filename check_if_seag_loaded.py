import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check total results count
cursor.execute("SELECT COUNT(*) FROM results")
total_results = cursor.fetchone()[0]
print(f"Total results in database: {total_results}")

# Check for results with Singapore city or foreign athletes (SEAG would have many foreign)
cursor.execute("""
    SELECT COUNT(*) FROM results r
    JOIN meets m ON r.meet_id = m.id
    WHERE m.city = 'Singapore'
""")
singapore_results = cursor.fetchone()[0]
print(f"Results in meets with city='Singapore': {singapore_results}")

# Check foreign athletes count
cursor.execute("""
    SELECT COUNT(DISTINCT r.athlete_id) FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    WHERE a.is_foreign = 1
""")
foreign_athletes = cursor.fetchone()[0]
print(f"Total foreign athletes in results: {foreign_athletes}")

# Check what meet names exist
cursor.execute("SELECT DISTINCT name FROM meets ORDER BY name")
all_meet_names = cursor.fetchall()
print(f"\nAll unique meet names ({len(all_meet_names)} total):")
for name, in all_meet_names:
    cursor.execute("SELECT COUNT(*) FROM results WHERE meet_id IN (SELECT id FROM meets WHERE name = ?)", (name,))
    count = cursor.fetchone()[0]
    print(f"  {name}: {count} results")

# Check if SEAG file was processed by looking for Singapore athletes or specific meet date
cursor.execute("""
    SELECT COUNT(*) FROM results r
    JOIN meets m ON r.meet_id = m.id
    WHERE m.meet_date = '2025-06-25'
""")
june_25_results = cursor.fetchone()[0]
print(f"\nResults on 2025-06-25 (SEAG date): {june_25_results}")

conn.close()














