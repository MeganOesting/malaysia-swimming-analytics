"""Update remaining SEAG athletes with birthdates"""
import sqlite3
from datetime import datetime

# Remaining athletes with their birthdates (DD/MM/YYYY format)
REMAINING_ATHLETES = [
    ('CHEREEN NGO YIRUI', '18/09/2010'),
    ('DYLAN LEONG YI QUAN', '19/06/2009'),
    ('HO WEI YAN', 'Megan Ho'),  # Need to find as "Megan Ho"
    ('MUHAMMAD IRIEL DARWISH LIM', '16/04/2012'),
    ('NADIA LIM', '11/11/2010'),
    ('SEAH SHU HUI', '24/06/2009'),
]

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

print("=" * 100)
print("Updating Remaining SEAG Athletes with Birthdates")
print("=" * 100)

# First, handle HO WEI YAN - need to find "Megan Ho" in athleteinfo
cursor.execute("""
    SELECT name, birthdate
    FROM athleteinfo
    WHERE UPPER(name) LIKE '%MEGAN%HO%' OR UPPER(name) LIKE '%HO%MEGAN%'
""")
megan_ho = cursor.fetchone()
if megan_ho:
    print(f"Found Megan Ho: {megan_ho[0]} - Birthdate: {megan_ho[1]}")
    # Update the birthdate for HO WEI YAN
    for i, (name, bdate) in enumerate(REMAINING_ATHLETES):
        if name == 'HO WEI YAN':
            REMAINING_ATHLETES[i] = ('HO WEI YAN', megan_ho[1])
            break

updated_count = 0
not_found = []

for seag_name, birthdate_str in REMAINING_ATHLETES:
    # Convert DD/MM/YYYY to YYYY-MM-DD
    if '/' in birthdate_str:
        try:
            bdate_obj = datetime.strptime(birthdate_str, '%d/%m/%Y')
            birthdate_iso = bdate_obj.strftime('%Y-%m-%d')
        except:
            # If it's already in ISO format (from Megan Ho lookup)
            birthdate_iso = birthdate_str
    else:
        birthdate_iso = birthdate_str
    
    # Find the SEAG athlete
    cursor.execute("""
        SELECT DISTINCT a.id, a.name
        FROM athletes a
        JOIN results r ON a.id = r.athlete_id
        JOIN meets m ON r.meet_id = m.id
        WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
        AND UPPER(a.name) = UPPER(?)
        AND a.birth_date IS NULL
    """, (seag_name,))
    
    result = cursor.fetchone()
    if result:
        athlete_id, current_name = result
        cursor.execute("""
            UPDATE athletes 
            SET birth_date = ?
            WHERE id = ?
        """, (birthdate_iso, athlete_id))
        updated_count += 1
        print(f"✅ Updated: {current_name} -> {birthdate_iso}")
    else:
        # Try case-insensitive search
        cursor.execute("""
            SELECT DISTINCT a.id, a.name
            FROM athletes a
            JOIN results r ON a.id = r.athlete_id
            JOIN meets m ON r.meet_id = m.id
            WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
            AND UPPER(REPLACE(a.name, ' ', '')) = UPPER(REPLACE(?, ' ', ''))
            AND a.birth_date IS NULL
        """, (seag_name,))
        
        result = cursor.fetchone()
        if result:
            athlete_id, current_name = result
            cursor.execute("""
                UPDATE athletes 
                SET birth_date = ?
                WHERE id = ?
            """, (birthdate_iso, athlete_id))
            updated_count += 1
            print(f"✅ Updated: {current_name} -> {birthdate_iso}")
        else:
            not_found.append(seag_name)
            print(f"⚠️  Not found: {seag_name}")

conn.commit()

print(f"\n{'='*100}")
print(f"Update Summary:")
print(f"  Updated: {updated_count} athletes")
print(f"  Not found: {len(not_found)}")

if not_found:
    print(f"\nNot found athletes:")
    for name in not_found:
        print(f"  - {name}")

# Verify all SEAG athletes now have birthdates
print(f"\n{'='*100}")
print("Verifying SEAG Athletes:")
print("=" * 100)

cursor.execute("""
    SELECT COUNT(DISTINCT a.id) as total_seag,
           COUNT(DISTINCT CASE WHEN a.birth_date IS NOT NULL THEN a.id END) as with_birthdate
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
""")

total_seag, with_birthdate = cursor.fetchone()
print(f"\nSEAG Athletes:")
print(f"  Total: {total_seag}")
print(f"  With birthdates: {with_birthdate}")
print(f"  Coverage: {100*with_birthdate/total_seag if total_seag > 0 else 0:.1f}%")

# Show remaining if any
cursor.execute("""
    SELECT DISTINCT a.name
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
    AND a.birth_date IS NULL
    ORDER BY a.name
""")

remaining = cursor.fetchall()
if remaining:
    print(f"\n⚠️  Still missing birthdates ({len(remaining)}):")
    for (name,) in remaining:
        print(f"  - {name}")
else:
    print(f"\n✅ All SEAG athletes now have birthdates!")

conn.close()


