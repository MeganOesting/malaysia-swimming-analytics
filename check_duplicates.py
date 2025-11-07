import sqlite3

conn = sqlite3.connect('malaysia_swimming.db')
c = conn.cursor()

# Check if UNIQUE index exists
c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_results_unique'")
idx = c.fetchone()
print("UNIQUE index exists:", idx is not None)
if idx:
    print("Index SQL:", idx[0])

# Check for NULL time_seconds
c.execute("SELECT COUNT(*) FROM results WHERE time_seconds IS NULL")
print("Results with NULL time_seconds:", c.fetchone()[0])

# Check SUKMA meet results
c.execute("SELECT id FROM meets WHERE name LIKE '%Sukan Malaysia%' LIMIT 1")
meet_row = c.fetchone()
if meet_row:
    meet_id = meet_row[0]
    c.execute("SELECT COUNT(*) FROM results WHERE meet_id = ?", (meet_id,))
    print(f"Total results for SUKMA meet: {c.fetchone()[0]}")
    
    # Check for exact duplicates
    c.execute("""
        SELECT meet_id, event_id, athlete_id, time_seconds, COUNT(*) as cnt
        FROM results 
        WHERE meet_id = ?
        GROUP BY meet_id, event_id, athlete_id, time_seconds
        HAVING COUNT(*) > 1
        LIMIT 5
    """, (meet_id,))
    dupes = c.fetchall()
    print(f"Duplicate groups found: {len(dupes)}")
    if dupes:
        print("Sample duplicates:", dupes[:3])

conn.close()
