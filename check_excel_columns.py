#!/usr/bin/env python3
"""Check what columns are in Excel files vs what we're storing"""

import pandas as pd
from pathlib import Path

meets_dir = Path('data/meets')
excel_files = [f for f in meets_dir.glob('*.xls*') if 'Malaysia On Track' not in f.name]

if not excel_files:
    print("No Excel files found!")
    exit()

# Check first standard format file
standard_file = None
for f in excel_files:
    if 'SEAG' not in f.name:
        standard_file = f
        break

if not standard_file:
    print("No standard format file found!")
    exit()

print(f"Checking: {standard_file.name}\n")

# Read Excel
if standard_file.suffix == '.xlsx':
    df = pd.read_excel(standard_file)
else:
    df = pd.read_excel(standard_file, engine='xlrd')

print(f"Total columns in file: {len(df.columns)}\n")

# Find header row
header_row = 0
for i, row in df.iterrows():
    if any(str(cell).strip().upper() == 'GENDER' for cell in row if pd.notna(cell)):
        header_row = i
        break

print(f"Header row: {header_row}\n")
print("Column mapping (index: Excel header → Currently stored):")
print("-" * 70)

# Get header row
header = df.iloc[header_row]

# Based on process_standard_meet_file mapping:
mapping = {
    0: "Unknown",
    1: "GENDER → athletes.gender",
    2: "DISTANCE → events.distance",
    3: "STROKE → events.stroke",
    4: "NAME → athletes.name",
    5: "BIRTHDATE → athletes.birth_date (NOW STORED)",
    6: "NATION → Used for is_foreign check (NOT STORED)",
    7: "Unknown",
    8: "TIME → results.time_string, results.time_seconds",
    9: "Unknown",
    10: "AQUA POINTS → results.aqua_points",
    11: "Unknown",
    12: "PLACE → results.place",
    13: "Unknown",
    14: "Unknown",
    15: "Unknown",
    16: "CLUB → Used for state_code mapping (NOT STORED)",
    17: "Unknown",
}

for idx in range(min(20, len(header))):  # Check first 20 columns
    excel_val = str(header.iloc[idx]) if pd.notna(header.iloc[idx]) else ""
    stored = mapping.get(idx, "NOT USED")
    print(f"{idx:2d}: {excel_val:30s} → {stored}")

# Show sample data row
print("\n" + "=" * 70)
print("Sample data row (first non-empty after header):")
print("-" * 70)
for idx in range(header_row + 1, min(header_row + 5, len(df))):
    row = df.iloc[idx]
    if pd.notna(row.iloc[4]):  # Has a name
        print(f"\nRow {idx}:")
        for col_idx in range(min(18, len(row))):
            val = row.iloc[col_idx]
            if pd.notna(val) and str(val).strip():
                header_val = str(header.iloc[col_idx]) if col_idx < len(header) else f"Col{col_idx}"
                print(f"  {col_idx:2d} ({header_val[:20]:20s}): {val}")
        break














