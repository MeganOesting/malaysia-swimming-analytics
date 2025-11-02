"""Check day_age and year_age in results"""
import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check a sample of results with ages
cursor.execute("""
    SELECT 
        a.name,
        a.birth_date,
        m.name as meet_name,
        m.meet_date,
        r.day_age,
        r.year_age,
        COUNT(*) as result_count
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE a.birth_date IS NOT NULL
    GROUP BY a.id, m.id, r.day_age, r.year_age
    ORDER BY m.meet_date, a.name
    LIMIT 20
""")

print("Sample results with day_age and year_age:")
print("=" * 100)
print(f'{"Athlete Name":<30} | {"Birth Date":<12} | {"Meet Name":<35} | {"Meet Date":<12} | {"Day Age":<8} | {"Year Age":<9} | {"Results"}')
print("-" * 100)

for row in cursor.fetchall():
    name, birth_date, meet_name, meet_date, day_age, year_age, result_count = row
    print(f'{name:<30} | {birth_date or "N/A":<12} | {meet_name:<35} | {meet_date or "N/A":<12} | {day_age or "N/A":<8} | {year_age or "N/A":<9} | {result_count}')

print("-" * 100)

# Check age coverage
cursor.execute("SELECT COUNT(*) FROM results WHERE day_age IS NOT NULL")
with_day_age = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM results WHERE year_age IS NOT NULL")
with_year_age = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM results")
total_results = cursor.fetchone()[0]

print(f"\nAge Coverage:")
print(f"  Results with day_age: {with_day_age} / {total_results} ({100*with_day_age/total_results:.1f}%)")
print(f"  Results with year_age: {with_year_age} / {total_results} ({100*with_year_age/total_results:.1f}%)")

# Check that each athlete has consistent day_age within each meet
cursor.execute("""
    SELECT 
        a.name as athlete_name,
        m.name as meet_name,
        COUNT(DISTINCT r.day_age) as distinct_day_ages,
        COUNT(*) as result_count
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE r.day_age IS NOT NULL
    GROUP BY a.id, m.id
    HAVING COUNT(DISTINCT r.day_age) > 1
    LIMIT 10
""")

inconsistent = cursor.fetchall()
if inconsistent:
    print(f"\n⚠️  Warning: Found {len(inconsistent)} athlete-meet combinations with inconsistent day_age:")
    for athlete_name, meet_name, distinct_count, result_count in inconsistent:
        print(f"  {athlete_name} in {meet_name}: {distinct_count} different day_age values across {result_count} results")
else:
    print(f"\n✅ All athletes have consistent day_age within each meet (each athlete's day_age is the same for all their results in a meet)")

# Show some examples of athletes with results in multiple meets to verify day_age changes between meets
cursor.execute("""
    SELECT 
        a.name as athlete_name,
        m.name as meet_name,
        m.meet_date,
        r.day_age,
        COUNT(*) as result_count
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE a.id IN (
        SELECT athlete_id 
        FROM results 
        GROUP BY athlete_id 
        HAVING COUNT(DISTINCT meet_id) > 1
        LIMIT 5
    )
    AND r.day_age IS NOT NULL
    GROUP BY a.id, m.id, r.day_age
    ORDER BY a.name, m.meet_date
""")

print(f"\nExample athletes with results in multiple meets (showing day_age changes between meets):")
print("-" * 100)
for row in cursor.fetchall():
    athlete_name, meet_name, meet_date, day_age, result_count = row
    print(f"  {athlete_name:<30} | {meet_name:<35} | {meet_date:<12} | day_age: {day_age} ({result_count} results)")

conn.close()

