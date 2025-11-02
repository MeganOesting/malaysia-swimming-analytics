import sqlite3

conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()

print('=== ALL MEETS DATA VERIFICATION ===')
print()

# Check all meets and their result counts
cursor.execute("""
    SELECT m.id, m.name, m.meet_type, m.meet_date, COUNT(r.id) as result_count
    FROM meets m
    LEFT JOIN results r ON m.id = r.meet_id
    GROUP BY m.id, m.name, m.meet_type, m.meet_date
    ORDER BY result_count DESC
""")

meets_with_counts = cursor.fetchall()
print('All meets with result counts:')
for meet in meets_with_counts:
    print(f'  {meet[1]} ({meet[2]}) - {meet[4]} results - Date: {meet[3]}')
print()

# Check which meets have the most results
cursor.execute("""
    SELECT m.name, COUNT(r.id) as result_count
    FROM meets m
    JOIN results r ON m.id = r.meet_id
    GROUP BY m.name
    ORDER BY result_count DESC
    LIMIT 10
""")

top_meets = cursor.fetchall()
print('Top meets by result count:')
for meet in top_meets:
    print(f'  {meet[0]}: {meet[1]} results')
print()

# Check total results count
cursor.execute("SELECT COUNT(*) FROM results")
total_results = cursor.fetchone()[0]
print(f'Total results in database: {total_results}')
print()

# Check sample results with meet names
cursor.execute("""
    SELECT 
        a.name, a.gender, r.age, e.distance, e.stroke, 
        r.time_string, r.place, r.aqua_points, m.name as meet_name
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN events e ON r.event_id = e.id
    JOIN meets m ON r.meet_id = m.id
    LIMIT 10
""")

sample_results = cursor.fetchall()
print('Sample results from all meets:')
for result in sample_results:
    print(f'  {result[0]} ({result[1]}, {result[2]}) - {result[3]}m {result[4]} - {result[5]} - Place: {result[6]} - AQUA: {result[7]} - Meet: {result[8]}')
print()

conn.close()



