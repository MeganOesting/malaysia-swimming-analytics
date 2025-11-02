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
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add city column if it doesn't exist
    try:
        cursor.execute("""
            ALTER TABLE meets ADD COLUMN city TEXT
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create athletes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athletes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            age INTEGER,
            birth_date TEXT,
            nation TEXT,
            club_name TEXT,
            club_code TEXT,
            is_foreign BOOLEAN DEFAULT 0,
            state_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add missing columns if they don't exist (for existing databases)
    columns_to_add = [
        ('birth_date', 'TEXT'),
        ('nation', 'TEXT'),
        ('club_name', 'TEXT'),
        ('club_code', 'TEXT'),
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"""
                ALTER TABLE athletes ADD COLUMN {col_name} {col_type}
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists
    
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
            time_seconds_numeric REAL,
            place INTEGER,
            aqua_points INTEGER,
            rudolph_points REAL,
            course TEXT,
            result_meet_date TEXT,
            day_age INTEGER,
            year_age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meet_id) REFERENCES meets (id),
            FOREIGN KEY (athlete_id) REFERENCES athletes (id),
            FOREIGN KEY (event_id) REFERENCES events (id)
        )
    """)
    
    # Add missing columns if they don't exist (for existing databases)
    result_columns_to_add = [
        ('time_seconds_numeric', 'REAL'),
        ('rudolph_points', 'REAL'),
        ('course', 'TEXT'),
        ('result_meet_date', 'TEXT'),
        ('day_age', 'INTEGER'),
        ('year_age', 'INTEGER'),
    ]
    for col_name, col_type in result_columns_to_add:
        try:
            cursor.execute(f"""
                ALTER TABLE results ADD COLUMN {col_name} {col_type}
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists
    
    conn.commit()

def process_standard_meet_file(df, meet_info, foreign_athletes, club_mapping, course='LCM'):
    """Process standard meet file with proper column headers
    Returns (athletes, results, events, extracted_meet_info)
    where extracted_meet_info contains the actual meet name/city from the data
    
    Args:
        course: 'LCM' or 'SCM' - used for validation (e.g., 100m IM only in SCM)
    """
    athletes = []
    results = []
    events = []
    extracted_meet_info = {'name': None, 'city': None}
    
    print(f"  Processing standard format with {len(df)} rows")
    
    # Headers are typically in row 2 (index 2), data starts in row 3 (index 3)
    # But check to be sure - look for 'GENDER' in row 1 or 2
    header_row = 1  # Default to row 2 (index 1)
    for i in [1, 0, 2]:  # Check row 2 first (index 1), then row 1, then row 3
        if i < len(df):
            row = df.iloc[i]
            if any(str(cell).strip().upper() == 'GENDER' for cell in row if pd.notna(cell)):
                header_row = i
                break
    
    print(f"  Header row found at: {header_row} (data starts at {header_row + 1})")
    
    # Collect unique meet names and cities from the data
    meet_names_seen = set()
    meet_cities_seen = set()
    
    # Process data rows starting after header
    for index in range(header_row + 1, len(df)):
        row = df.iloc[index]
        
        # Skip empty rows
        if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
            continue
        
        try:
            # Map columns using standard format
            # Note: course from column 0 might differ from detected course, use detected course
            course_from_data = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            # Use the detected course passed as parameter (more reliable)
            result_course = course
            gender = str(row.iloc[1]).strip().upper() if pd.notna(row.iloc[1]) else ''
            distance = int(row.iloc[2]) if pd.notna(row.iloc[2]) else None
            stroke = str(row.iloc[3]).strip().upper() if pd.notna(row.iloc[3]) else ''
            name = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
            birthdate = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ''
            nation = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else ''
            club_code = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else None
            time_str = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ''
            time_seconds_numeric = float(row.iloc[9]) if pd.notna(row.iloc[9]) else None
            aqua_points = row.iloc[10] if pd.notna(row.iloc[10]) else None
            rudolph_points = float(row.iloc[11]) if pd.notna(row.iloc[11]) else None
            place = int(row.iloc[12]) if pd.notna(row.iloc[12]) else None
            result_meet_date = row.iloc[13] if pd.notna(row.iloc[13]) else None
            
            # Parse meet date from result_meet_date if available
            parsed_meet_date = None
            if result_meet_date:
                from datetime import datetime
                # Handle datetime/Timestamp objects directly
                if isinstance(result_meet_date, (pd.Timestamp, datetime)):
                    parsed_meet_date = result_meet_date.strftime('%Y-%m-%d')
                elif isinstance(result_meet_date, str) and result_meet_date.strip():
                    # Try to parse various date formats (DD.MM.YYYY, DD/MM/YYYY, etc.)
                    date_str = result_meet_date.strip()
                    date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']
                    for fmt in date_formats:
                        try:
                            parsed_meet_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
            meet_city = str(row.iloc[14]).strip() if pd.notna(row.iloc[14]) else None
            meet_name = str(row.iloc[15]).strip() if pd.notna(row.iloc[15]) else None
            club_name = str(row.iloc[16]).strip() if pd.notna(row.iloc[16]) else ''
            
            # Collect meet name from column 15 (MEETNAME)
            # Skip if it looks like header or data column (LCM, SCM, F, M, numbers, short strings)
            if meet_name and meet_name.strip():
                meet_name_clean = meet_name.strip()
                # Filter out obvious non-meet-name values
                skip_values = ['LCM', 'SCM', 'F', 'M', 'MEETNAME', 'COURSE', 'GENDER', 'DISTANCE', 'STROKE', 'NAME', 'BIRTHDATE']
                if (meet_name_clean.upper() not in skip_values and 
                    not meet_name_clean.isdigit() and 
                    len(meet_name_clean) > 5 and  # Meet names should be reasonably long
                    meet_name_clean.lower() not in ['lcm', 'scm', 'f', 'm']):
                    # Check if it looks like an athlete name (has comma pattern like "Last, First")
                    # Meet names typically don't have this pattern, or if they do, the comma is followed by more text
                    if ',' in meet_name_clean:
                        parts = meet_name_clean.split(',')
                        # If it's "LastName, FirstName", skip it. If it's "Meet Name, Location", keep it.
                        # Meet names with commas usually have more text after the comma
                        if len(parts) == 2 and len(parts[1].strip()) < 5:
                            # Likely an athlete name, skip
                            pass
                        else:
                            # Likely a meet name with location info
                            meet_names_seen.add(meet_name_clean)
                    else:
                        # No comma, likely a meet name
                        meet_names_seen.add(meet_name_clean)
            
            # Collect meet city from column 14
            if meet_city and meet_city.strip():
                meet_city_clean = meet_city.strip()
                skip_values = ['LCM', 'SCM', 'F', 'M', 'MEETCITY', 'MEET CITY', 'CITY']
                if (meet_city_clean.upper() not in skip_values and 
                    not meet_city_clean.isdigit() and 
                    len(meet_city_clean) > 2):
                    meet_cities_seen.add(meet_city_clean)
            
            if not name or name == '':
                continue
            
            # Calculate day_age and year_age from birthdate if available
            day_age = None
            year_age = None
            if birthdate and birthdate != '' and str(birthdate).strip() != '' and str(birthdate).strip().upper() != 'NAN':
                try:
                    from datetime import datetime, date
                    # Handle pandas Timestamp/datetime objects
                    if isinstance(birthdate, pd.Timestamp):
                        birth_date = birthdate.to_pydatetime()
                    elif isinstance(birthdate, datetime):
                        birth_date = birthdate
                    elif isinstance(birthdate, date):
                        birth_date = birthdate
                    else:
                        # Convert to string and parse
                        birthdate_str = str(birthdate).strip()
                        if ':' in birthdate_str and ' ' in birthdate_str:
                            birthdate_str = birthdate_str.split()[0]  # Take just the date part
                        
                        if '/' in birthdate_str:
                            birth_date = datetime.strptime(birthdate_str, '%d/%m/%Y')
                        elif '.' in birthdate_str and len(birthdate_str.split('.')) == 3:
                            birth_date = datetime.strptime(birthdate_str, '%d.%m.%Y')
                        elif '-' in birthdate_str and len(birthdate_str) >= 10:
                            birth_date = datetime.strptime(birthdate_str[:10], '%Y-%m-%d')
                        else:
                            birth_date = None
                    
                    if birth_date:
                        # Get meet date (first day of the meet) - use meet_info['meet_date'] for consistency
                        # All results in the same meet should have the same day_age
                        meet_date_str = meet_info.get('meet_date')
                        if meet_date_str:
                            try:
                                if isinstance(meet_date_str, str):
                                    meet_date = datetime.strptime(meet_date_str[:10], '%Y-%m-%d')
                                else:
                                    meet_date = meet_date_str
                                
                                # day_age: Age on the first day of the meet (same for all results in the meet)
                                meet_date_obj = meet_date.date() if hasattr(meet_date, 'date') else meet_date
                                birth_date_obj = birth_date.date() if hasattr(birth_date, 'date') else birth_date
                                day_age = meet_date_obj.year - birth_date_obj.year
                                # Adjust if birthday hasn't occurred yet this year
                                if (meet_date_obj.month, meet_date_obj.day) < (birth_date_obj.month, birth_date_obj.day):
                                    day_age -= 1
                                
                                # year_age: Age on December 31 of the meet year (same for all results in same year)
                                meet_year = meet_date_obj.year
                                year_end = date(meet_year, 12, 31)
                                year_age = year_end.year - birth_date_obj.year
                                # Adjust if birthday hasn't occurred yet by Dec 31
                                if (year_end.month, year_end.day) < (birth_date_obj.month, birth_date_obj.day):
                                    year_age -= 1
                            except Exception as e:
                                # Fallback to year-based calculation
                                meet_year = int(str(meet_info.get('meet_date', '2024-01-01'))[:4])
                                year_age = meet_year - birth_date.year
                                day_age = year_age  # Use year_age as approximation
                except Exception as e:
                    day_age = None
                    year_age = None
            
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
            
            # Store birthdate in ISO format (YYYY-MM-DD) for consistency
            birth_date_str = None
            if birthdate and birthdate != '' and str(birthdate).strip() != '' and str(birthdate).strip().upper() != 'NAN':
                try:
                    # Handle pandas Timestamp/datetime objects
                    if isinstance(birthdate, pd.Timestamp):
                        birth_date_str = birthdate.strftime('%Y-%m-%d')
                    elif isinstance(birthdate, datetime):
                        birth_date_str = birthdate.strftime('%Y-%m-%d')
                    else:
                        # Convert to string and parse
                        birthdate_str = str(birthdate).strip()
                        if ':' in birthdate_str and ' ' in birthdate_str:
                            # Likely a datetime string like "2010-11-11 00:00:00"
                            birthdate_str = birthdate_str.split()[0]  # Take just the date part
                        
                        if '/' in birthdate_str:
                            birth_date = datetime.strptime(birthdate_str, '%d/%m/%Y')
                            birth_date_str = birth_date.strftime('%Y-%m-%d')
                        elif '.' in birthdate_str and len(birthdate_str.split('.')) == 3:
                            birth_date = datetime.strptime(birthdate_str, '%d.%m.%Y')
                            birth_date_str = birth_date.strftime('%Y-%m-%d')
                        elif '-' in birthdate_str and len(birthdate_str) >= 10:
                            # Already in YYYY-MM-DD format or similar
                            birth_date_str = birthdate_str[:10]  # Take first 10 chars
                except Exception as e:
                    birth_date_str = None
            
            # Extract athlete data
            # Note: Age is now calculated per result (day_age and year_age), not per athlete
            # We'll set age to None or use year_age as an approximation for the athlete table
            athlete = {
                'id': str(uuid.uuid4()),
                'name': name,
                'gender': gender,
                'age': year_age,  # Use year_age as approximation for athlete age (can be None)
                'birth_date': birth_date_str,
                'nation': nation if nation else None,
                'club_name': club_name if club_name else None,
                'club_code': club_code if club_code else None,
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
            
            # Use the parsed_meet_date we already computed
            parsed_meet_date_for_result = parsed_meet_date
            
            # Clean meet_name and meet_city for grouping
            result_meet_name = None
            if meet_name and meet_name.strip():
                meet_name_clean = meet_name.strip()
                skip_values = ['LCM', 'SCM', 'F', 'M', 'MEETNAME', 'COURSE', 'GENDER', 'DISTANCE', 'STROKE', 'NAME', 'BIRTHDATE']
                if (meet_name_clean.upper() not in skip_values and 
                    not meet_name_clean.isdigit() and 
                    len(meet_name_clean) > 5):
                    # Check if it looks like an athlete name
                    if ',' in meet_name_clean:
                        parts = meet_name_clean.split(',')
                        if not (len(parts) == 2 and len(parts[1].strip()) < 5):
                            result_meet_name = meet_name_clean
                    else:
                        result_meet_name = meet_name_clean
            
            result_meet_city = None
            if meet_city and meet_city.strip():
                meet_city_clean = meet_city.strip()
                skip_values = ['LCM', 'SCM', 'F', 'M', 'MEETCITY', 'MEET CITY', 'CITY']
                if (meet_city_clean.upper() not in skip_values and 
                    not meet_city_clean.isdigit() and 
                    len(meet_city_clean) > 2):
                    result_meet_city = meet_city_clean
            
            result = {
                'id': str(uuid.uuid4()),
                'meet_id': meet_info['id'],  # Will be updated later when grouping by meet
                'athlete_id': athlete['id'],
                'event_id': event['id'],
                'time_seconds': time_seconds,
                'time_string': time_str,
                'time_seconds_numeric': time_seconds_numeric,
                'place': place,
                'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
                'rudolph_points': rudolph_points,
                'course': result_course,
                'result_meet_date': parsed_meet_date_for_result,
                'day_age': day_age,
                'year_age': year_age,
                # Temporary fields for grouping (will be removed after meet assignment)
                '_meet_name': result_meet_name,
                '_meet_city': result_meet_city,
                '_meet_date': parsed_meet_date_for_result
            }
            
            # Update meet info with city and name if provided (but don't change the meet ID)
            if meet_city:
                meet_info['city'] = meet_city
            # Only update meet name if it's more descriptive (has more info)
            if meet_name and meet_name.strip() and meet_name.strip() != meet_info.get('name', ''):
                # Prefer the more specific name from Excel
                if len(meet_name.strip()) > len(meet_info.get('name', '')):
                    meet_info['name'] = meet_name.strip()
            
            athletes.append(athlete)
            events.append(event)
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing row {index}: {e}")
            continue
    
    # Extract the most common meet name, city, and date from the data
    if meet_names_seen:
        # Use the most descriptive name (longest, or first non-generic one)
        sorted_names = sorted(meet_names_seen, key=lambda x: (len(x), x), reverse=True)
        extracted_meet_info['name'] = sorted_names[0]
        print(f"    Extracted meet name from data: {extracted_meet_info['name']}")
    
    if meet_cities_seen:
        extracted_meet_info['city'] = sorted(meet_cities_seen, key=lambda x: len(x), reverse=True)[0]
        print(f"    Extracted meet city from data: {extracted_meet_info['city']}")
    
    # Collect meet dates from result_meet_date column (column N, index 13)
    meet_dates_seen = set()
    from datetime import datetime
    
    # Also check the header row for the date
    if len(df.columns) > 13 and header_row < len(df):
        header_val = df.iloc[header_row, 13] if pd.notna(df.iloc[header_row, 13]) else None
        if header_val is not None:
            # Check if it's a datetime/Timestamp object
            if isinstance(header_val, (datetime, pd.Timestamp)):
                meet_dates_seen.add(header_val.strftime('%Y-%m-%d'))
            elif isinstance(header_val, str) and header_val.strip():
                date_str = header_val.strip()
                date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                        meet_dates_seen.add(parsed_date)
                        break
                    except ValueError:
                        continue
    
    # Also check data rows
    for index in range(header_row + 1, len(df)):
        row = df.iloc[index]
        if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
            continue
        if len(row) <= 13:
            continue
        result_meet_date = row.iloc[13]
        if pd.notna(result_meet_date):
            # Handle datetime/Timestamp objects directly
            if isinstance(result_meet_date, (datetime, pd.Timestamp)):
                meet_dates_seen.add(result_meet_date.strftime('%Y-%m-%d'))
            else:
                # Try string parsing
                date_str = str(result_meet_date).strip()
                if date_str and date_str != 'nan':
                    date_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S']
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                            meet_dates_seen.add(parsed_date)
                            break
                        except ValueError:
                            continue
    
    if meet_dates_seen:
        # Use the most common date
        date_counts = {}
        for date in meet_dates_seen:
            date_counts[date] = date_counts.get(date, 0) + 1
        if date_counts:
            extracted_meet_info['meet_date'] = max(date_counts.items(), key=lambda x: x[1])[0]
            print(f"    Extracted meet date from data: {extracted_meet_info['meet_date']}")
    
    return athletes, results, events, extracted_meet_info

def process_seag_file(df, meet_info, foreign_athletes, club_mapping):
    """Process SEAG file with column mapping to standard format"""
    athletes = []
    results = []
    events = []
    
    print(f"  Processing SEAG format with {len(df)} rows")
    
    # Find the header row (look for 'FULLNAME' or 'GENDER' in the data)
    header_row = 0
    for i, row in df.iterrows():
        row_values = [str(cell).strip().upper() for cell in row if pd.notna(cell)]
        if 'FULLNAME' in row_values or 'GENDER' in row_values:
            header_row = i
            break
    
    print(f"  Header row found at: {header_row}")
    
    # Extract meet info from SEAG file (meet name and city are provided, not in data rows)
    # Meet Name: "47th Southeast Asian Age Group Aquatics Championships"
    # Meet City: "Singapore"
    extracted_meet_info = {
        'name': '47th Southeast Asian Age Group Aquatics Championships',
        'city': 'Singapore'
    }
    
    # ALWAYS set SEAG meet name and city (don't check if they exist, just set them)
    meet_info['name'] = extracted_meet_info['name']
    meet_info['city'] = extracted_meet_info['city']
    
    # Process data rows starting after header
    # SEAG columns: 0=COURSE, 1=GENDER, 2=DISTANCE, 3=STROKE, 4=FULLNAME, 5=BIRTHDATE (empty), 
    #               6=NATION, 7=CLUBCODE, 8=SWIMTIME, 9=SWIMTIME_N, 10=PTS_FINA, 11=PTS_RUDOLPH,
    #               12=PLACE, 13=MEETDATE, 14=MEETCITY, 15=MEETNAME, 16=CLUBNAME, 17=REGION, 18=AGE (birthyear)
    for index in range(header_row + 1, len(df)):
        row = df.iloc[index]
        
        # Skip empty rows
        if pd.isna(row.iloc[4]) or (isinstance(row.iloc[4], str) and row.iloc[4].strip() == ''):
            continue
        
        try:
            # Map SEAG columns using positional indices
            course = 'LCM'  # SEAG is always LCM (confirmed by user)
            gender = str(row.iloc[1]).strip().upper() if pd.notna(row.iloc[1]) else ''
            distance = int(row.iloc[2]) if pd.notna(row.iloc[2]) else None
            stroke = str(row.iloc[3]).strip().upper() if pd.notna(row.iloc[3]) else ''
            name = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
            # birthdate = row.iloc[5] - not available in SEAG file, will be populated later
            nation = str(row.iloc[6]).strip().upper() if pd.notna(row.iloc[6]) else None
            club_code = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else None
            time_str = str(row.iloc[8]).strip() if pd.notna(row.iloc[8]) else ''
            time_seconds_numeric = float(row.iloc[9]) if pd.notna(row.iloc[9]) else None
            aqua_points = row.iloc[10] if pd.notna(row.iloc[10]) else None
            rudolph_points = row.iloc[11] if pd.notna(row.iloc[11]) else None
            place = int(row.iloc[12]) if pd.notna(row.iloc[12]) else None
            birthyear = int(row.iloc[18]) if pd.notna(row.iloc[18]) else None  # Column 18 is birthyear, not age
            
            if not name or name == '':
                continue
            
            # Birthdate not available in SEAG file - will be populated later from separate file
            birth_date_str = None
            
            # Calculate day_age and year_age from birthyear and meet date
            # Note: SEAG files only have birthyear, not full birthdate, so we'll use Jan 1 of birthyear
            day_age = None
            year_age = None
            if birthyear and meet_info.get('meet_date'):
                try:
                    from datetime import datetime, date
                    # Use January 1st of birthyear as approximate birthdate
                    approx_birth_date = date(birthyear, 1, 1)
                    meet_date_str = meet_info['meet_date']
                    if isinstance(meet_date_str, str):
                        meet_date = datetime.strptime(meet_date_str[:10], '%Y-%m-%d').date()
                    else:
                        meet_date = meet_date_str
                    
                    # day_age: Age on the first day of the meet
                    day_age = meet_date.year - approx_birth_date.year
                    # Adjust if birthday hasn't occurred yet this year (using Jan 1 as reference)
                    # Since we use Jan 1, age = year difference (birthday already passed)
                    
                    # year_age: Age on December 31 of the meet year
                    meet_year = meet_date.year
                    year_end = date(meet_year, 12, 31)
                    year_age = year_end.year - approx_birth_date.year
                    # Since we use Jan 1 as birthdate, birthday always passed by Dec 31
                except Exception as e:
                    day_age = None
                    year_age = None
            
            # Club name not available in SEAG file - will be populated later
            club_name = None
            
            # Check if foreign athlete
            is_foreign = name.upper() in foreign_athletes or (nation and nation not in ['MAS', 'MALAYSIA', ''])
            
            # Determine state code
            state_code = None
            if is_foreign:
                state_code = nation if nation and nation not in ['MAS', 'MALAYSIA', ''] else 'FGN'
            else:
                # For SEAG, we'll need to populate club_name later to determine state code
                state_code = 'UN'  # Unassigned for now
        
            # Extract athlete data
            # Note: Age is now calculated per result (day_age and year_age), not per athlete
            athlete = {
                'id': str(uuid.uuid4()),
                'name': name,
                'gender': gender,
                'age': year_age,  # Use year_age as approximation for athlete age (can be None)
                'birth_date': birth_date_str,  # Will be populated later
                'nation': nation,
                'club_name': None,  # Will be populated later
                'club_code': club_code,
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
            # Use time_seconds_numeric if available, otherwise calculated time_seconds
            result_time_numeric = time_seconds_numeric if time_seconds_numeric else time_seconds
            
            result = {
                'id': str(uuid.uuid4()),
                'meet_id': meet_info['id'],
                'athlete_id': athlete['id'],
                'event_id': event['id'],
                'time_seconds': time_seconds,
                'time_string': time_str,
                'time_seconds_numeric': result_time_numeric,
                'place': place,
                'aqua_points': int(aqua_points) if pd.notna(aqua_points) else None,
                'rudolph_points': float(rudolph_points) if pd.notna(rudolph_points) else None,
                'course': course,
                'result_meet_date': meet_info.get('meet_date'),
                'day_age': day_age,
                'year_age': year_age
            }
            
            athletes.append(athlete)
            events.append(event)
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing SEAG row {index}: {e}")
            continue
    
    return athletes, results, events, extracted_meet_info

def process_meet_file(file_path, meet_info, foreign_athletes, club_mapping):
    """Process a single meet file and return data for database
    Each sheet in the Excel file represents a different event in the meet"""
    print(f"Processing: {file_path.name}")
    
    all_athletes = []
    all_results = []
    all_events = []
    
    try:
        # Read all sheets in the Excel file
        if file_path.suffix == '.xlsx':
            excel_file = pd.ExcelFile(file_path)
        else:
            excel_file = pd.ExcelFile(file_path, engine='xlrd')
        
        sheet_names = excel_file.sheet_names
        print(f"  Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
        
        # Detect course (LCM vs SCM) from the data
        # Check first few sheets for course indicator
        course = 'LCM'  # Default to LCM
        for sheet_name in sheet_names[:3]:  # Check first 3 sheets
            try:
                df_sample = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd' if file_path.suffix == '.xls' else None)
                # Look for 'COURSE' column or in first row
                for i in range(min(3, len(df_sample))):
                    row_values = [str(cell).strip().upper() if pd.notna(cell) else '' for cell in df_sample.iloc[i]]
                    row_str = ' '.join(row_values)
                    if 'SCM' in row_str:
                        course = 'SCM'
                        break
                    elif 'LCM' in row_str:
                        course = 'LCM'
                        break
                if course != 'LCM':
                    break
            except:
                continue
        
        print(f"  Detected course: {course}")
        
        # Store course in meet_info so it's available throughout processing
        meet_info['course'] = course
        
        # Filter out relay events, lap events, and summary sheets
        # Skip patterns:
        # - "Lap" sheets (e.g., "50m Fr Lap")
        # - Relay sheets (e.g., "4 x 50m Fr")
        # - Summary sheets (e.g., "Top Results")
        # - 5000m Free (never valid)
        # - 100m IM when course is LCM (100m IM only exists in SCM)
        valid_sheet_names = []
        for sheet_name in sheet_names:
            sheet_lower = sheet_name.lower().strip()
            
            # Skip empty sheets or single character sheets
            if sheet_lower == '' or sheet_lower == 'x':
                print(f"    Skipping empty sheet: {sheet_name}")
                continue
            
            # Skip "Lap" sheets (these are lap splits, not final results)
            if ' lap' in sheet_lower or sheet_lower.endswith(' lap'):
                print(f"    Skipping lap sheet: {sheet_name}")
                continue
            
            # Skip relay sheets (4 x ...)
            if sheet_lower.startswith('4 x') or ' 4 x ' in sheet_lower or '4x' in sheet_lower:
                print(f"    Skipping relay sheet: {sheet_name}")
                continue
            
            # Skip summary/top results sheets
            if 'top result' in sheet_lower or 'topresults' in sheet_lower or sheet_lower == 'summary':
                print(f"    Skipping summary sheet: {sheet_name}")
                continue
            
            # Skip 5000m Free (never valid)
            if '5000' in sheet_lower and ('fr' in sheet_lower or 'free' in sheet_lower):
                print(f"    Skipping 5000m Free sheet: {sheet_name} (not a valid event)")
                continue
            
            # Skip 100m IM when course is LCM (100m IM only exists in SCM)
            if course == 'LCM' and ('100' in sheet_lower) and ('me' in sheet_lower or 'im' in sheet_lower or 'medley' in sheet_lower):
                # Make sure it's actually 100m IM, not 100m Fly, etc.
                if '100m' in sheet_lower.replace(' ', '') or '100 m' in sheet_lower:
                    # Check if it's specifically IM/medley (not other strokes)
                    if not any(stroke in sheet_lower for stroke in ['bk', 'br', 'bu', 'fly', 'back', 'breast', 'butterfly']):
                        print(f"    Skipping 100m IM sheet (LCM): {sheet_name} (100m IM only exists in SCM)")
                        continue
            
            # All other sheets should be individual events - process them
            valid_sheet_names.append(sheet_name)
        
        print(f"  Processing {len(valid_sheet_names)} valid sheet(s)")
        
        # Process each sheet as a separate event
        sheet_meet_names = set()  # Track meet names found across all sheets
        sheet_meet_dates = set()  # Track meet dates found across all sheets
        for sheet_name in valid_sheet_names:
            print(f"    Processing sheet: {sheet_name}")
            try:
                if file_path.suffix == '.xlsx':
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
                
                print(f"      Shape: {df.shape}")
                
                # Process based on file type
                if 'SEAG_2025_ALL' in file_path.name:
                    athletes, results, events, extracted_info = process_seag_file(df, meet_info, foreign_athletes, club_mapping)
                else:
                    # Pass course to standard processing function
                    athletes, results, events, extracted_info = process_standard_meet_file(df, meet_info, foreign_athletes, club_mapping, course)
                
                # Collect meet names and dates from this sheet (works for both SEAG and standard files)
                if extracted_info.get('name'):
                    sheet_meet_names.add(extracted_info['name'])
                if extracted_info.get('meet_date'):
                    sheet_meet_dates.add(extracted_info['meet_date'])
                
                all_athletes.extend(athletes)
                all_results.extend(results)
                all_events.extend(events)
                print(f"      Added {len(athletes)} athletes, {len(results)} results, {len(events)} events")
            except Exception as e:
                print(f"      Error processing sheet {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Update meet info with actual data from Excel
        # For SEAG files, the meet name was already set in process_seag_file
        if sheet_meet_names and 'SEAG' not in file_path.name:
            # If all sheets have the same meet name, use it; otherwise keep the original
            if len(sheet_meet_names) == 1:
                meet_info['name'] = list(sheet_meet_names)[0]
                print(f"  Using meet name from Excel data: {meet_info['name']}")
            else:
                # Multiple different meet names found (e.g., state meets) - keep original grouping
                print(f"  Multiple meet names found in sheets: {sheet_meet_names}")
                print(f"  Using filename-based meet name: {meet_info['name']}")
        elif 'SEAG' in file_path.name:
            print(f"  Using SEAG meet name: {meet_info['name']}, city: {meet_info.get('city')}")
        
        # Update meet date from Excel data if found
        if sheet_meet_dates:
            # Use the most common date, or first one if all are the same
            date_counts = {}
            for date in sheet_meet_dates:
                date_counts[date] = date_counts.get(date, 0) + 1
            if date_counts:
                most_common_date = max(date_counts.items(), key=lambda x: x[1])[0]
                meet_info['meet_date'] = most_common_date
                print(f"  Using meet date from Excel data: {meet_info['meet_date']}")
        else:
            print(f"  No meet date found in Excel data, using filename-based date: {meet_info.get('meet_date')}")
        
        return all_athletes, all_results, all_events
            
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
            INSERT OR IGNORE INTO meets (id, name, meet_type, meet_date, location, city)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (meet['id'], meet.get('name', ''), meet.get('meet_type'), meet.get('meet_date'), 
              meet.get('location'), meet.get('city')))
    
    # Insert athletes
    print("Inserting athletes...")
    for athlete in all_athletes:
        cursor.execute("""
            INSERT OR IGNORE INTO athletes (id, name, gender, age, birth_date, nation, club_name, club_code, is_foreign, state_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (athlete['id'], athlete['name'], athlete['gender'], athlete['age'], 
              athlete.get('birth_date'), athlete.get('nation'), athlete.get('club_name'), 
              athlete.get('club_code'), athlete['is_foreign'], athlete['state_code']))
    
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
                                          time_string, time_seconds_numeric, place, aqua_points, 
                                          rudolph_points, course, result_meet_date, day_age, year_age)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result['id'], result['meet_id'], result['athlete_id'], result['event_id'],
              result['time_seconds'], result['time_string'], result.get('time_seconds_numeric'),
              result['place'], result['aqua_points'], result.get('rudolph_points'),
              result.get('course'), result.get('result_meet_date'), 
              result.get('day_age'), result.get('year_age')))
    
    conn.commit()

def main():
    """Main conversion function"""
    print("Converting Excel meet files to SQLite (Fixed Version)...")
    
    # Get database connection
    conn = get_database_connection()
    
    # Create tables
    print("Creating database tables...")
    create_database_tables(conn)
    
    # Clear existing data before importing (to avoid duplicates from previous runs)
    print("Clearing existing data...")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM results")
    cursor.execute("DELETE FROM athletes")
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM meets")
    conn.commit()
    print("  Cleared existing data")
    
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
    
    # Group files by meet to use the same meet ID
    # For state meets, we need to check actual meet names from Excel data
    meet_id_map = {}  # Maps (meet_name, meet_date) to meet_id
    meet_info_by_id = {}  # Store meet_info by ID for later updates
    
    # Track athletes by name to reuse IDs across files
    athlete_id_map = {}  # Maps normalized_athlete_name to athlete_id
    athlete_data_map = {}  # Store athlete data by ID for reference
    
    def get_or_create_athlete_id(name, athlete_data_template):
        """Get existing athlete ID or create new one, reusing across files"""
        # Normalize name for matching (case-insensitive, strip whitespace)
        normalized_name = str(name).strip().upper()
        
        if normalized_name in athlete_id_map:
            return athlete_id_map[normalized_name]
        else:
            # Create new athlete ID and store
            athlete_id = str(uuid.uuid4())
            athlete_id_map[normalized_name] = athlete_id
            # Store the athlete data (use template as base, update name)
            athlete_data = athlete_data_template.copy()
            athlete_data['id'] = athlete_id
            athlete_data['name'] = name  # Keep original name casing
            athlete_data_map[athlete_id] = athlete_data
            return athlete_id
    
    for file_path in excel_files:
        if 'Malaysia On Track Times Spreadsheet Workbook' in file_path.name:
            continue  # Skip the source workbook
            
        meet_info = extract_meet_info(file_path.name)
        
        # For state meets with multiple actual meet names, we keep them grouped under "State Championships 2024"
        # but store the individual meet names in the database
        # For regular meets (MIAG, MO, SUKMA), combine Men's and Women's files using filename-based meet name
        
        # Set a temporary ID first (needed for process_meet_file)
        temp_meet_id = str(uuid.uuid4())
        meet_info['id'] = temp_meet_id
        
        # Process file to get actual meet name and date from Excel data
        athletes, results, events = process_meet_file(file_path, meet_info, foreign_athletes, club_mapping)
        
        # Use actual meet_date (from Excel if extracted, otherwise from filename)
        actual_meet_date = meet_info.get('meet_date', '2024-01-01')  # Fallback if no date found
        
        # Check if results have individual meet names (e.g., multiple state meets in one workbook)
        has_individual_meets = any(r.get('_meet_name') for r in results)
        
        if not has_individual_meets:
            # Single meet per file - handle deduplication as before
            # Now create meet_key with the ACTUAL date from Excel (or filename date if not found)
            normalized_meet_name = meet_info['name']
            # Remove gender suffixes if present (e.g., "SUKMA 2024 Men" -> "SUKMA 2024")
            normalized_meet_name = normalized_meet_name.replace(' Men', '').replace(' Women', '').replace(' Men\'s', '').replace(' Women\'s', '').strip()
            
            meet_key = (normalized_meet_name, actual_meet_date)
            
            # If this meet already exists, reuse the ID; otherwise use the temp ID
            if meet_key not in meet_id_map:
                # New meet - use the temp ID we already created
                meet_id_map[meet_key] = temp_meet_id
                meet_info_by_id[temp_meet_id] = meet_info.copy()
                all_meets.append(meet_info.copy())
            else:
                # Existing meet - update all result meet_ids to use the existing ID
                existing_meet_id = meet_id_map[meet_key]
                for result in results:
                    result['meet_id'] = existing_meet_id
                
                meet_info['id'] = existing_meet_id
                # Update existing meet info with any new data (city, name, date)
                existing_meet = meet_info_by_id[existing_meet_id]
                if meet_info.get('city') and not existing_meet.get('city'):
                    existing_meet['city'] = meet_info['city']
                if meet_info.get('name') and len(meet_info['name']) > len(existing_meet.get('name', '')):
                    existing_meet['name'] = meet_info['name']
                # Update date if we got a better one from Excel
                if actual_meet_date and actual_meet_date != existing_meet.get('meet_date'):
                    existing_meet['meet_date'] = actual_meet_date
                # Update the meet in all_meets too
                for m in all_meets:
                    if m['id'] == existing_meet_id:
                        m.update(existing_meet)
                        break
        
        # Group results by actual meet name/city if they have _meet_name set
        # This handles cases where one workbook contains multiple meets (e.g., state meets)
        # Note: We group by name+city only (not date) to avoid splitting multi-day meets
        if any(r.get('_meet_name') for r in results):
            # Group results by meet info (name + city, but not date to allow multi-day meets)
            from collections import defaultdict
            meet_groups = defaultdict(list)
            meet_date_ranges = defaultdict(list)  # Track dates for each meet to use earliest
            
            for result in results:
                meet_key = (
                    result.get('_meet_name') or meet_info['name'],
                    result.get('_meet_city') or meet_info.get('city', '')
                )
                meet_groups[meet_key].append(result)
                # Track the date for this result
                result_date = result.get('_meet_date') or actual_meet_date
                if result_date:
                    meet_date_ranges[meet_key].append(result_date)
            
            # Create separate meet records for each group
            for (group_meet_name, group_meet_city), group_results in meet_groups.items():
                # Determine the meet date (use earliest date from date range, or most common)
                group_meet_key_temp = (group_meet_name, group_meet_city)
                dates_for_meet = meet_date_ranges.get(group_meet_key_temp, [])
                if dates_for_meet:
                    # Use earliest date for the meet (first day of multi-day meet)
                    group_meet_date = sorted(set(dates_for_meet))[0]
                else:
                    group_meet_date = actual_meet_date
                
                # Create normalized meet key for deduplication (name + city only, not date)
                # This ensures multi-day meets are combined into a single meet record
                normalized_group_name = group_meet_name.replace(' Men', '').replace(' Women', '').replace(' Men\'s', '').replace(' Women\'s', '').strip()
                normalized_group_city = (group_meet_city or '').strip()
                group_meet_key = (normalized_group_name, normalized_group_city)
                
                # Get or create meet ID for this group
                if group_meet_key not in meet_id_map:
                    group_meet_id = str(uuid.uuid4())
                    meet_id_map[group_meet_key] = group_meet_id
                    
                    # Create meet info for this group
                    group_meet_info = {
                        'id': group_meet_id,
                        'name': group_meet_name,
                        'city': group_meet_city if group_meet_city else meet_info.get('city', ''),
                        'meet_date': group_meet_date,
                        'course': meet_info.get('course', 'LCM'),
                        'meet_type': meet_info.get('meet_type', 'Unknown')
                    }
                    meet_info_by_id[group_meet_id] = group_meet_info
                    all_meets.append(group_meet_info.copy())
                else:
                    group_meet_id = meet_id_map[group_meet_key]
                    # Update existing meet info if we have better data
                    existing_meet = meet_info_by_id[group_meet_id]
                    if group_meet_city and not existing_meet.get('city'):
                        existing_meet['city'] = group_meet_city
                    if len(group_meet_name) > len(existing_meet.get('name', '')):
                        existing_meet['name'] = group_meet_name
                    # Update date if we found an earlier date (for multi-day meets)
                    existing_date = existing_meet.get('meet_date')
                    if group_meet_date and existing_date:
                        if group_meet_date < existing_date:
                            existing_meet['meet_date'] = group_meet_date
                    elif group_meet_date and not existing_date:
                        existing_meet['meet_date'] = group_meet_date
                
                # Update all results in this group to use the correct meet_id
                for result in group_results:
                    result['meet_id'] = group_meet_id
                    # Remove temporary fields
                    result.pop('_meet_name', None)
                    result.pop('_meet_city', None)
                    result.pop('_meet_date', None)
        else:
            # No meet-specific grouping, use the file-level meet
            # Remove temporary fields if they exist
            for result in results:
                result.pop('_meet_name', None)
                result.pop('_meet_city', None)
                result.pop('_meet_date', None)
        
        # Reuse athlete IDs across files - update athlete IDs and result references
        athlete_id_updates = {}  # Map old_id -> new_id
        for athlete in athletes:
            old_id = athlete['id']
            new_id = get_or_create_athlete_id(athlete['name'], athlete)
            athlete_id_updates[old_id] = new_id
            athlete['id'] = new_id  # Update athlete ID
        
        # Update result athlete_ids to use deduplicated IDs
        for result in results:
            old_athlete_id = result['athlete_id']
            if old_athlete_id in athlete_id_updates:
                result['athlete_id'] = athlete_id_updates[old_athlete_id]
        
        # Only add unique athletes to list (by ID now, since IDs are deduplicated)
        for athlete in athletes:
            if athlete['id'] not in {a['id'] for a in all_athletes}:
                all_athletes.append(athlete)
        
        all_results.extend(results)
        all_events.extend(events)
        
        print(f"  Processed {len(athletes)} athletes, {len(results)} results, {len(events)} events")
    
    # Athletes are already deduplicated by ID (reused across files)
    # But remove any remaining duplicates by ID just to be safe
    unique_athletes = []
    seen_ids = set()
    for athlete in all_athletes:
        if athlete['id'] not in seen_ids:
            unique_athletes.append(athlete)
            seen_ids.add(athlete['id'])
    
    # Deduplicate events and create mapping from old IDs to new IDs
    unique_events = []
    seen_events = {}  # Map event_key -> event_id
    event_id_updates = {}  # Map old_event_id -> new_event_id
    
    for event in all_events:
        event_key = f"{event['distance']}_{event['stroke']}_{event['gender']}"
        if event_key not in seen_events:
            # First time seeing this event - add it to unique_events and track its ID
            unique_events.append(event)
            seen_events[event_key] = event['id']
        else:
            # Event already exists - map old ID to existing ID
            existing_event_id = seen_events[event_key]
            event_id_updates[event['id']] = existing_event_id
    
    # Update result event_ids to use deduplicated event IDs
    for result in all_results:
        old_event_id = result['event_id']
        if old_event_id in event_id_updates:
            result['event_id'] = event_id_updates[old_event_id]
    
    print(f"\nTotal unique athletes: {len(unique_athletes)}")
    print(f"Total unique events: {len(unique_events)}")
    print(f"Total results: {len(all_results)}")
    print(f"Total meets before deduplication: {len(all_meets)}")
    
    # Deduplicate meets by ID (should already be unique, but double-check)
    unique_meets = {}
    for meet in all_meets:
        if meet['id'] not in unique_meets:
            unique_meets[meet['id']] = meet
    
    unique_meets_list = list(unique_meets.values())
    print(f"Total unique meets: {len(unique_meets_list)}")
    
    # Insert data
    print("\nInserting data into database...")
    insert_data(conn, unique_athletes, all_results, unique_events, unique_meets_list)
    
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







