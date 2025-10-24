#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Meet Files to SQLite Conversion (Fixed)
Converts Excel meet files to SQLite database with proper standard format handling
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

def get_database_connection():
    """Get SQLite database connection"""
    db_path = project_root / "malaysia_swimming.db"
    return sqlite3.connect(str(db_path))

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
    elif 'mo' in filename:
        return {
            'name': 'Malaysia Open 2025',
            'meet_type': 'National Open',
            'meet_date': '2025-02-01',
            'location': 'Malaysia'
        }
    elif 'seag' in filename:
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

def load_foreign_athletes():
    """Load foreign athlete names from AthleteINFO.csv"""
    foreign_athletes = set()
    
    try:
        athlete_info_path = project_root / "data" / "athletes" / "AthleteINFO.csv"
        if athlete_info_path.exists():
            df = pd.read_csv(athlete_info_path)
            for _, row in df.iterrows():
                if row.get('foreign', '').upper() == 'Y':
                    foreign_athletes.add(str(row.get('name', '')).strip().upper())
    except Exception as e:
        print(f"Warning: Could not load foreign athletes: {e}")
    
    return foreign_athletes

def load_club_mapping():
    """Load club to state mapping from Clubs_By_State.xlsx"""
    club_mapping = {}
    
    try:
        clubs_path = project_root / "data" / "reference" / "Clubs_By_State.xlsx"
        if clubs_path.exists():
            xl_file = pd.ExcelFile(clubs_path)
            for sheet_name in xl_file.sheet_names:
                if len(sheet_name) == 3:  # State code
                    df = pd.read_excel(clubs_path, sheet_name=sheet_name)
                    for _, row in df.iterrows():
                        club_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ''
                        if club_name:
                            club_mapping[club_name.upper()] = sheet_name.upper()
    except Exception as e:
        print(f"Warning: Could not load club mapping: {e}")
    
    return club_mapping

def create_database_tables(conn):
    """Create database tables"""
    cursor = conn.cursor()
    
    # Create meets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            meet_type TEXT,
            meet_date TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create athletes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            age INTEGER,
            is_foreign BOOLEAN DEFAULT 0,
            state_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            distance INTEGER,
            stroke TEXT,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            meet_id TEXT,
            athlete_id TEXT,
            event_id TEXT,
            time_seconds REAL,
            time_string TEXT,
            place INTEGER,
            aqua_points INTEGER,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meet_id) REFERENCES meets (id),
            FOREIGN KEY (athlete_id) REFERENCES athletes (id),
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    """)
    
    conn.commit()

def process_standard_meet_file(df, meet_info, foreign_athletes, club_mapping):
    """Process standard meet file with proper column headers"""
    athletes = []
    results = []
    events = []
    
    print(f"  Processing standard format with {len(df)} rows")
    
    # Find the header row (look for 'GENDER' in the data)
    header_row = 0
    for i, row in df.iterrows():
        if any(str(cell).strip().upper() == 'GENDER' for cell in row if pd.notna(cell)):
            header_row = i
            break
    
    print(f"  Header row found at: {header_row}")
    
    # Process data rows starting after header
    for index in range(header_row + 1, len(df)):
        row = df.iloc[index]
        
        # Skip empty rows
        if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
            continue
        
        try:
            # Map columns using standard format
            gender = str(row.iloc[1]).strip().upper() if pd.notna(row.iloc[1]) else ''
            distance = int(row.iloc[2]) if pd.notna(row.iloc[2]) else None
            stroke = str(row.iloc[3]).strip().upper() if pd.notna(row.iloc[3]) else ''
            name = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
            birthdate = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ''
            nation = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else ''
            time_str = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ''
            aqua_points = row.iloc[10] if pd.notna(row.iloc[10]) else None
            place = int(row.iloc[12]) if pd.notna(row.iloc[12]) else None
            club_name = str(row.iloc[16]).strip() if pd.notna(row.iloc[16]) else ''
            
            if not name or name == '':
                continue
            
            # Calculate age from birthdate if available
            age = None
            if birthdate and birthdate != '':
                try:
                    # Handle different date formats
                    if '/' in birthdate:
                        birth_date = datetime.strptime(birthdate, '%d/%m/%Y')
                    elif '-' in birthdate:
                        birth_date = datetime.strptime(birthdate, '%Y-%m-%d')
                    else:
                        birth_date = datetime.strptime(birthdate, '%d.%m.%Y')
                    
                    # Calculate age as of meet year
                    meet_year = int(meet_info['meet_date'][:4])
                    age = meet_year - birth_date.year
                except:
                    age = None
            
            # Check if foreign athlete
            is_foreign = name.upper() in foreign_athletes or nation not in ['MAS', 'MALAYSIA', '']
            
            # Determine state code
            state_code = None
            if is_foreign:
                state_code = nation if nation not in ['MAS', 'MALAYSIA', ''] else 'FGN'
            else:
                if club_name:
                    state_code = club_mapping.get(club_name.upper(), 'UN')
                else:
                    state_code = 'UN'
            
            # Extract athlete data
            athlete = {
                'id': str(uuid.uuid4()),
                'name': name,
                'gender': gender,
                'age': age,
                'is_foreign': is_foreign,
                'state_code': state_code
            }
            
            # Create event
            event = {
                'id': str(uuid.uuid4()),
                'distance': distance,
                'stroke': stroke,
                'gender': gender
            }
            
            # Extract result data
            time_seconds = convert_time_to_seconds(time_str)
            
            result = {
                'id': str(uuid.uuid4()),
                'meet_id': meet_info['id'],
                'athlete_id': athlete['id'],
                'event_id': event['id'],
                'time_seconds': time_seconds,
                'time_string': time_str,
                'place': place,
                'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
                'age': age
            }
            
            athletes.append(athlete)
            events.append(event)
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing row {index}: {e}")
            continue
    
    return athletes, results, events

def process_seag_file(df, meet_info, foreign_athletes, club_mapping):
    """Process SEAG file with column mapping to standard format"""
    athletes = []
    results = []
    events = []
    
    print(f"  Processing SEAG format with {len(df)} rows")
    
    for index, row in df.iterrows():
        if pd.isna(row.get('E')) or row.get('E') == '':
            continue
            
        # Map SEAG columns to standard format
        # SEAG: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X
        # Standard: Gender, Distance, Stroke, Name, Birthdate, Nation, Time, AQUA, Place, Club
        
        name = str(row.get('E', '')).strip()
        gender = str(row.get('B', '')).strip().upper()
        distance = int(row.get('C', 0)) if pd.notna(row.get('C')) else None
        stroke = str(row.get('D', '')).strip().upper()
        age = int(row.get('G', 0)) if pd.notna(row.get('G')) else None
        time_str = str(row.get('I', '')).strip()
        aqua_points = row.get('K') if pd.notna(row.get('K')) else None
        place = int(row.get('M', 0)) if pd.notna(row.get('M')) else None
        
        if not name or name == '':
            continue
        
        # Check if foreign athlete
        is_foreign = name.upper() in foreign_athletes
        
        # Determine state code
        state_code = None
        if is_foreign:
            state_code = 'FGN'  # Foreign
        else:
            # For SEAG, we'll use a default mapping or try to extract from other fields
            state_code = 'UN'  # Unassigned for now
        
        # Extract athlete data
        athlete = {
            'id': str(uuid.uuid4()),
            'name': name,
            'gender': gender,
            'age': age,
            'is_foreign': is_foreign,
            'state_code': state_code
        }
        
        # Create event
        event = {
            'id': str(uuid.uuid4()),
            'distance': distance,
            'stroke': stroke,
            'gender': gender
        }
        
        # Extract result data
        time_seconds = convert_time_to_seconds(time_str)
        
        result = {
            'id': str(uuid.uuid4()),
            'meet_id': meet_info['id'],
            'athlete_id': athlete['id'],
            'event_id': event['id'],
            'time_seconds': time_seconds,
            'time_string': time_str,
            'place': place,
            'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
            'age': age
        }
        
        athletes.append(athlete)
        events.append(event)
        results.append(result)
    
    return athletes, results, events

def process_meet_file(file_path, meet_info, foreign_athletes, club_mapping):
    """Process a single meet file and return data for database"""
    print(f"Processing: {file_path.name}")
    
    try:
        # Read Excel file
        if file_path.suffix == '.xlsx':
            df = pd.read_excel(file_path)
        else:
            df = pd.read_excel(file_path, engine='xlrd')
        
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        
        # Process based on file type
        if 'SEAG_2025_ALL' in file_path.name:
            return process_seag_file(df, meet_info, foreign_athletes, club_mapping)
        else:
            return process_standard_meet_file(df, meet_info, foreign_athletes, club_mapping)
            
    except Exception as e:
        print(f"  Error processing {file_path.name}: {e}")
        return [], [], []

def insert_data(conn, all_athletes, all_results, all_events, all_meets):
    """Insert data into database"""
    cursor = conn.cursor()
    
    # Insert meets
    print("Inserting meets...")
    for meet in all_meets:
        cursor.execute("""
            INSERT OR IGNORE INTO meets (id, name, meet_type, meet_date, location)
            VALUES (?, ?, ?, ?, ?)
        """, (meet['id'], meet['name'], meet['meet_type'], meet['meet_date'], meet['location']))
    
    # Insert athletes
    print("Inserting athletes...")
    for athlete in all_athletes:
        cursor.execute("""
            INSERT OR IGNORE INTO athletes (id, name, gender, age, is_foreign, state_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (athlete['id'], athlete['name'], athlete['gender'], athlete['age'], 
              athlete['is_foreign'], athlete['state_code']))
    
    # Insert events
    print("Inserting events...")
    for event in all_events:
        cursor.execute("""
            INSERT OR IGNORE INTO events (id, distance, stroke, gender)
            VALUES (?, ?, ?, ?)
        """, (event['id'], event['distance'], event['stroke'], event['gender']))
    
    # Insert results
    print("Inserting results...")
    for result in all_results:
        cursor.execute("""
            INSERT OR IGNORE INTO results (id, meet_id, athlete_id, event_id, time_seconds, 
                                          time_string, place, aqua_points, age)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result['id'], result['meet_id'], result['athlete_id'], result['event_id'],
              result['time_seconds'], result['time_string'], result['place'], 
              result['aqua_points'], result['age']))
    
    conn.commit()

def main():
    """Main conversion function"""
    print("Converting Excel meet files to SQLite (Fixed Version)...")
    
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
    print("\nInserting data into database...")
    insert_data(conn, unique_athletes, all_results, unique_events, all_meets)
    
    # Verify data
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM athletes")
    athlete_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM meets")
    meet_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM results")
    result_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events")
    event_count = cursor.fetchone()[0]
    
    print(f"\nDatabase populated successfully!")
    print(f"  Athletes: {athlete_count}")
    print(f"  Meets: {meet_count}")
    print(f"  Results: {result_count}")
    print(f"  Events: {event_count}")
    
    conn.close()
    print(f"\nExcel to SQLite conversion completed successfully!")
    print(f"Database saved as: {project_root / 'malaysia_swimming.db'}")

if __name__ == "__main__":
    main()


