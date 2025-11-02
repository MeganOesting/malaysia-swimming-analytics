#!/usr/bin/env python3
"""
Convert all Excel meet files to PostgreSQL database
"""

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text, insert
import os
import sys
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def get_database_connection():
    """Get database connection"""
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://swimming_user:swimming_pass@localhost:5432/malaysia_swimming"
    )
    return create_engine(database_url)

def convert_time_to_seconds(time_str):
    """Convert time string to seconds"""
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

def process_meet_file(file_path, meet_info):
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
            return process_seag_file(df, meet_info)
        else:
            return process_standard_meet_file(df, meet_info)
            
    except Exception as e:
        print(f"  Error processing {file_path.name}: {e}")
        return [], []

def process_seag_file(df, meet_info):
    """Process SEAG file with known column structure"""
    athletes = []
    results = []
    
    for index, row in df.iterrows():
        if pd.isna(row.get('E')) or row.get('E') == '':
            continue
            
        # Extract athlete data
        athlete = {
            'name': str(row.get('E', '')).strip(),
            'gender': str(row.get('B', '')).strip().upper(),
            'age': int(row.get('G', 0)) if pd.notna(row.get('G')) else None,
            'is_foreign': False,  # Will be determined later
            'club_id': None,
            'state_code': None
        }
        
        # Extract result data
        time_seconds = convert_time_to_seconds(row.get('I'))
        aqua_points = row.get('K') if pd.notna(row.get('K')) else None
        
        result = {
            'meet_name': meet_info['name'],
            'athlete_name': athlete['name'],
            'gender': athlete['gender'],
            'distance': int(row.get('C', 0)) if pd.notna(row.get('C')) else None,
            'stroke': str(row.get('D', '')).strip().upper(),
            'time_seconds': time_seconds,
            'time_string': str(row.get('I', '')).strip(),
            'place': int(row.get('M', 0)) if pd.notna(row.get('M')) else None,
            'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
            'age': athlete['age'],
            'meet_date': meet_info['meet_date']
        }
        
        athletes.append(athlete)
        results.append(result)
    
    return athletes, results

def process_standard_meet_file(df, meet_info):
    """Process standard meet file with column mapping"""
    athletes = []
    results = []
    
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
                
            # Extract athlete data
            athlete = {
                'name': name,
                'gender': gender,
                'age': age,
                'is_foreign': False,  # Will be determined later
                'club_id': None,
                'state_code': None
            }
            
            # Extract result data
            time_seconds = convert_time_to_seconds(time_str)
            
            result = {
                'meet_name': meet_info['name'],
                'athlete_name': name,
                'gender': gender,
                'distance': distance,
                'stroke': stroke,
                'time_seconds': time_seconds,
                'time_string': time_str,
                'place': place,
                'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
                'age': age,
                'meet_date': meet_info['meet_date']
            }
            
            athletes.append(athlete)
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing row {index}: {e}")
            continue
    
    return athletes, results

def create_database_tables(engine):
    """Create database tables if they don't exist"""
    with engine.connect() as conn:
        # Create meets table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                meet_type VARCHAR(100),
                meet_date DATE,
                location VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create athletes table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS athletes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                gender CHAR(1),
                age INTEGER,
                is_foreign BOOLEAN DEFAULT FALSE,
                club_id INTEGER,
                state_code VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create results table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS results (
                id SERIAL PRIMARY KEY,
                meet_id INTEGER,
                athlete_id INTEGER,
                athlete_name VARCHAR(255),
                gender CHAR(1),
                distance INTEGER,
                stroke VARCHAR(10),
                time_seconds DECIMAL(8,3),
                time_string VARCHAR(20),
                place INTEGER,
                aqua_points INTEGER,
                age INTEGER,
                meet_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.commit()

def insert_data(engine, all_athletes, all_results, all_meets):
    """Insert data into database"""
    with engine.connect() as conn:
        # Insert meets
        print("Inserting meets...")
        for meet in all_meets:
            conn.execute(text("""
                INSERT INTO meets (name, meet_type, meet_date, location)
                VALUES (:name, :meet_type, :meet_date, :location)
                ON CONFLICT DO NOTHING
            """), meet)
        
        # Insert athletes
        print("Inserting athletes...")
        for athlete in all_athletes:
            conn.execute(text("""
                INSERT INTO athletes (name, gender, age, is_foreign, club_id, state_code)
                VALUES (:name, :gender, :age, :is_foreign, :club_id, :state_code)
                ON CONFLICT DO NOTHING
            """), athlete)
        
        # Insert results
        print("Inserting results...")
        for result in all_results:
            conn.execute(text("""
                INSERT INTO results (athlete_name, gender, distance, stroke, time_seconds, 
                                   time_string, place, aqua_points, age, meet_date)
                VALUES (:athlete_name, :gender, :distance, :stroke, :time_seconds,
                        :time_string, :place, :aqua_points, :age, :meet_date)
            """), result)
        
        conn.commit()

def main():
    """Main conversion function"""
    print("🔄 Converting Excel files to PostgreSQL...")
    
    # Get database connection
    engine = get_database_connection()
    
    # Create tables
    print("Creating database tables...")
    create_database_tables(engine)
    
    # Process all meet files
    meets_dir = project_root / "data" / "meets"
    excel_files = list(meets_dir.glob("*.xls*"))
    
    all_athletes = []
    all_results = []
    all_meets = []
    
    print(f"Found {len(excel_files)} Excel files to process")
    
    for file_path in excel_files:
        if 'Malaysia On Track Times Spreadsheet Workbook' in file_path.name:
            continue  # Skip the source workbook
            
        meet_info = extract_meet_info(file_path.name)
        all_meets.append(meet_info)
        
        athletes, results = process_meet_file(file_path, meet_info)
        all_athletes.extend(athletes)
        all_results.extend(results)
        
        print(f"  Processed {len(athletes)} athletes, {len(results)} results")
    
    # Remove duplicates
    unique_athletes = []
    seen_names = set()
    for athlete in all_athletes:
        if athlete['name'] not in seen_names:
            unique_athletes.append(athlete)
            seen_names.add(athlete['name'])
    
    print(f"\nTotal unique athletes: {len(unique_athletes)}")
    print(f"Total results: {len(all_results)}")
    print(f"Total meets: {len(all_meets)}")
    
    # Insert data
    print("\nInserting data into database...")
    insert_data(engine, unique_athletes, all_results, all_meets)
    
    print("\n✅ Excel to PostgreSQL conversion completed successfully!")

if __name__ == "__main__":
    main()


