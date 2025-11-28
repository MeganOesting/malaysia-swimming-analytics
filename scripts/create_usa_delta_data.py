"""
Create and populate usa_delta_data table from USA Delta Data CSV files.

Table schema:
- usa_delta_event_id: TEXT (e.g., LCM_Back_100_F)
- usa_athlete_id: INTEGER (foreign key to usa_athlete)
- usa_delta_age_start: INTEGER
- usa_delta_age_end: INTEGER
- usa_delta_time_start: REAL
- usa_delta_time_end: REAL
- usa_delta_improvement_seconds: REAL
- usa_delta_improvement_percentage: REAL
- usa_delta_rank_start: INTEGER
- usa_delta_rank_end: INTEGER

Data source: statistical_analysis/USA Data/USA Delta Data/
"""

import sqlite3
import os
import re
import csv

# Paths
BASE_PATH = r"C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
DB_PATH = os.path.join(BASE_PATH, "malaysia_swimming.db")
DATA_PATH = os.path.join(BASE_PATH, "statistical_analysis", "USA Data", "USA Delta Data")

# Stroke mapping from filename to event_id format
STROKE_MAP = {
    "Back": "Back",
    "Breast": "Breast",
    "Fly": "Fly",
    "Free": "Free",
    "IM": "Medley"
}


def create_table(conn):
    """Create the usa_delta_data table."""
    cur = conn.cursor()

    # Drop if exists
    cur.execute("DROP TABLE IF EXISTS usa_delta_data")

    # Create table
    cur.execute("""
        CREATE TABLE usa_delta_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usa_delta_event_id TEXT NOT NULL,
            usa_athlete_id INTEGER NOT NULL,
            usa_delta_age_start INTEGER NOT NULL,
            usa_delta_age_end INTEGER NOT NULL,
            usa_delta_time_start REAL NOT NULL,
            usa_delta_time_end REAL NOT NULL,
            usa_delta_improvement_seconds REAL NOT NULL,
            usa_delta_improvement_percentage REAL NOT NULL,
            usa_delta_rank_start INTEGER,
            usa_delta_rank_end INTEGER,
            FOREIGN KEY (usa_athlete_id) REFERENCES usa_athlete(usa_athlete_id)
        )
    """)

    # Create indexes for faster lookups
    cur.execute("CREATE INDEX idx_usa_delta_athlete ON usa_delta_data(usa_athlete_id)")
    cur.execute("CREATE INDEX idx_usa_delta_event ON usa_delta_data(usa_delta_event_id)")

    conn.commit()
    print("[OK] Created usa_delta_data table")


def parse_filename(filename):
    """
    Parse filename to extract gender, distance, stroke.

    Example: "F 100 Back 15 to 16 Athlete_Improvement_Data.csv"
    Returns: ('F', 100, 'Back')
    """
    # Pattern: G DIST STROKE AGE to AGE ...
    pattern = r'^([FM])\s+(\d+)\s+(\w+)\s+\d+\s+to\s+\d+'
    match = re.match(pattern, filename)

    if not match:
        print(f"  [WARNING] Could not parse filename: {filename}")
        return None

    gender = match.group(1)
    distance = int(match.group(2))
    stroke = match.group(3)

    return (gender, distance, stroke)


def build_event_id(gender, distance, stroke):
    """
    Build event_id from components.

    Example: ('F', 100, 'Back') -> 'LCM_Back_100_F'
    """
    stroke_normalized = STROKE_MAP.get(stroke, stroke)
    return f"LCM_{stroke_normalized}_{distance}_{gender}"


def load_athletes(conn):
    """Load all athletes into a lookup dict keyed by (name, gender)."""
    cur = conn.cursor()
    cur.execute("SELECT usa_athlete_id, usa_name, usa_gender FROM usa_athlete")

    athletes = {}
    for row in cur.fetchall():
        usa_id, name, gender = row
        key = (name.lower().strip(), gender)
        athletes[key] = usa_id

    print(f"[OK] Loaded {len(athletes)} athletes from usa_athlete table")
    return athletes


def process_csv(filepath, athletes, event_id, gender):
    """
    Process a single CSV file and return list of records.

    Returns: list of tuples and list of unmatched names
    """
    records = []
    unmatched = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                name = row['name'].strip()

                # Look up athlete by name and gender
                key = (name.lower().strip(), gender)
                athlete_id = athletes.get(key)

                if athlete_id is None:
                    unmatched.append((name, gender))
                    continue

                # Parse fields
                age_start = int(row['age_from'])
                age_end = int(row['age_to'])
                time_start = float(row['time_from'])
                time_end = float(row['time_to'])
                improvement_seconds = float(row['improvement_seconds'])
                improvement_percentage = float(row['improvement_percentage'])

                # Rank fields might be empty
                rank_start = int(row['rank_from']) if row['rank_from'].strip() else None
                rank_end = int(row['rank_to']) if row['rank_to'].strip() else None

                records.append((
                    event_id,
                    athlete_id,
                    age_start,
                    age_end,
                    time_start,
                    time_end,
                    improvement_seconds,
                    improvement_percentage,
                    rank_start,
                    rank_end
                ))

            except (ValueError, KeyError) as e:
                continue

    return records, unmatched


def main():
    print("=" * 60)
    print("Creating usa_delta_data table")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # Create table
    create_table(conn)

    # Load athletes
    athletes = load_athletes(conn)

    # Process all files
    all_records = []
    all_unmatched = []
    file_count = 0

    # Walk through all delta folders
    for folder in sorted(os.listdir(DATA_PATH)):
        folder_path = os.path.join(DATA_PATH, folder)
        if not os.path.isdir(folder_path):
            continue

        # Find CSV file in folder
        for filename in os.listdir(folder_path):
            if not filename.endswith('.csv'):
                continue

            filepath = os.path.join(folder_path, filename)

            # Parse filename
            parsed = parse_filename(filename)
            if parsed is None:
                continue

            gender, distance, stroke = parsed
            event_id = build_event_id(gender, distance, stroke)

            # Process file
            records, unmatched = process_csv(filepath, athletes, event_id, gender)
            all_records.extend(records)
            all_unmatched.extend(unmatched)
            file_count += 1

    print(f"\n[OK] Processed {file_count} CSV files")
    print(f"[OK] Found {len(all_records)} records to insert")
    print(f"[WARNING] {len(all_unmatched)} records could not be matched to athletes")

    # Show sample unmatched
    if all_unmatched:
        unique_unmatched = list(set(all_unmatched))[:10]
        print("\nSample unmatched athletes:")
        for name, gender in unique_unmatched:
            print(f"  - {name} ({gender})")

    # Insert records
    if all_records:
        cur = conn.cursor()
        cur.executemany("""
            INSERT INTO usa_delta_data (
                usa_delta_event_id,
                usa_athlete_id,
                usa_delta_age_start,
                usa_delta_age_end,
                usa_delta_time_start,
                usa_delta_time_end,
                usa_delta_improvement_seconds,
                usa_delta_improvement_percentage,
                usa_delta_rank_start,
                usa_delta_rank_end
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, all_records)
        conn.commit()
        print(f"\n[OK] Inserted {len(all_records)} records into usa_delta_data")

    # Verify
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usa_delta_data")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT usa_athlete_id) FROM usa_delta_data")
    unique_athletes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT usa_delta_event_id) FROM usa_delta_data")
    unique_events = cur.fetchone()[0]

    print(f"\n" + "=" * 60)
    print(f"SUMMARY")
    print(f"=" * 60)
    print(f"Total records: {total}")
    print(f"Unique athletes: {unique_athletes}")
    print(f"Unique events: {unique_events}")

    # Sample data
    print(f"\nSample records:")
    cur.execute("""
        SELECT d.usa_delta_event_id, a.usa_name,
               d.usa_delta_age_start, d.usa_delta_age_end,
               d.usa_delta_time_start, d.usa_delta_time_end,
               d.usa_delta_improvement_seconds, d.usa_delta_improvement_percentage
        FROM usa_delta_data d
        JOIN usa_athlete a ON d.usa_athlete_id = a.usa_athlete_id
        LIMIT 5
    """)
    for row in cur.fetchall():
        event, name, age_s, age_e, time_s, time_e, imp_sec, imp_pct = row
        print(f"  {event}: {name} ({age_s}->{age_e}) {time_s:.2f}->{time_e:.2f} ({imp_sec:+.2f}s, {imp_pct:+.2f}%)")

    conn.close()
    print("\n[OK] Done!")


if __name__ == "__main__":
    main()
