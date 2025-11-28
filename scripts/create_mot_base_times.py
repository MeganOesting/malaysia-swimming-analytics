"""
Create mot_base_times table.

Table schema:
- mot_event_id: TEXT (e.g., LCM_Back_100_F)
- mot_age: INTEGER (15-23)
- mot_time_seconds: REAL

Age 23 always gets the podium_target_time from the most recent sea_games_year.
Ages 15-22 are NULL for now (to be populated later).
"""

import sqlite3
import os

# Paths
BASE_PATH = r"C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
DB_PATH = os.path.join(BASE_PATH, "malaysia_swimming.db")


def main():
    print("=" * 60)
    print("Creating mot_base_times table")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Drop if exists
    cur.execute("DROP TABLE IF EXISTS mot_base_times")

    # Create table
    cur.execute("""
        CREATE TABLE mot_base_times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot_event_id TEXT NOT NULL,
            mot_age INTEGER NOT NULL,
            mot_time_seconds REAL,
            UNIQUE(mot_event_id, mot_age)
        )
    """)
    print("[OK] Created mot_base_times table")

    # Create index
    cur.execute("CREATE INDEX idx_mot_event ON mot_base_times(mot_event_id)")
    cur.execute("CREATE INDEX idx_mot_age ON mot_base_times(mot_age)")

    # Get all LCM events
    cur.execute("SELECT id FROM events WHERE event_course = 'LCM' ORDER BY id")
    events = [row[0] for row in cur.fetchall()]
    print(f"[OK] Found {len(events)} LCM events")

    # Get most recent year from podium_target_times
    cur.execute("SELECT MAX(sea_games_year) FROM podium_target_times")
    most_recent_year = cur.fetchone()[0]
    print(f"[OK] Most recent podium target year: {most_recent_year}")

    # Get podium target times for most recent year
    cur.execute("""
        SELECT event_id, target_time_seconds
        FROM podium_target_times
        WHERE sea_games_year = ?
    """, (most_recent_year,))
    podium_times = {row[0]: row[1] for row in cur.fetchall()}
    print(f"[OK] Loaded {len(podium_times)} podium target times")

    # Insert rows for each event and age 15-23
    ages = [15, 16, 17, 18, 19, 20, 21, 22, 23]
    insert_count = 0

    for event_id in events:
        for age in ages:
            if age == 23:
                # Use podium target time for age 23
                time_seconds = podium_times.get(event_id)
            else:
                # NULL for other ages (to be populated later)
                time_seconds = None

            cur.execute("""
                INSERT INTO mot_base_times (mot_event_id, mot_age, mot_time_seconds)
                VALUES (?, ?, ?)
            """, (event_id, age, time_seconds))
            insert_count += 1

    conn.commit()
    print(f"[OK] Inserted {insert_count} rows")

    # Verify
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    cur.execute("SELECT COUNT(*) FROM mot_base_times")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT mot_event_id) FROM mot_base_times")
    unique_events = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mot_base_times WHERE mot_time_seconds IS NOT NULL")
    with_times = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mot_base_times WHERE mot_time_seconds IS NULL")
    without_times = cur.fetchone()[0]

    print(f"Total rows: {total}")
    print(f"Unique events: {unique_events}")
    print(f"Rows with times (age 23): {with_times}")
    print(f"Rows without times (ages 15-22): {without_times}")

    # Sample data - age 23 with podium times
    print(f"\nSample age 23 records (with podium target times):")
    cur.execute("""
        SELECT mot_event_id, mot_age, mot_time_seconds
        FROM mot_base_times
        WHERE mot_age = 23 AND mot_time_seconds IS NOT NULL
        ORDER BY mot_event_id
        LIMIT 10
    """)
    for row in cur.fetchall():
        event, age, time_sec = row
        mins = int(time_sec // 60)
        secs = time_sec % 60
        if mins > 0:
            time_str = f"{mins}:{secs:05.2f}"
        else:
            time_str = f"{secs:.2f}"
        print(f"  {event} age {age}: {time_sec} ({time_str})")

    # Check for events without podium times at age 23
    cur.execute("""
        SELECT mot_event_id FROM mot_base_times
        WHERE mot_age = 23 AND mot_time_seconds IS NULL
    """)
    missing = cur.fetchall()
    if missing:
        print(f"\n[WARNING] Events without podium target times at age 23:")
        for row in missing:
            print(f"  {row[0]}")

    conn.close()
    print("\n[OK] Done!")


if __name__ == "__main__":
    main()
