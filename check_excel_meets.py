#!/usr/bin/env python3
"""Check what meets are in the Excel file - using same method as conversion script"""

import pandas as pd

file_path = r'C:\Users\megan\Downloads\MAS_2025_LCM_Men (9).xls'

print(f'Reading file: {file_path}')
print('=' * 80)

xl = pd.ExcelFile(file_path)
print(f'Total sheets: {len(xl.sheet_names)}')

all_meet_names = set()
all_meet_cities = set()
all_meet_dates = set()

for sheet_name in xl.sheet_names:
    try:
        # Read without header first to check structure
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Find header row (contains 'GENDER')
        header_row = None
        for i in [1, 0, 2]:
            if i < len(df):
                row = df.iloc[i]
                if any(str(cell).strip().upper() == 'GENDER' for cell in row if pd.notna(cell)):
                    header_row = i
                    break
        
        if header_row is None:
            print(f'  Sheet {sheet_name}: No header row found, skipping')
            continue
        
        # Process data rows starting after header
        for index in range(header_row + 1, len(df)):
            row = df.iloc[index]
            
            # Skip empty rows
            if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
                continue
            
            # Column 15 (index 15) is MEETNAME
            # Column 14 (index 14) is MEETCITY
            # Column 13 (index 13) is MEETDATE (result_meet_date)
            
            if len(row) > 15:
                meet_name = str(row.iloc[15]).strip() if pd.notna(row.iloc[15]) else ''
                meet_city = str(row.iloc[14]).strip() if pd.notna(row.iloc[14]) else ''
                meet_date = row.iloc[13] if pd.notna(row.iloc[13]) else None
                
                # Filter out obvious non-meet-name values
                skip_values = ['LCM', 'SCM', 'F', 'M', 'MEETNAME', 'COURSE', 'GENDER', 'DISTANCE', 'STROKE', 'NAME', 'BIRTHDATE', 'nan', '']
                
                if meet_name and meet_name.upper() not in skip_values and len(meet_name) > 5:
                    all_meet_names.add(meet_name)
                
                if meet_city and meet_city.upper() not in skip_values and len(meet_city) > 2:
                    all_meet_cities.add(meet_city)
                
                if meet_date and str(meet_date) not in ['nan', '']:
                    all_meet_dates.add(str(meet_date))
                    
    except Exception as e:
        print(f'Error processing sheet {sheet_name}: {e}')
        continue

print(f'\nUnique Meet Names ({len(all_meet_names)}):')
print('=' * 80)
for name in sorted(all_meet_names):
    print(f'  - {name}')

print(f'\nUnique Meet Cities ({len(all_meet_cities)}):')
print('=' * 80)
for city in sorted(all_meet_cities):
    print(f'  - {city}')

print(f'\nUnique Meet Dates ({len(all_meet_dates)}):')
print('=' * 80)
for date in sorted(all_meet_dates):
    print(f'  - {date}')

print('\n' + '=' * 80)
print('\nNow checking what meets are in the database...')
print('=' * 80)

import sqlite3
conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()
cursor.execute('SELECT name, meet_date, city FROM meets ORDER BY meet_date DESC')
db_meets = cursor.fetchall()

print(f'\nMeets in database ({len(db_meets)}):')
for meet in db_meets:
    print(f'  - {meet[0]} ({meet[1]}) - {meet[2]}')

print('\n' + '=' * 80)
print('\nComparing:')
print('=' * 80)
db_meet_names = {meet[0].lower().strip() for meet in db_meets}
excel_meet_names_lower = {name.lower().strip() for name in all_meet_names}

missing_from_db = excel_meet_names_lower - db_meet_names
if missing_from_db:
    print(f'\nMeets in Excel file but NOT in database ({len(missing_from_db)}):')
    for name in sorted(missing_from_db):
        print(f'  - {name}')

conn.close()
