#!/usr/bin/env python3
"""
Convert AthleteINFO.csv to SQLite and update athletes table with birthdates.
Athlete ID format: First 2 letters of surname + 8-digit birthdate (YYYYMMDD, leading zero for months <10)
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import re

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
ATHLETEINFO_CSV = PROJECT_ROOT / "data" / "athletes" / "AthleteINFO.csv"
DATABASE_PATH = PROJECT_ROOT / "malaysia_swimming.db"

def create_athleteinfo_table(conn):
    """Create athleteinfo table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS athleteinfo (
            athlete_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            birthdate TEXT,
            gender TEXT,
            club_name TEXT,
            raw_data TEXT  -- Store full row as JSON for reference
        )
    """)
    conn.commit()

def extract_birthdate_from_id(athlete_id):
    """Extract birthdate from Athlete ID format: First 2 letters + 8-digit birthdate
    
    The birthdate in the ID could be in DDMMYYYY format (based on CSV data).
    We'll try both DDMMYYYY and YYYYMMDD formats.
    """
    if pd.isna(athlete_id) or athlete_id == '':
        return None
    
    athlete_id = str(athlete_id).strip()
    # Athlete ID format: 2 letters + 8 digits
    # Example: AL07042008 (DDMMYYYY) or AB20080704 (YYYYMMDD)
    match = re.match(r'^[A-Z]{2}(\d{8})$', athlete_id.upper())
    if match:
        date_str = match.group(1)  # 8 digits
        
        # Try DDMMYYYY format first (most likely based on CSV data)
        try:
            day = date_str[:2]
            month = date_str[2:4]
            year = date_str[4:8]
            datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            return f"{year}-{month}-{day}"
        except ValueError:
            pass
        
        # Try YYYYMMDD format as fallback
        try:
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            return f"{year}-{month}-{day}"
        except ValueError:
            pass
    
    return None

def parse_birthdate(birthdate_value, athlete_id=None):
    """Parse birthdate from various formats, with fallback to athlete_id
    
    The birthdate column typically contains DDMMYYYY format (e.g., "07042008" = 07/04/2008)
    """
    # Try to extract from athlete_id first if birthdate_value is empty
    if pd.isna(birthdate_value) or birthdate_value == '' or str(birthdate_value).strip() == '':
        if athlete_id:
            return extract_birthdate_from_id(athlete_id)
        return None
    
    birthdate_str = str(birthdate_value).strip()
    
    # Remove leading zeros if it's a number and has leading zeros that might be padding
    # But be careful - if it's exactly 8 digits, try DDMMYYYY first
    
    # Try DDMMYYYY format first (most common based on CSV)
    if len(birthdate_str) == 8 and birthdate_str.isdigit():
        try:
            day = birthdate_str[:2]
            month = birthdate_str[2:4]
            year = birthdate_str[4:8]
            dt = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Try various other date formats
    date_formats = [
        '%Y-%m-%d',      # 2025-01-15
        '%Y/%m/%d',      # 2025/01/15
        '%d/%m/%Y',      # 15/01/2025
        '%d.%m.%Y',      # 15.01.2025
        '%d-%m-%Y',      # 15-01-2025
        '%m/%d/%Y',      # 01/15/2025
        '%Y%m%d',        # 20250115
        '%d%m%Y',        # 15012025 (if not 8 digits)
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(birthdate_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If no format worked, try extracting from athlete_id
    if athlete_id:
        return extract_birthdate_from_id(athlete_id)
    
    return None

def load_athleteinfo_to_sqlite():
    """Load AthleteINFO.csv into SQLite athleteinfo table"""
    print(f"Loading AthleteINFO from: {ATHLETEINFO_CSV}")
    
    if not ATHLETEINFO_CSV.exists():
        print(f"❌ Error: AthleteINFO.csv not found at {ATHLETEINFO_CSV}")
        return False
    
    # Read CSV
    try:
        df = pd.read_csv(ATHLETEINFO_CSV, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(ATHLETEINFO_CSV, encoding='latin-1')
    
    print(f"Loaded {len(df)} rows from AthleteINFO.csv")
    print(f"Columns: {df.columns.tolist()}")
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    create_athleteinfo_table(conn)
    
    cursor = conn.cursor()
    
    # Get column indices (0-based)
    # Column 1 = index 0: Athlete ID
    # Column 2 = index 1: Name
    # Column 3 = index 2: Birthdate
    # Column 4 = index 3: Gender
    # Column 5 = index 4: Club name
    
    inserted = 0
    updated = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Get values (handle missing columns gracefully)
            athlete_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) and len(row) > 0 else None
            name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) and len(row) > 1 else None
            birthdate_col = row.iloc[2] if len(row) > 2 else None
            gender = str(row.iloc[3]).strip().upper() if pd.notna(row.iloc[3]) and len(row) > 3 else None
            club_name = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) and len(row) > 4 else None
            
            if not athlete_id or not name:
                continue
            
            # Parse birthdate (try column 3 first, then extract from athlete_id)
            birthdate = parse_birthdate(birthdate_col, athlete_id)
            
            # Store raw data as JSON string for reference
            import json
            raw_data = json.dumps(row.to_dict(), default=str)
            
            # Insert or update
            cursor.execute("""
                INSERT OR REPLACE INTO athleteinfo 
                (athlete_id, name, birthdate, gender, club_name, raw_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (athlete_id, name, birthdate, gender, club_name, raw_data))
            
            inserted += 1
            
        except Exception as e:
            print(f"  Error processing row {idx}: {e}")
            errors += 1
            continue
    
    conn.commit()
    
    print(f"\n✅ AthleteINFO loaded successfully!")
    print(f"   Inserted/Updated: {inserted}")
    print(f"   Errors: {errors}")
    
    # Show sample data
    cursor.execute("SELECT COUNT(*) FROM athleteinfo")
    count = cursor.fetchone()[0]
    print(f"   Total records in athleteinfo table: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM athleteinfo WHERE birthdate IS NOT NULL")
    with_birthdate = cursor.fetchone()[0]
    print(f"   Records with birthdate: {with_birthdate} ({with_birthdate/count*100:.1f}%)")
    
    # Show sample records
    cursor.execute("SELECT athlete_id, name, birthdate, gender FROM athleteinfo LIMIT 5")
    print("\n   Sample records:")
    for row in cursor.fetchall():
        print(f"     {row}")
    
    conn.close()
    return True

def normalize_name(name):
    """Normalize name for matching (handle order variations, capitalization, punctuation)"""
    if not name:
        return ""
    
    # Convert to uppercase and strip
    name = str(name).strip().upper()
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Remove common punctuation
    name = name.replace(',', ' ')
    name = name.replace('.', ' ')
    name = name.replace('-', ' ')
    name = name.replace("'", '')
    name = name.replace('"', '')
    
    # Remove extra spaces again
    name = ' '.join(name.split())
    
    return name

def create_name_variations(name):
    """Create name variations for matching (handle different name orders)"""
    normalized = normalize_name(name)
    if not normalized:
        return []
    
    # Split into parts
    parts = normalized.split()
    
    variations = []
    # Add original normalized
    variations.append(normalized)
    
    # If there are at least 2 parts, try different orders
    if len(parts) >= 2:
        # "LAST, FIRST" -> "FIRST LAST"
        variations.append(' '.join(reversed(parts)))
        # "FIRST LAST" -> "LAST FIRST"
        variations.append(' '.join(parts))
        
        # For names with 3+ parts, try various combinations
        if len(parts) >= 3:
            # Try moving first part to end
            variations.append(' '.join(parts[1:] + parts[0:1]))
            # Try moving last part to beginning
            variations.append(' '.join(parts[-1:] + parts[:-1]))
    
    return list(set(variations))  # Remove duplicates

def update_athletes_table_with_birthdates():
    """Update athletes table birthdates by matching names with athleteinfo
    
    Handles name variations:
    - Case-insensitive matching
    - Name order variations (LAST, FIRST vs FIRST LAST)
    - Punctuation differences
    """
    print("\n" + "="*60)
    print("Updating athletes table with birthdates from AthleteINFO...")
    print("="*60)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all athletes without birthdates
    cursor.execute("""
        SELECT id, name, gender 
        FROM athletes 
        WHERE birth_date IS NULL OR birth_date = ''
    """)
    athletes_to_update = cursor.fetchall()
    
    print(f"Found {len(athletes_to_update)} athletes without birthdates")
    
    # Get all athleteinfo records with birthdates
    cursor.execute("""
        SELECT name, birthdate, gender 
        FROM athleteinfo 
        WHERE birthdate IS NOT NULL AND birthdate != ''
    """)
    athleteinfo_records = cursor.fetchall()
    
    print(f"Found {len(athleteinfo_records)} AthleteINFO records with birthdates")
    
    # Create lookup dictionary with name variations
    # Key: normalized name variation, Value: (original_name, birthdate)
    birthdate_lookup = {}
    for name, birthdate, gender in athleteinfo_records:
        variations = create_name_variations(name)
        for variation in variations:
            if variation not in birthdate_lookup:
                birthdate_lookup[variation] = (name, birthdate)
            # Keep first match if duplicates
    
    print(f"Created {len(birthdate_lookup)} name variation lookups")
    
    updated = 0
    not_found = 0
    matches = []
    
    for athlete_id, name, gender in athletes_to_update:
        variations = create_name_variations(name)
        matched = False
        
        for variation in variations:
            if variation in birthdate_lookup:
                original_name, birthdate = birthdate_lookup[variation]
                cursor.execute("""
                    UPDATE athletes 
                    SET birth_date = ? 
                    WHERE id = ?
                """, (birthdate, athlete_id))
                updated += 1
                matches.append((name, original_name, birthdate))
                matched = True
                break
        
        if not matched:
            not_found += 1
    
    conn.commit()
    
    print(f"\n✅ Birthdate update complete!")
    print(f"   Updated: {updated} athletes")
    print(f"   Not found in AthleteINFO: {not_found}")
    
    # Show some sample matches
    if matches:
        print(f"\n   Sample matches (first 5):")
        for db_name, info_name, bdate in matches[:5]:
            print(f"     '{db_name}' -> '{info_name}' ({bdate})")
    
    # Check final statistics
    cursor.execute("SELECT COUNT(*) FROM athletes WHERE birth_date IS NOT NULL AND birth_date != ''")
    with_birthdate = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM athletes")
    total = cursor.fetchone()[0]
    print(f"\n   Total athletes with birthdates: {with_birthdate}/{total} ({with_birthdate/total*100:.1f}%)")
    
    # Check specifically for SEAG athletes
    cursor.execute("""
        SELECT COUNT(*) FROM athletes 
        WHERE (birth_date IS NOT NULL AND birth_date != '')
        AND id IN (
            SELECT DISTINCT athlete_id FROM results 
            WHERE meet_id IN (
                SELECT id FROM meets WHERE name LIKE '%SEAG%' OR name LIKE '%Southeast Asian%'
            )
        )
    """)
    seag_with_birthdate = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM athletes 
        WHERE id IN (
            SELECT DISTINCT athlete_id FROM results 
            WHERE meet_id IN (
                SELECT id FROM meets WHERE name LIKE '%SEAG%' OR name LIKE '%Southeast Asian%'
            )
        )
    """)
    total_seag = cursor.fetchone()[0]
    
    if total_seag > 0:
        print(f"   SEAG athletes with birthdates: {seag_with_birthdate}/{total_seag} ({seag_with_birthdate/total_seag*100:.1f}%)")
    
    conn.close()
    return updated

def main():
    """Main function"""
    print("="*60)
    print("AthleteINFO to SQLite Conversion")
    print("="*60)
    
    # Step 1: Load AthleteINFO to SQLite
    if not load_athleteinfo_to_sqlite():
        print("❌ Failed to load AthleteINFO")
        return
    
    # Step 2: Update athletes table with birthdates
    updated = update_athletes_table_with_birthdates()
    
    print("\n" + "="*60)
    print(f"✅ Conversion complete! Updated {updated} athletes with birthdates.")
    print("="*60)

if __name__ == "__main__":
    main()

