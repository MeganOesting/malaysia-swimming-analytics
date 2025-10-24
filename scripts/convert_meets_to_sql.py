#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Meet Files to PostgreSQL Conversion
Converts Excel meet files to PostgreSQL using proper schema and Docker connection
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text, insert
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
    """Get database connection for Docker environment"""
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming"
    )
    return create_engine(database_url)

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

def process_seag_file(df, meet_info, foreign_athletes, club_mapping):
    """Process SEAG file with known column structure"""
    athletes = []
    results = []
    events = []
    
    for index, row in df.iterrows():
        if pd.isna(row.get('E')) or row.get('E') == '':
            continue
            
        # Extract athlete data
        name = str(row.get('E', '')).strip()
        gender = str(row.get('B', '')).strip().upper()
        age = int(row.get('G', 0)) if pd.notna(row.get('G')) else None
        
        # Check if foreign athlete
        is_foreign = name.upper() in foreign_athletes
        
        # Determine state code
        state_code = None
        if is_foreign:
            # For foreign athletes, try to extract from team name or use default
            state_code = 'FGN'  # Foreign
        else:
            # For Malaysian athletes, use club mapping
            team_name = str(row.get('Q', '')).strip() if pd.notna(row.get('Q')) else ''
            if team_name:
                state_code = club_mapping.get(team_name.upper(), 'UN')
        
        athlete = {
            'id': str(uuid.uuid4()),
            'name': name,
            'gender': gender,
            'age': age,
            'is_foreign': is_foreign,
            'state_code': state_code
        }
        
        # Extract result data
        distance = int(row.get('C', 0)) if pd.notna(row.get('C')) else None
        stroke = str(row.get('D', '')).strip().upper()
        time_str = str(row.get('I', '')).strip()
        time_seconds = convert_time_to_seconds(time_str)
        aqua_points = row.get('K') if pd.notna(row.get('K')) else None
        place = int(row.get('M', 0)) if pd.notna(row.get('M')) else None
        
        # Create event
        event = {
            'id': str(uuid.uuid4()),
            'distance': distance,
            'stroke': stroke,
            'gender': gender
        }
        
        result = {
            'id': str(uuid.uuid4()),
            'athlete_id': athlete['id'],
            'meet_name': meet_info['name'],
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

def process_standard_meet_file(df, meet_info, foreign_athletes, club_mapping):
    """Process standard meet file with column mapping"""
    athletes = []
    results = []
    events = []
    
    # Find data rows (skip headers)
    data_start = 0
    for i, row in df.iterrows():
        if any(str(cell).strip().upper() in ['GENDER', 'DISTANCE', 'STROKE', 'NAME'] for cell in row if pd.notna(cell)):
            data_start = i + 1
            break
    
    print(f"  Data starts at row: {data_start}")
    
    for index in range(data_start, len(df)):
        row = df.iloc[index]
        
        # Skip empty rows
        if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
            continue
            
        # Map columns (standard format)
        try:
            gender = str(row.iloc[1]).strip().upper() if len(row) > 1 else ''
            distance = int(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else None
            stroke = str(row.iloc[3]).strip().upper() if len(row) > 3 else ''
            name = str(row.iloc[4]).strip() if len(row) > 4 else ''
            birthdate = str(row.iloc[5]).strip() if len(row) > 5 else ''
            age = int(row.iloc[6]) if len(row) > 6 and pd.notna(row.iloc[6]) else None
            time_str = str(row.iloc[8]).strip() if len(row) > 8 else ''
            aqua_points = row.iloc[10] if len(row) > 10 and pd.notna(row.iloc[10]) else None
            place = int(row.iloc[12]) if len(row) > 12 and pd.notna(row.iloc[12]) else None
            team = str(row.iloc[16]).strip() if len(row) > 16 else ''
            
            if not name or name == '':
                continue
                
            # Check if foreign athlete
            is_foreign = name.upper() in foreign_athletes
            
            # Determine state code
            state_code = None
            if is_foreign:
                state_code = 'FGN'  # Foreign
            else:
                # For Malaysian athletes, use club mapping
                if team:
                    state_code = club_mapping.get(team.upper(), 'UN')
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
                'athlete_id': athlete['id'],
                'meet_name': meet_info['name'],
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

def insert_data(engine, all_athletes, all_results, all_events, all_meets):
    """Insert data into database using proper schema"""
    with engine.connect() as conn:
        # Insert meets
        print("Inserting meets...")
        for meet in all_meets:
            conn.execute(text("""
                INSERT INTO meets (id, name, meet_type, meet_date, location)
                VALUES (:id, :name, :meet_type, :meet_date, :location)
                ON CONFLICT (id) DO NOTHING
            """), {
                'id': meet['id'],
                'name': meet['name'],
                'meet_type': meet['meet_type'],
                'meet_date': meet['meet_date'],
                'location': meet['location']
            })
        
        # Insert athletes
        print("Inserting athletes...")
        for athlete in all_athletes:
            conn.execute(text("""
                INSERT INTO athletes (id, name, gender, age, is_foreign, state_code)
                VALUES (:id, :name, :gender, :age, :is_foreign, :state_code)
                ON CONFLICT (id) DO NOTHING
            """), athlete)
        
        # Insert events
        print("Inserting events...")
        for event in all_events:
            conn.execute(text("""
                INSERT INTO events (id, distance, stroke, gender)
                VALUES (:id, :distance, :stroke, :gender)
                ON CONFLICT (id) DO NOTHING
            """), event)
        
        # Insert results
        print("Inserting results...")
        for result in all_results:
            conn.execute(text("""
                INSERT INTO results (id, athlete_id, meet_id, event_id, time_seconds, 
                                   place, points, created_at)
                VALUES (:id, :athlete_id, :meet_id, :event_id, :time_seconds,
                        :place, :points, CURRENT_TIMESTAMP)
            """), {
                'id': result['id'],
                'athlete_id': result['athlete_id'],
                'meet_id': result['meet_id'],
                'event_id': result['event_id'],
                'time_seconds': result['time_seconds'],
                'place': result['place'],
                'points': result['aqua_points']
            })
        
        conn.commit()

def main():
    """Main conversion function"""
    print("🔄 Converting Excel meet files to PostgreSQL...")
    
    # Get database connection
    engine = get_database_connection()
    
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
    insert_data(engine, unique_athletes, all_results, unique_events, all_meets)
    
    print("\n✅ Excel to PostgreSQL conversion completed successfully!")

if __name__ == "__main__":
    main()


