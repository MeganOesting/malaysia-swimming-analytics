"""Recalculate day_age and year_age for SEAG athletes' results now that they have birthdates"""
import sqlite3
from datetime import datetime, date

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

print("=" * 100)
print("Recalculating day_age and year_age for SEAG Athletes' Results")
print("=" * 100)

# Get all SEAG results that need age recalculation
cursor.execute("""
    SELECT 
        r.id as result_id,
        a.id as athlete_id,
        a.name as athlete_name,
        a.birth_date,
        m.name as meet_name,
        m.meet_date,
        r.day_age as old_day_age,
        r.year_age as old_year_age
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
    AND a.birth_date IS NOT NULL
    ORDER BY a.name, m.meet_date
""")

results = cursor.fetchall()

updated_count = 0
errors = []

for result_id, athlete_id, athlete_name, birth_date, meet_name, meet_date, old_day_age, old_year_age in results:
    try:
        # Parse birthdate
        if isinstance(birth_date, str):
            birth_date_obj = datetime.strptime(birth_date[:10], '%Y-%m-%d').date()
        else:
            birth_date_obj = birth_date
        
        # Parse meet date
        if isinstance(meet_date, str):
            meet_date_obj = datetime.strptime(meet_date[:10], '%Y-%m-%d').date()
        else:
            meet_date_obj = meet_date
        
        # Calculate day_age: Age on the first day of the meet
        day_age = meet_date_obj.year - birth_date_obj.year
        if (meet_date_obj.month, meet_date_obj.day) < (birth_date_obj.month, birth_date_obj.day):
            day_age -= 1
        
        # Calculate year_age: Age on December 31 of the meet year
        meet_year = meet_date_obj.year
        year_end = date(meet_year, 12, 31)
        year_age = year_end.year - birth_date_obj.year
        if (year_end.month, year_end.day) < (birth_date_obj.month, birth_date_obj.day):
            year_age -= 1
        
        # Update the result
        cursor.execute("""
            UPDATE results
            SET day_age = ?, year_age = ?
            WHERE id = ?
        """, (day_age, year_age, result_id))
        
        updated_count += 1
        
        # Show first few updates
        if updated_count <= 5:
            print(f"✅ {athlete_name} | {meet_name} | day_age: {old_day_age} -> {day_age}, year_age: {old_year_age} -> {year_age}")
    
    except Exception as e:
        errors.append((athlete_name, meet_name, str(e)))

conn.commit()

print(f"\n{'='*100}")
print(f"Update Summary:")
print(f"  Results updated: {updated_count}")
print(f"  Errors: {len(errors)}")

if errors:
    print(f"\nErrors:")
    for athlete_name, meet_name, error in errors[:5]:
        print(f"  {athlete_name} in {meet_name}: {error}")

# Verify all SEAG results now have correct ages
cursor.execute("""
    SELECT 
        COUNT(*) as total_results,
        COUNT(CASE WHEN r.day_age IS NOT NULL THEN 1 END) as with_day_age,
        COUNT(CASE WHEN r.year_age IS NOT NULL THEN 1 END) as with_year_age
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
""")

total_results, with_day_age, with_year_age = cursor.fetchone()

print(f"\n{'='*100}")
print("SEAG Results Age Coverage:")
print(f"  Total SEAG results: {total_results}")
print(f"  With day_age: {with_day_age} ({100*with_day_age/total_results if total_results > 0 else 0:.1f}%)")
print(f"  With year_age: {with_year_age} ({100*with_year_age/total_results if total_results > 0 else 0:.1f}%)")

# Show sample of updated ages
cursor.execute("""
    SELECT 
        a.name,
        a.birth_date,
        m.meet_date,
        r.day_age,
        r.year_age
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
    AND a.birth_date IS NOT NULL
    GROUP BY a.id, m.id
    ORDER BY a.name
    LIMIT 10
""")

print(f"\n{'='*100}")
print("Sample Updated SEAG Athletes:")
print(f"{'Athlete Name':<35} | {'Birth Date':<12} | {'Meet Date':<12} | {'Day Age':<8} | {'Year Age':<9}")
print("-" * 100)
for row in cursor.fetchall():
    name, birth_date, meet_date, day_age, year_age = row
    print(f"{name:<35} | {birth_date or 'N/A':<12} | {meet_date or 'N/A':<12} | {day_age or 'N/A':<8} | {year_age or 'N/A':<9}")

conn.close()












