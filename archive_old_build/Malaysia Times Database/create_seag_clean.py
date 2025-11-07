#!/usr/bin/env python3
import pandas as pd

# Read the source sheet
wb_path = 'Malaysia On Track Times Spreadsheet Workbook (1).xlsx'
df = pd.read_excel(wb_path, sheet_name='Age Points Applied to SEA AgeAY', header=None)

print(f'Source sheet shape: {df.shape}')
print('First 3 rows of source:')
for i in range(min(3, len(df))):
    print(f'Row {i}: {df.iloc[i].tolist()[:10]}')

# Create new DataFrame with correct column structure matching other meet files
new_rows = []

# Add header row to match standard format
header_row = ['', 'Gender', 'Distance', 'Stroke', 'Name', 'Birthdate', 'Age', 'H', 'Time', 'J', 'AQUA', 'L', 'Place', 'Meet Date', 'O', 'P', 'Team']
new_rows.append(header_row)

# Process data rows
for idx, row in df.iterrows():
    if idx == 0:  # Skip header row
        continue
    
    # Extract data according to your mapping
    gender = row.iloc[1] if len(row) > 1 else ''  # Column B
    event = row.iloc[2] if len(row) > 2 else ''  # Column C (event)
    name = row.iloc[4] if len(row) > 4 else ''   # Column E
    birthdate = row.iloc[5] if len(row) > 5 else ''  # Column F
    age = row.iloc[3] if len(row) > 3 else ''   # Column D (age)
    time = row.iloc[8] if len(row) > 8 else ''   # Column I
    place = row.iloc[12] if len(row) > 12 else ''  # Column M
    
    # Split event into distance and stroke
    # You'll need to tell me the format of the event column
    distance = ''
    stroke = ''
    
    # Create new row with correct structure
    new_row = ['', gender, distance, stroke, name, birthdate, age, '', time, '', '', '', place, '', '', '']
    new_rows.append(new_row)

# Create new DataFrame
new_df = pd.DataFrame(new_rows)

# Save to meets folder
new_df.to_excel('Meets/SEAG_2025_ALL.xlsx', index=False, header=False)
print(f'New SEAG file created with {len(new_df)} rows')
print('First few rows:')
for i in range(min(3, len(new_df))):
    print(f'Row {i}: {new_df.iloc[i].tolist()[:10]}')



