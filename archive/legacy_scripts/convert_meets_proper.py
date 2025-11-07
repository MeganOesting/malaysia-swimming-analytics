#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Proper Meet Files to SQLite Conversion
Follows the exact logic from the old Flask build for sheet filtering and event processing
"""

import pandas as pd
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import re
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Sheet filtering tokens from old build
SKIP_SHEET_TOKENS = ("lap", "top results", "5000m")

# Event options using stroke abbreviations (as stored in backend) - uppercase to match data
EVENT_OPTIONS = [
    "50m FR",
    "100m FR", 
    "200m FR",
    "400m FR",
    "800m FR",
    "1500m FR",
    "50m BK",
    "100m BK",
    "200m BK",
    "50m BR",
    "100m BR",
    "200m BR",
    "50m BU",
    "100m BU",
    "200m BU",
    "200m ME",
    "400m ME",
]

# Stroke mapping from old build
STROKE_MAP = {
    "FR": "Free",
    "BK": "Back", 
    "BR": "Breast",
    "BU": "Fly",
    "ME": "IM",
}

# Allowed distances from old build
ALLOWED_DISTANCES = [50, 100, 200, 400, 800, 1500]

def get_database_connection():
    """Get SQLite database connection"""
    db_path = project_root / "database" / "malaysia_swimming.db"
    return sqlite3.connect(str(db_path))

def iter_valid_sheets(workbook_path):
    """Get valid sheet names following old build logic exactly"""
    try:
        engine = "xlrd" if str(workbook_path).lower().endswith(".xls") else None
        xl = pd.ExcelFile(workbook_path, engine=engine)
    except Exception:
        return []
    
    valid = []
    
    # Special-case: if using our combined SEA Age workbook, prefer only that sheet
    try:
        base = os.path.basename(workbook_path).lower()
        if 'seag_2025_all' in base:
            for name in xl.sheet_names:
                if name.strip().lower() == 'seag_2025_all':
                    return [name]
    except Exception:
        pass
    
    for name in xl.sheet_names:
        lower = name.lower()
        if any(tok in lower for tok in SKIP_SHEET_TOKENS):
            continue
        # Skip any sheet with "x" in the name (relays)
        if 'x' in lower:
            continue
        valid.append(name)
    
    return valid

def convert_time_to_seconds(time_str):
    """Convert time string to seconds (handles mm:ss.ss and ss.ss formats)"""
    if not time_str or pd.isna(time_str):
        return None
    
    try:
        time_str = str(time_str).strip()
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        else:
            return float(time_str)
    except Exception:
        return None

def extract_meet_info(filename):
    """Extract meet information from filename"""
    filename = filename.lower()
    
    if 'sukma' in filename:
        return {
            'name': 'SUKMA 2024',
            'meet_type': 'National Games',
            'meet_date': '2024-08-18',
            'location': 'Malaysia'
        }
    elif 'miag' in filename:
        return {
            'name': 'MIAG 2025',
            'meet_type': 'International Age Group',
            'meet_date': '2025-01-15',
            'location': 'Malaysia'
        }
    elif 'malaysia open' in filename or 'mo_2025' in filename:
        return {
            'name': 'Malaysia Open 2025',
            'meet_type': 'National Open',
            'meet_date': '2025-02-01',
            'location': 'Malaysia'
        }
    elif 'seag' in filename or 'sea age' in filename:
        return {
            'name': 'SEA Age 2025',
            'meet_type': 'Regional Age Group',
            'meet_date': '2025-06-25',
            'location': 'Malaysia'
        }
    elif 'january' in filename or 'state' in filename:
        return {
            'name': 'State Championships 2024',
            'meet_type': 'State Championships',
            'meet_date': '2024-01-15',
            'location': 'Malaysia'
        }
    else:
        return {
            'name': 'Unknown Meet',
            'meet_type': 'Unknown',
            'meet_date': '2024-01-01',
            'location': 'Malaysia'
        }

def process_sheet(df, meet_id, gender, foreign_athletes, club_mapping):
    """Process a single sheet following old build column mapping exactly"""
    athletes = []
    results = []
    events = []
    
    # Map columns by index (exactly as old build)
    colB = df.get(1)   # Gender
    colC = df.get(2)    # Distance
    colD = df.get(3)    # Stroke
    colE = df.get(4)    # Name
    colF = df.get(5)    # Birthdate (dd.mm.yyyy)
    colG = df.get(6)    # Age (optional direct age)
    colI = df.get(8)    # Time (Excel col I)
    colK = df.get(10)   # AQUA points (Excel col K)
    colM = df.get(12)   # Place (Excel col M)
    colQ = df.get(16)   # Team/State (Excel col Q)
    colN = df.get(13)   # Meet date (dd.mm.yyyy)
    
    if colB is None or colC is None or colD is None or colE is None:
        return athletes, results, events
    
    # Process data exactly as old build
    gender_col = colB.astype(str).str.strip().str.upper()
    distance_col = pd.to_numeric(colC, errors='coerce')
    stroke_col = colD.astype(str).str.strip().str.upper()
    name_col = colE.astype(str).str.strip()
    
    # Skip header rows (row 1: meet info, row 2: headers, row 3+: data)
    df_data = df.iloc[2:].copy() if len(df) > 2 else df
    
    if len(df_data) == 0:
        return athletes, results, events
    
    # Re-map columns for data section
    colB_data = df_data.get(1)   # Gender
    colC_data = df_data.get(2)    # Distance
    colD_data = df_data.get(3)    # Stroke
    colE_data = df_data.get(4)    # Name
    colF_data = df_data.get(5)    # Birthdate (dd.mm.yyyy)
    colG_data = df_data.get(6)    # Age (optional direct age)
    colI_data = df_data.get(8)    # Time (Excel col I)
    colK_data = df_data.get(10)   # AQUA points (Excel col K)
    colM_data = df_data.get(12)   # Place (Excel col M)
    colQ_data = df_data.get(16)   # Team/State (Excel col Q)
    colN_data = df_data.get(13)   # Meet date (dd.mm.yyyy)
    
    if colB_data is None or colC_data is None or colD_data is None or colE_data is None:
        return athletes, results, events
    
    # Process data exactly as old build
    gender_col = colB_data.astype(str).str.strip().str.upper()
    distance_col = pd.to_numeric(colC_data, errors='coerce')
    stroke_col = colD_data.astype(str).str.strip().str.upper()
    name_col = colE_data.astype(str).str.strip()
    
    # Candidate mask: gender + has name + distance in allowed set
    mask = (
        (gender_col == gender) &
        (name_col != "") &
        (distance_col.isin(ALLOWED_DISTANCES))
    )
    
    # Get the actual data rows that match our criteria
    data_rows = df_data[mask]
    
    print(f"    Found {len(data_rows)} matching rows for {gender}")
    
    for idx, row in data_rows.iterrows():
        try:
            # Extract data using the row data directly
            swimmer_name = str(row.iloc[4]).strip()  # Column E (index 4)
            if not swimmer_name or swimmer_name == 'nan':
                print(f"    Skipping row {idx}: empty name")
                continue
                
            distance = int(row.iloc[2])  # Column C (index 2)
            stroke = str(row.iloc[3]).strip().upper()  # Column D (index 3)
            
            # Keep stroke as abbreviation for backend storage
            event_name = f"{distance}m {stroke}"
            
            print(f"    Processing: {swimmer_name} - {event_name}")
            
            # Check if event is in our allowed list (using abbreviations)
            if event_name not in EVENT_OPTIONS:
                print(f"    Skipping {event_name} - not in allowed events")
                continue
            
            # Get other data - corrected column mapping based on actual headers
            time_str = str(row.iloc[8]) if not pd.isna(row.iloc[8]) else ""  # Column 8: SWIMTIME (display time)
            time_seconds = 0
            try:
                if not pd.isna(row.iloc[9]):  # Column 9: SWIMTIME_N (time in seconds for calculations)
                    time_seconds = float(row.iloc[9])
            except:
                pass
                
            aqua_points = 0
            try:
                if not pd.isna(row.iloc[10]) and str(row.iloc[10]).replace('.', '').isdigit():  # Column 10: PTS_FINA
                    aqua_points = int(float(row.iloc[10]))
            except:
                pass
            
            place = 0
            try:
                if not pd.isna(row.iloc[12]) and str(row.iloc[12]).replace('.', '').isdigit():  # Column 12: PLACE
                    place = int(float(row.iloc[12]))
            except:
                pass
                
            team = str(row.iloc[16]) if not pd.isna(row.iloc[16]) else ""  # Column 16: CLUBNAME
            
            # Calculate age from birthdate (Column 5: BIRTHDATE)
            age = None
            try:
                if not pd.isna(row.iloc[5]):  # Column 5: BIRTHDATE
                    birthdate = row.iloc[5]
                    if hasattr(birthdate, 'year'):  # It's a datetime object
                        current_year = datetime.now().year
                        age = current_year - birthdate.year
                    else:
                        # Try to parse as string
                        birthdate_str = str(birthdate)
                        if '.' in birthdate_str:
                            day, month, year = birthdate_str.split('.')
                            birth_year = int(year)
                            current_year = datetime.now().year
                            age = current_year - birth_year
            except:
                pass
            
            if age is None:
                age = 18  # Default age
            
            # Use time_seconds from column 9 (already in seconds)
            if time_seconds == 0:
                continue
            
            # Create athlete
            athlete_id = str(uuid.uuid4())
            athlete = {
                'id': athlete_id,
                'name': swimmer_name,
                'gender': gender,
                'created_at': datetime.now().isoformat()
            }
            athletes.append(athlete)
            
            # Create event
            event_id = str(uuid.uuid4())
            event = {
                'id': event_id,
                'distance': distance,
                'stroke': stroke,  # Store abbreviation as-is
                'gender': gender,
                'created_at': datetime.now().isoformat()
            }
            events.append(event)
            
            # Create result
            result = {
                'id': str(uuid.uuid4()),
                'meet_id': meet_id,
                'athlete_id': athlete_id,
                'event_id': event_id,
                'time_seconds': time_seconds,
                'time_string': time_str,
                'place': place,
                'aqua_points': aqua_points,
                'age': age,
                'created_at': datetime.now().isoformat()
            }
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing row {idx}: {e}")
            continue
    
    return athletes, results, events

def process_meet_file(file_path, meet_info, foreign_athletes, club_mapping):
    """Process a single meet file following old build logic exactly"""
    print(f"Processing: {file_path.name}")
    
    try:
        # Get valid sheets using old build logic
        valid_sheets = iter_valid_sheets(file_path)
        print(f"  Valid sheets: {valid_sheets}")
        
        all_athletes = []
        all_results = []
        all_events = []
        
        # Process each valid sheet
        for sheet_name in valid_sheets:
            print(f"  Processing sheet: {sheet_name}")
            
            try:
                engine = "xlrd" if str(file_path).lower().endswith(".xls") else None
                if engine:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine=engine)
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                
                print(f"    Sheet shape: {df.shape}")
                
                # Process for both genders
                for gender in ['M', 'F']:
                    athletes, results, events = process_sheet(df, meet_info['id'], gender, foreign_athletes, club_mapping)
                    all_athletes.extend(athletes)
                    all_results.extend(results)
                    all_events.extend(events)
                    
                    print(f"    {gender}: {len(athletes)} athletes, {len(results)} results, {len(events)} events")
                
            except Exception as e:
                print(f"    Error processing sheet {sheet_name}: {e}")
                continue
        
        print(f"  Total: {len(all_athletes)} athletes, {len(all_results)} results, {len(all_events)} events")
        return all_athletes, all_results, all_events
        
    except Exception as e:
        print(f"  Error processing {file_path.name}: {e}")
        return [], [], []

def create_database_tables(conn):
    """Create database tables"""
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS results")
    cursor.execute("DROP TABLE IF EXISTS athletes") 
    cursor.execute("DROP TABLE IF EXISTS events")
    cursor.execute("DROP TABLE IF EXISTS meets")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE meets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            meet_type TEXT,
            meet_date TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE athletes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            distance INTEGER NOT NULL,
            stroke TEXT NOT NULL,
            gender TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE results (
            id TEXT PRIMARY KEY,
            meet_id TEXT NOT NULL,
            athlete_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            time_seconds REAL NOT NULL,
            time_string TEXT NOT NULL,
            place INTEGER NOT NULL,
            aqua_points INTEGER NOT NULL,
            age INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meet_id) REFERENCES meets(id),
            FOREIGN KEY (athlete_id) REFERENCES athletes(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    """)
    
    conn.commit()

def load_foreign_athletes():
    """Load foreign athletes from AthleteINFO.csv"""
    foreign_athletes = set()
    try:
        csv_path = project_root / "data" / "athletes" / "AthleteINFO.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                if 'foreign' in str(row.get('notes', '')).lower():
                    foreign_athletes.add(str(row.get('name', '')).strip())
    except Exception as e:
        print(f"Error loading foreign athletes: {e}")
    return foreign_athletes

def load_club_mapping():
    """Load club to state mapping"""
    club_mapping = {}
    try:
        xlsx_path = project_root / "data" / "reference" / "Clubs_By_State.xlsx"
        if xlsx_path.exists():
            df = pd.read_excel(xlsx_path)
            for _, row in df.iterrows():
                club = str(row.get('Club', '')).strip()
                state = str(row.get('State', '')).strip()
                if club and state:
                    club_mapping[club.lower()] = state
    except Exception as e:
        print(f"Error loading club mapping: {e}")
    return club_mapping

def insert_data(conn, all_athletes, all_results, all_events, all_meets):
    """Insert data into database"""
    cursor = conn.cursor()
    
    # Insert meets
    for meet in all_meets:
        cursor.execute("""
            INSERT INTO meets (id, name, meet_type, meet_date, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (meet['id'], meet['name'], meet['meet_type'], meet['meet_date'], meet['location'], meet['created_at']))
    
    # Insert athletes
    for athlete in all_athletes:
        cursor.execute("""
            INSERT INTO athletes (id, name, gender, created_at)
            VALUES (?, ?, ?, ?)
        """, (athlete['id'], athlete['name'], athlete['gender'], athlete['created_at']))
    
    # Insert events
    for event in all_events:
        cursor.execute("""
            INSERT INTO events (id, distance, stroke, gender, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (event['id'], event['distance'], event['stroke'], event['gender'], event['created_at']))
    
    # Insert results
    for result in all_results:
        cursor.execute("""
            INSERT INTO results (id, meet_id, athlete_id, event_id, time_seconds, time_string, place, aqua_points, age, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result['id'], result['meet_id'], result['athlete_id'], result['event_id'], 
              result['time_seconds'], result['time_string'], result['place'], result['aqua_points'], result['age'], result['created_at']))
    
    conn.commit()

def main():
    """Main conversion function"""
    print("Converting Excel meet files to SQLite (following old build logic exactly)...")
    
    # Get database connection
    conn = get_database_connection()
    
    # Create tables
    print("Creating database tables...")
    create_database_tables(conn)
    
    # Load reference data
    print("Loading reference data...")
    foreign_athletes = load_foreign_athletes()
    club_mapping = load_club_mapping()
    print(f"Loaded {len(foreign_athletes)} foreign athletes")
    print(f"Loaded {len(club_mapping)} club mappings")
    
    # Process all meet files
    meets_dir = project_root / "data" / "meets"
    excel_files = list(meets_dir.glob("*.xls*"))
    
    all_athletes = []
    all_results = []
    all_events = []
    all_meets = []
    
    print(f"Found {len(excel_files)} Excel files to process")
    
    for file_path in excel_files:
        if 'Malaysia On Track Times Spreadsheet Workbook' in file_path.name:
            continue  # Skip the source workbook
            
        meet_info = extract_meet_info(file_path.name)
        meet_info['id'] = str(uuid.uuid4())
        meet_info['created_at'] = datetime.now().isoformat()
        all_meets.append(meet_info)
        
        athletes, results, events = process_meet_file(file_path, meet_info, foreign_athletes, club_mapping)
        all_athletes.extend(athletes)
        all_results.extend(results)
        all_events.extend(events)
        
        print(f"  Processed {len(athletes)} athletes, {len(results)} results, {len(events)} events")
    
    # Remove duplicates
    unique_athletes = []
    seen_names = set()
    for athlete in all_athletes:
        if athlete['name'] not in seen_names:
            unique_athletes.append(athlete)
            seen_names.add(athlete['name'])
    
    unique_events = []
    seen_events = set()
    for event in all_events:
        event_key = f"{event['distance']}_{event['stroke']}_{event['gender']}"
        if event_key not in seen_events:
            unique_events.append(event)
            seen_events.add(event_key)
    
    print(f"\nTotal unique athletes: {len(unique_athletes)}")
    print(f"Total unique events: {len(unique_events)}")
    print(f"Total results: {len(all_results)}")
    print(f"Total meets: {len(all_meets)}")
    
    # Insert data
    print("Inserting data into database...")
    insert_data(conn, unique_athletes, all_results, unique_events, all_meets)
    
    conn.close()
    print("Conversion complete!")

if __name__ == "__main__":
    main()
