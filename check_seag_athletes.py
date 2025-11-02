import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# List all meets
cursor.execute("SELECT DISTINCT id, name, meet_date FROM meets ORDER BY name")
all_meets = cursor.fetchall()
print('All meets in database:')
for m in all_meets:
    print(f'  {m[0][:8]}... {m[1]} ({m[2]})')

print('\n' + '='*60)

# Find SEAG meets
cursor.execute("""
    SELECT id, name, meet_date 
    FROM meets 
    WHERE name LIKE '%SEAG%' 
       OR name LIKE '%Southeast%' 
       OR name LIKE '%Singapore%'
       OR name LIKE '%47th%'
    ORDER BY name
""")
meets = cursor.fetchall()
print('SEAG-related meets:')
for m in meets:
    print(f'  ID: {m[0][:8]}..., Name: {m[1]}, Date: {m[2]}')

# Count athletes in SEAG meets
cursor.execute("""
    SELECT COUNT(DISTINCT athlete_id) 
    FROM results 
    WHERE meet_id IN (
        SELECT id FROM meets 
        WHERE name LIKE '%SEAG%' 
           OR name LIKE '%Southeast%' 
           OR name LIKE '%Singapore%'
           OR name LIKE '%Age Group%'
    )
""")
count = cursor.fetchone()[0]
print(f'\nTotal athletes in SEAG-related meets: {count}')

# Check SEAG specifically
cursor.execute("""
    SELECT COUNT(DISTINCT r.athlete_id) 
    FROM results r
    WHERE r.meet_id IN (
        SELECT id FROM meets WHERE name = 'SEA Age 2025'
    )
""")
seag_total = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT r.athlete_id) 
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    WHERE r.meet_id IN (
        SELECT id FROM meets WHERE name = 'SEA Age 2025'
    )
    AND a.birth_date IS NOT NULL 
    AND a.birth_date != ''
""")
seag_with_birthdate = cursor.fetchone()[0]

print(f'\nSEA Age 2025 (SEAG) specific:')
print(f'  Total athletes: {seag_total}')
if seag_total > 0:
    print(f'  With birthdates: {seag_with_birthdate}/{seag_total} ({seag_with_birthdate/seag_total*100:.1f}%)')
else:
    print(f'  With birthdates: {seag_with_birthdate} (No SEAG athletes found - check meet name)')

# Show sample SEAG athletes without birthdates
cursor.execute("""
    SELECT DISTINCT a.name, a.nation, a.is_foreign
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    WHERE r.meet_id IN (
        SELECT id FROM meets WHERE name = 'SEA Age 2025'
    )
    AND (a.birth_date IS NULL OR a.birth_date = '')
    LIMIT 10
""")
no_birthdate = cursor.fetchall()
print(f'\nSample SEAG athletes WITHOUT birthdates (first 10):')
for name, nation, is_foreign in no_birthdate:
    print(f'  {name} (Nation: {nation}, Foreign: {is_foreign})')

# Check how many are Malaysian vs Foreign
cursor.execute("""
    SELECT COUNT(DISTINCT a.id)
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    WHERE r.meet_id IN (
        SELECT id FROM meets WHERE name = 'SEA Age 2025'
    )
    AND a.is_foreign = 0
""")
malaysian_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(DISTINCT a.id)
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    WHERE r.meet_id IN (
        SELECT id FROM meets WHERE name = 'SEA Age 2025'
    )
    AND a.is_foreign = 1
""")
foreign_count = cursor.fetchone()[0]

print(f'\nSEAG athlete breakdown:')
print(f'  Malaysian athletes: {malaysian_count}')
print(f'  Foreign athletes: {foreign_count}')

conn.close()

