import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Test the exact query from the API
cursor.execute("PRAGMA table_info(meets)")
columns = [col[1] for col in cursor.fetchall()]
has_meet_date = 'meet_date' in columns
print(f"meet_date column exists: {has_meet_date}")

if has_meet_date:
    query = """
    SELECT 
        a.name,
        a.gender,
        r.age,
        e.distance,
        e.stroke,
        r.time_string,
        r.place,
        r.aqua_points,
        m.id as meet_id,
        m.name as meet_name,
        m.meet_type as meet_code
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN events e ON r.event_id = e.id
    JOIN meets m ON r.meet_id = m.id
    ORDER BY m.meet_date DESC, e.distance, e.stroke, COALESCE(r.time_seconds, 999999)
    LIMIT 5
    """
else:
    query = """
    SELECT 
        a.name,
        a.gender,
        r.age,
        e.distance,
        e.stroke,
        r.time_string,
        r.place,
        r.aqua_points,
        m.id as meet_id,
        m.name as meet_name,
        m.meet_type as meet_code
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN events e ON r.event_id = e.id
    JOIN meets m ON r.meet_id = m.id
    ORDER BY e.distance, e.stroke, COALESCE(r.time_seconds, 999999)
    LIMIT 5
    """

try:
    cursor.execute(query)
    results = cursor.fetchall()
    print(f"\nQuery returned {len(results)} rows")
    if results:
        print("\nFirst 5 results:")
        for row in results:
            print(f"  {row[0]} ({row[1]}) - {row[3]}m {row[4]} - Meet: {row[9]}")
    else:
        print("\nNo results returned!")
        # Check if JOINs are the problem
        cursor.execute("SELECT COUNT(*) FROM results")
        total_results = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM athletes")
        total_athletes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM meets")
        total_meets = cursor.fetchone()[0]
        print(f"Total in tables: results={total_results}, athletes={total_athletes}, events={total_events}, meets={total_meets}")
        
        # Check for orphaned results
        cursor.execute("SELECT COUNT(*) FROM results r LEFT JOIN athletes a ON r.athlete_id = a.id WHERE a.id IS NULL")
        orphaned_athletes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM results r LEFT JOIN events e ON r.event_id = e.id WHERE e.id IS NULL")
        orphaned_events = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM results r LEFT JOIN meets m ON r.meet_id = m.id WHERE m.id IS NULL")
        orphaned_meets = cursor.fetchone()[0]
        print(f"Orphaned: athletes={orphaned_athletes}, events={orphaned_events}, meets={orphaned_meets}")
except Exception as e:
    print(f"\nError executing query: {e}")
    import traceback
    traceback.print_exc()

conn.close()












