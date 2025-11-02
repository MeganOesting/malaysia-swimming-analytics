import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Check if SEAG meet IDs have any results
cursor.execute("SELECT id FROM meets WHERE name = 'SEA Age 2025' LIMIT 1")
seag_meet_ids = [row[0] for row in cursor.fetchall()]

if seag_meet_ids:
    seag_id = seag_meet_ids[0]
    cursor.execute("SELECT COUNT(*) FROM results WHERE meet_id = ?", (seag_id,))
    result_count = cursor.fetchone()[0]
    print(f"Results for 'SEA Age 2025' meet ID {seag_id[:8]}...: {result_count}")
    
    if result_count == 0:
        print("\nNo results linked to 'SEA Age 2025' meets!")
        print("Checking if SEAG results are linked to different meet names...")
        
        # Check what meet IDs actually have results
        cursor.execute("""
            SELECT DISTINCT m.id, m.name, COUNT(r.id) as result_count
            FROM meets m
            LEFT JOIN results r ON m.id = r.meet_id
            GROUP BY m.id, m.name
            HAVING result_count > 0
            ORDER BY result_count DESC
            LIMIT 10
        """)
        print("\nTop 10 meets by result count:")
        for meet_id, name, count in cursor.fetchall():
            print(f"  {meet_id[:8]}... {name}: {count} results")
else:
    print("No 'SEA Age 2025' meets found")

# Also check the actual SEAG file processing - maybe results are under different meet names
print("\n" + "="*60)
print("Checking for results with SEAG-related keywords in athlete names or other fields...")

# Check if any results have athlete names that might indicate SEAG
cursor.execute("""
    SELECT COUNT(*) FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    WHERE a.nation != 'MAS' AND a.nation IS NOT NULL
    LIMIT 1000
""")
foreign_results = cursor.fetchone()[0]
print(f"Results with non-Malaysian athletes: {foreign_results}")

conn.close()




