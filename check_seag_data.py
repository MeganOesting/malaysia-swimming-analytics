"""Check SEAG data in database"""
import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check SEAG athletes
cursor.execute("""
    SELECT 
        a.name,
        a.birth_date,
        a.age as athlete_age,
        m.name as meet_name,
        r.day_age,
        r.year_age,
        COUNT(*) as result_count
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%'
    GROUP BY a.id, r.day_age, r.year_age
    ORDER BY a.name
    LIMIT 20
""")

print("SEAG Athletes Data:")
print("=" * 100)
print(f'{"Athlete Name":<30} | {"Birth Date":<12} | {"Athlete Age":<12} | {"Meet":<50} | {"Day Age":<8} | {"Year Age":<9} | {"Results"}')
print("-" * 100)

for row in cursor.fetchall():
    name, birth_date, athlete_age, meet_name, day_age, year_age, result_count = row
    print(f'{name:<30} | {birth_date or "NONE":<12} | {athlete_age or "N/A":<12} | {meet_name:<50} | {day_age or "N/A":<8} | {year_age or "N/A":<9} | {result_count}')

print("-" * 100)

# Summary
cursor.execute("""
    SELECT 
        COUNT(DISTINCT a.id) as total_seag_athletes,
        COUNT(*) as total_seag_results
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%'
""")

total_athletes, total_results = cursor.fetchone()
print(f"\nSummary:")
print(f"  Total SEAG athletes: {total_athletes}")
print(f"  Total SEAG results: {total_results}")
print(f"  Birth dates available: 0 (SEAG files only have birthyear in column 18, not full birthdates)")

conn.close()


