#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - Club Info Converter

Converts Clubs_By_State.xlsx to SQLite database tables for states and clubs.

Excel File Structure Expected:
- Multiple sheets, each named with a 3-letter state code (e.g., "KL", "SGR", "JHR")
- Each sheet contains club names in the first column (column 0, index 0)
- The sheet name is the state code (alias)
- We need to extract:
  - State long name (need to determine from context or user input)
  - State alias (3-letter code from sheet name)
  - Club long name (from first column)
  - Club alias (may need to be determined or generated)

For now, on first upload:
- Extract states from sheet names (3-letter codes)
- Extract club names from first column of each sheet
- Store state code (alias) and club name
- We'll add state long name and club alias later
"""

import pandas as pd
import sqlite3
from pathlib import Path
import uuid

def get_database_connection():
    """Get SQLite database connection - same as convert_meets_to_sqlite_simple"""
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "swimming_analytics.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def create_club_tables(conn):
    """Create states and clubs tables if they don't exist"""
    cursor = conn.cursor()
    
    # Create states table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS states (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create clubs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            alias TEXT,
            state_code TEXT NOT NULL,
            state_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (state_id) REFERENCES states(id)
        )
    """)
    
    # Create indexes
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clubs_state_code ON clubs(state_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clubs_name ON clubs(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_states_code ON states(code)")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()

def process_clubs_file(file_path):
    """
    Process Clubs_By_State.xlsx file and return states and clubs data
    
    Expected structure:
    - Multiple sheets, each named with a state code (2-3 letters, e.g., "KL", "SGR")
    - Each sheet should have club names in first column, codes in second (optional), state in third (optional)
    
    Returns:
        dict with 'states' and 'clubs' lists
    """
    states = []
    clubs = []
    
    try:
        print(f"[club converter] Opening file: {file_path}")
        excel_file = pd.ExcelFile(file_path, engine='xlrd' if str(file_path).endswith('.xls') else None)
        sheet_names = excel_file.sheet_names
        
        print(f"[club converter] Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
        
        # Validate this looks like a clubs file (should have state code sheet names)
        # Check if this might be a meet results file instead (has sheets like "50m Fr", "100m Fr", etc.)
        meet_indicators = ['50M', '100M', '200M', '400M', '800M', '1500M', 'FR', 'BK', 'BR', 'BU', 'ME', 'IM']
        has_meet_indicators = any(any(ind in str(s).upper() for ind in meet_indicators) for s in sheet_names[:3])
        
        state_code_sheets = [s for s in sheet_names if len(str(s).strip().upper()) >= 2 and len(str(s).strip().upper()) <= 3]
        if len(state_code_sheets) == 0:
            if has_meet_indicators:
                raise ValueError("This appears to be a meet results file, not a Clubs_By_State file. Please upload this to the 'Upload & Convert Meet' tab instead. Clubs_By_State files should have sheets named with state codes (e.g., 'KL', 'SGR', 'JHR').")
            raise ValueError("This doesn't appear to be a Clubs_By_State file. Expected sheets with 2-3 letter state codes (e.g., 'KL', 'SGR'), but found: " + ", ".join(sheet_names[:5]))
        
        for sheet_name in sheet_names:
            # Skip non-state sheets (state codes are typically 2-3 characters)
            sheet_name_clean = str(sheet_name).strip().upper()
            
            # Only process sheets that look like state codes (2-3 uppercase letters)
            if len(sheet_name_clean) < 2 or len(sheet_name_clean) > 3:
                print(f"    Skipping sheet '{sheet_name}' (doesn't look like a state code)")
                continue
            
            # This is a state code (alias)
            state_code = sheet_name_clean
            
            # Create state record (name will be populated later)
            state_id = str(uuid.uuid4())
            state = {
                'id': state_id,
                'code': state_code,
                'name': None  # Will be populated later
            }
            states.append(state)
            
            # Read the sheet
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='xlrd' if str(file_path).endswith('.xls') else None)
                print(f"[club converter]    Processing sheet '{sheet_name}' with {len(df)} rows")
                
                # Extract club names from first column (index 0)
                # If second column exists, use it as club code/alias
                # If third column exists, use it as state (but we already have state from sheet name)
                for idx, row in df.iterrows():
                    try:
                        # Skip header rows (row 0 might be headers)
                        if idx == 0:
                            # Check if this looks like a header row
                            first_val = str(row.iloc[0]).strip().upper() if len(row) > 0 else ''
                            if first_val in ['CLUB', 'CLUB NAME', 'NAME', 'TEAM', 'TEAM NAME']:
                                continue
                        
                        club_name_cell = row.iloc[0] if len(row) > 0 else None
                        club_code_cell = row.iloc[1] if len(row) > 1 else None
                        
                        if pd.notna(club_name_cell):
                            club_name = str(club_name_cell).strip()
                            
                            # Skip empty or header-like rows
                            if (club_name and 
                                club_name.upper() not in ['CLUB', 'CLUB NAME', 'NAME', 'TEAM', 'TEAM NAME', ''] and
                                len(club_name) > 1):
                                
                                club_code = None
                                if pd.notna(club_code_cell):
                                    club_code = str(club_code_cell).strip()
                                
                                club = {
                                    'id': str(uuid.uuid4()),
                                    'name': club_name,
                                    'alias': club_code,  # Use second column as alias/code
                                    'state_code': state_code,
                                    'state_id': state_id
                                }
                                clubs.append(club)
                                print(f"[club converter]      Added club: {club_name} ({club_code or 'no code'})")
                    except Exception as e:
                        print(f"[club converter]      Error processing row {idx} in sheet {sheet_name}: {e}")
                        continue
                        
            except Exception as e:
                print(f"[club converter]    Error reading sheet '{sheet_name}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[club converter] Extracted {len(states)} states and {len(clubs)} clubs")
        
    except ValueError as ve:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        print(f"[club converter] Error processing file: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    return {'states': states, 'clubs': clubs}

def insert_club_data(conn, states, clubs):
    """
    Insert states and clubs into database
    
    Returns:
        dict with counts of inserted/skipped states and clubs
    """
    cursor = conn.cursor()
    
    # Ensure tables exist
    create_club_tables(conn)
    
    # Insert states
    inserted_states = 0
    skipped_states = 0
    
    for state in states:
        # Check if state code already exists
        cursor.execute("SELECT id FROM states WHERE code = ?", (state['code'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing state (keep existing ID)
            state['id'] = existing[0]
            cursor.execute("""
                UPDATE states 
                SET name = COALESCE(?, name)
                WHERE code = ?
            """, (state['name'], state['code']))
            skipped_states += 1
        else:
            # Insert new state
            cursor.execute("""
                INSERT INTO states (id, code, name)
                VALUES (?, ?, ?)
            """, (state['id'], state['code'], state['name']))
            inserted_states += 1
    
    # Insert clubs
    inserted_clubs = 0
    skipped_clubs = 0
    
    for club in clubs:
        # Check if club already exists (same name and state)
        cursor.execute("""
            SELECT id FROM clubs 
            WHERE name = ? AND state_code = ?
        """, (club['name'], club['state_code']))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing club (keep existing ID)
            club['id'] = existing[0]
            cursor.execute("""
                UPDATE clubs 
                SET alias = COALESCE(?, alias),
                    state_id = ?
                WHERE name = ? AND state_code = ?
            """, (club['alias'], club['state_id'], club['name'], club['state_code']))
            skipped_clubs += 1
        else:
            # Insert new club
            cursor.execute("""
                INSERT INTO clubs (id, name, alias, state_code, state_id)
                VALUES (?, ?, ?, ?, ?)
            """, (club['id'], club['name'], club['alias'], club['state_code'], club['state_id']))
            inserted_clubs += 1
    
    conn.commit()
    
    return {
        'inserted_states': inserted_states,
        'skipped_states': skipped_states,
        'inserted_clubs': inserted_clubs,
        'skipped_clubs': skipped_clubs
    }

# Test function
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
        if file_path.exists():
            conn = get_database_connection()
            data = process_clubs_file(file_path)
            result = insert_club_data(conn, data['states'], data['clubs'])
            print(f"\n✅ Inserted: {result['inserted_states']} states, {result['inserted_clubs']} clubs")
            print(f"   Skipped: {result['skipped_states']} states, {result['skipped_clubs']} clubs")
            conn.close()
        else:
            print(f"File not found: {file_path}")
    else:
        print("Usage: python convert_clubs_to_sqlite.py <path_to_Clubs_By_State.xlsx>")

