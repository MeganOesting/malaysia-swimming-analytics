import sqlite3

conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()

print('=== SUKMA DATA VERIFICATION (PROPER SCHEMA) ===')
print()

# Find SUKMA meet by name
cursor.execute("SELECT id, name, meet_type, meet_date, location FROM meets WHERE name LIKE '%SUKMA%' OR name LIKE '%Sukma%'")
sukma_meets = cursor.fetchall()
print('SUKMA meets in database:')
for meet in sukma_meets:
    print(f'  ID: {meet[0]}')
    print(f'  Name: {meet[1]}')
    print(f'  Type: {meet[2]}')
    print(f'  Date: {meet[3]}')
    print(f'  Location: {meet[4]}')
    print()

# Get SUKMA results with joins
if sukma_meets:
    sukma_meet_id = sukma_meets[0][0]  # Use first SUKMA meet
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM results r 
        WHERE r.meet_id = ?
    """, (sukma_meet_id,))
    sukma_count = cursor.fetchone()[0]
    print(f'SUKMA results count: {sukma_count}')
    print()
    
    # Sample SUKMA results with joins
    cursor.execute("""
        SELECT 
            a.name, a.gender, r.age, e.distance, e.stroke, 
            r.time_string, r.place, r.aqua_points, m.name as meet_name
        FROM results r
        JOIN athletes a ON r.athlete_id = a.id
        JOIN events e ON r.event_id = e.id
        JOIN meets m ON r.meet_id = m.id
        WHERE r.meet_id = ?
        LIMIT 10
    """, (sukma_meet_id,))
    
    sample_results = cursor.fetchall()
    print('Sample SUKMA results:')
    for result in sample_results:
        print(f'  {result[0]} ({result[1]}, {result[2]}) - {result[3]}m {result[4]} - {result[5]} - Place: {result[6]} - AQUA: {result[7]}')
    print()
    
    # Check unique events in SUKMA
    cursor.execute("""
        SELECT DISTINCT e.distance, e.stroke 
        FROM results r
        JOIN events e ON r.event_id = e.id
        WHERE r.meet_id = ?
        ORDER BY e.distance, e.stroke
    """, (sukma_meet_id,))
    
    events = cursor.fetchall()
    print('SUKMA events:')
    for event in events:
        print(f'  {event[0]}m {event[1]}')
    print()
    
    # Check gender distribution
    cursor.execute("""
        SELECT a.gender, COUNT(*) 
        FROM results r
        JOIN athletes a ON r.athlete_id = a.id
        WHERE r.meet_id = ?
        GROUP BY a.gender
    """, (sukma_meet_id,))
    
    gender_dist = cursor.fetchall()
    print('SUKMA gender distribution:')
    for gender, count in gender_dist:
        print(f'  {gender}: {count} results')
    print()
    
    # Check age distribution
    cursor.execute("""
        SELECT r.age, COUNT(*) 
        FROM results r
        WHERE r.meet_id = ?
        GROUP BY r.age 
        ORDER BY r.age
    """, (sukma_meet_id,))
    
    age_dist = cursor.fetchall()
    print('SUKMA age distribution:')
    for age, count in age_dist:
        print(f'  Age {age}: {count} results')
    print()

conn.close()



