"""
Create and populate usa_raw_period_data table from USA Swimming period data files.

Table schema:
- usa_raw_event_id: TEXT (e.g., LCM_Back_100_F)
- usa_raw_year: INTEGER (e.g., 2025)
- usa_athlete_id: INTEGER (foreign key to usa_athlete)
- usa_raw_time_seconds: REAL

Data source: statistical_analysis/USA Data/USA Period Data/
"""

import sqlite3
import os
import re

# Paths
BASE_PATH = r"C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
DB_PATH = os.path.join(BASE_PATH, "malaysia_swimming.db")
DATA_PATH = os.path.join(BASE_PATH, "statistical_analysis", "USA Data", "USA Period Data")

# Stroke mapping from filename to event_id format
STROKE_MAP = {
    "Back": "Back",
    "Breast": "Breast",
    "Fly": "Fly",
    "Free": "Free",
    "IM": "Medley"
}


def create_table(conn):
    """Create the usa_raw_period_data table."""
    cur = conn.cursor()

    # Drop if exists
    cur.execute("DROP TABLE IF EXISTS usa_raw_period_data")

    # Create table
    cur.execute("""
        CREATE TABLE usa_raw_period_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usa_raw_event_id TEXT NOT NULL,
            usa_raw_year INTEGER NOT NULL,
            usa_athlete_id INTEGER NOT NULL,
            usa_raw_time_seconds REAL NOT NULL,
            FOREIGN KEY (usa_athlete_id) REFERENCES usa_athlete(usa_athlete_id)
        )
    """)

    # Create index for faster lookups
    cur.execute("CREATE INDEX idx_usa_raw_athlete ON usa_raw_period_data(usa_athlete_id)")
    cur.execute("CREATE INDEX idx_usa_raw_event ON usa_raw_period_data(usa_raw_event_id)")
    cur.execute("CREATE INDEX idx_usa_raw_year ON usa_raw_period_data(usa_raw_year)")

    conn.commit()
    print("[OK] Created usa_raw_period_data table")


def parse_filename(filename):
    """
    Parse filename to extract gender, distance, stroke, age, year.

    Example: "F 100 Back 15 9.1.24-8.31.25.txt"
    Returns: ('F', 100, 'Back', 15, 2025)
    """
    # Remove .txt extension
    name = filename.replace('.txt', '')

    # Pattern: G DIST STROKE AGE PERIOD
    # Example: F 100 Back 15 9.1.24-8.31.25
    pattern = r'^([FM])\s+(\d+)\s+(\w+)\s+(\d+)\s+[\d.]+-([\d.]+)$'
    match = re.match(pattern, name)

    if not match:
        print(f"  [WARNING] Could not parse filename: {filename}")
        return None

    gender = match.group(1)
    distance = int(match.group(2))
    stroke = match.group(3)
    age = int(match.group(4))

    # Extract year from end date (e.g., "8.31.25" -> 2025)
    end_date = match.group(5)
    year_short = int(end_date.split('.')[-1])
    year = 2000 + year_short

    return (gender, distance, stroke, age, year)


def build_event_id(gender, distance, stroke):
    """
    Build event_id from components.

    Example: ('F', 100, 'Back') -> 'LCM_Back_100_F'
    """
    stroke_normalized = STROKE_MAP.get(stroke, stroke)
    return f"LCM_{stroke_normalized}_{distance}_{gender}"


def parse_time_string(time_str):
    """
    Parse swim time string to seconds.

    Examples:
    - "59.67" -> 59.67
    - "1:00.43" -> 60.43
    - "1:02.52r" -> 62.52 (strip suffix)
    - "15:23.45" -> 923.45
    """
    # Remove any trailing letters (r for relay leadoff, etc.)
    time_str = re.sub(r'[a-zA-Z]+$', '', time_str.strip())

    if ':' in time_str:
        # Format: MM:SS.ss or M:SS.ss
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    else:
        # Format: SS.ss
        return float(time_str)


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


def process_file(filepath, athletes, year, event_id, age):
    """
    Process a single data file and return list of records.

    Returns: list of (event_id, year, athlete_id, time_seconds)
    """
    records = []
    unmatched = []

    # Get gender from event_id
    gender = event_id.split('_')[-1]  # LCM_Back_100_F -> F

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip header row
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        parts = line.split('\t')
        if len(parts) < 3:
            continue

        # Columns: Rank, Swim Time, Name, Foreign, Age, Event, LSC, Team, Meet, Time Standard
        try:
            time_str = parts[1].strip()
            name = parts[2].strip()

            # Skip if time is invalid
            if not time_str or time_str == '-':
                continue

            # Parse time
            time_seconds = parse_time_string(time_str)

            # Look up athlete by name and gender only
            key = (name.lower().strip(), gender)
            athlete_id = athletes.get(key)

            if athlete_id is None:
                unmatched.append((name, gender))
                continue

            records.append((event_id, year, athlete_id, time_seconds))

        except (ValueError, IndexError) as e:
            continue

    return records, unmatched


def main():
    print("=" * 60)
    print("Creating usa_raw_period_data table")
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

    # Walk through all period folders
    for period_folder in sorted(os.listdir(DATA_PATH)):
        period_path = os.path.join(DATA_PATH, period_folder)
        if not os.path.isdir(period_path):
            continue

        print(f"\nProcessing period: {period_folder}")

        # Walk through event folders
        for event_folder in sorted(os.listdir(period_path)):
            event_path = os.path.join(period_path, event_folder)
            if not os.path.isdir(event_path):
                continue

            # Process each age file
            for filename in sorted(os.listdir(event_path)):
                if not filename.endswith('.txt'):
                    continue

                filepath = os.path.join(event_path, filename)

                # Parse filename
                parsed = parse_filename(filename)
                if parsed is None:
                    continue

                gender, distance, stroke, age, year = parsed
                event_id = build_event_id(gender, distance, stroke)

                # Process file
                records, unmatched = process_file(filepath, athletes, year, event_id, age)
                all_records.extend(records)
                all_unmatched.extend(unmatched)
                file_count += 1

    print(f"\n[OK] Processed {file_count} files")
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
            INSERT INTO usa_raw_period_data (usa_raw_event_id, usa_raw_year, usa_athlete_id, usa_raw_time_seconds)
            VALUES (?, ?, ?, ?)
        """, all_records)
        conn.commit()
        print(f"\n[OK] Inserted {len(all_records)} records into usa_raw_period_data")

    # Verify
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM usa_raw_period_data")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT usa_athlete_id) FROM usa_raw_period_data")
    unique_athletes = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT usa_raw_event_id) FROM usa_raw_period_data")
    unique_events = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT usa_raw_year) FROM usa_raw_period_data")
    unique_years = cur.fetchone()[0]

    print(f"\n" + "=" * 60)
    print(f"SUMMARY")
    print(f"=" * 60)
    print(f"Total records: {total}")
    print(f"Unique athletes: {unique_athletes}")
    print(f"Unique events: {unique_events}")
    print(f"Unique years: {unique_years}")

    # Sample data
    print(f"\nSample records:")
    cur.execute("""
        SELECT r.usa_raw_event_id, r.usa_raw_year, a.usa_name, r.usa_raw_time_seconds
        FROM usa_raw_period_data r
        JOIN usa_athlete a ON r.usa_athlete_id = a.usa_athlete_id
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row}")

    conn.close()
    print("\n[OK] Done!")


if __name__ == "__main__":
    main()
