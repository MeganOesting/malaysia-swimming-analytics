"""Analyze one meet workbook to understand structure and count swimmers"""
import pandas as pd
from pathlib import Path

# Let's analyze SUKMA Men's file
workbook_path = Path('data/meets/SUKMA_2024_Men.xls')

print(f"Analyzing: {workbook_path.name}\n")
print("="*60)

# Read all sheets
xl = pd.ExcelFile(workbook_path, engine='xlrd')
print(f"Total sheets: {len(xl.sheet_names)}")
print(f"Sheets: {xl.sheet_names}\n")

# Filter to event sheets only (skip Lap, relay, Top Results)
event_sheets = []
for sheet_name in xl.sheet_names:
    sheet_lower = sheet_name.lower().strip()
    if (' lap' in sheet_lower or sheet_lower.endswith(' lap') or
        sheet_lower.startswith('4 x') or ' 4 x ' in sheet_lower or '4x' in sheet_lower or
        'top result' in sheet_lower or sheet_lower == 'summary'):
        continue
    event_sheets.append(sheet_name)

print(f"Event sheets (after filtering): {len(event_sheets)}")
print(f"Event sheet names: {event_sheets}\n")
print("="*60)

# Analyze each event sheet
total_swimmers = 0
total_results = 0

for sheet_name in event_sheets:
    print(f"\nSheet: {sheet_name}")
    df = pd.read_excel(workbook_path, sheet_name=sheet_name, engine='xlrd')
    
    print(f"  Shape: {df.shape} (rows, columns)")
    
    # Find header row (look for 'NAME' or 'GENDER' or 'STROKE')
    header_row = 0
    for i in range(min(5, len(df))):
        row_values = [str(cell).strip().upper() if pd.notna(cell) else '' for cell in df.iloc[i]]
        if any(keyword in ' '.join(row_values) for keyword in ['NAME', 'GENDER', 'STROKE', 'DISTANCE']):
            header_row = i
            break
    
    print(f"  Header row: {header_row}")
    
    # Count data rows (starting after header)
    data_start = header_row + 1
    data_rows = len(df) - data_start
    
    # Count non-empty name rows
    name_column = None
    for col_idx in range(min(10, df.shape[1])):
        col_values = [str(df.iloc[i, col_idx]).strip().upper() if pd.notna(df.iloc[i, col_idx]) else '' 
                      for i in range(min(header_row + 3, len(df)))]
        if 'NAME' in ' '.join(col_values[:3]):
            name_column = col_idx
            break
    
    if name_column is not None:
        swimmers_in_event = 0
        for i in range(data_start, len(df)):
            name_val = df.iloc[i, name_column]
            if pd.notna(name_val) and str(name_val).strip() != '':
                swimmers_in_event += 1
        print(f"  Swimmers in this event: {swimmers_in_event}")
        total_swimmers += swimmers_in_event
        total_results += swimmers_in_event
    else:
        print(f"  Could not find name column, data rows: {data_rows}")
    
    # Show first few rows for debugging
    if sheet_name == event_sheets[0]:  # Only show for first sheet
        print(f"\n  First 3 data rows (columns 0-9):")
        for i in range(data_start, min(data_start + 3, len(df))):
            print(f"    Row {i}: {[str(df.iloc[i, j])[:20] if pd.notna(df.iloc[i, j]) else '' for j in range(min(10, df.shape[1]))]}")

print("\n" + "="*60)
print(f"\nSUMMARY for {workbook_path.name}:")
print(f"  Total event sheets: {len(event_sheets)}")
print(f"  Total swimmers (across all events): {total_swimmers}")
print(f"  Total results: {total_results}")
print(f"\nNote: These counts may include duplicates if same swimmer did multiple events.")




