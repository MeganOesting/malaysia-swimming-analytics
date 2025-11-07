"""Test SEAG file conversion specifically"""
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from convert_meets_to_sqlite_fixed import process_seag_file, extract_meet_info, get_database_connection, create_database_tables, load_foreign_athletes, load_club_mapping
import pandas as pd
import sqlite3

# Test SEAG file processing
seag_file = Path('data/meets/SEAG_2025_ALL.xlsx')
print(f"Testing SEAG file: {seag_file}")

# Load foreign athletes and club mapping
foreign_athletes = load_foreign_athletes()
club_mapping = load_club_mapping()

# Extract meet info from filename
meet_info = extract_meet_info(seag_file.name)
print(f"Extracted meet info: {meet_info}")

# Read the Excel file
print("\nReading SEAG file...")
df = pd.read_excel(seag_file, sheet_name='Sheet', header=None)
print(f"Loaded {len(df)} rows")

# Process SEAG file
print("\nProcessing SEAG file...")
athletes, results, events, extracted_info = process_seag_file(df, meet_info, foreign_athletes, club_mapping)

print(f"\nResults:")
print(f"  Athletes: {len(athletes)}")
print(f"  Results: {len(results)}")
print(f"  Events: {len(events)}")
print(f"  Extracted meet info: {extracted_info}")

if len(athletes) > 0:
    print(f"\nSample athlete: {athletes[0]}")
if len(results) > 0:
    print(f"Sample result: {results[0]}")














