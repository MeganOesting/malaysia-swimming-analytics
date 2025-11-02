import sqlite3

conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()

print('=== SUKMA 2024 DATA VERIFICATION ===')
print()

# Get all SUKMA meet IDs that have results
cursor.execute("""
    SELECT m.id, m.name, COUNT(r.id) as result_count
    FROM meets m
    JOIN results r ON m.id = r.meet_id
    WHERE m.name LIKE '%SUKMA%'
    GROUP BY m.id, m.name
    ORDER BY result_count DESC
""")

sukma_meets_with_results = cursor.fetchall()
print('SUKMA meets with results:')
for meet in sukma_meets_with_results:
    print(f'  ID: {meet[0]} - {meet[1]} - {meet[2]} results')
print()

# Get SUKMA results from the meet with most results
if sukma_meets_with_results:
    sukma_meet_id = sukma_meets_with_results[0][0]  # Use the one with most results
    
    cursor.execute("""
        SELECT 
            a.name, a.gender, r.age, e.distance, e.stroke, 
            r.time_string, r.place, r.aqua_points
        FROM results r
        JOIN athletes a ON r.athlete_id = a.id
        JOIN events e ON r.event_id = e.id
        WHERE r.meet_id = ?
        ORDER BY e.distance, e.stroke, r.place
        LIMIT 20
    """, (sukma_meet_id,))
    
    sukma_results = cursor.fetchall()
    print(f'SUKMA 2024 results (first 20):')
    for result in sukma_results:
        print(f'  {result[0]} ({result[1]}, {result[2]}) - {result[3]}m {result[4]} - {result[5]} - Place: {result[6]} - AQUA: {result[7]}')
    print()
    
    # Check unique events in SUKMA
    cursor.execute("""
        SELECT DISTINCT e.distance, e.stroke, COUNT(*) as count
        FROM results r
        JOIN events e ON r.event_id = e.id
        WHERE r.meet_id = ?
        GROUP BY e.distance, e.stroke
        ORDER BY e.distance, e.stroke
    """, (sukma_meet_id,))
    
    events = cursor.fetchall()
    print('SUKMA events with counts:')
    for event in events:
        print(f'  {event[0]}m {event[1]}: {event[2]} results')
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



