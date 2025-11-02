#!/usr/bin/env python3
import pandas as pd

# Read the source workbook and check the sheet names
wb_path = '../Malaysia Times Database/Malaysia On Track Times Spreadsheet Workbook (1).xlsx'
xl_file = pd.ExcelFile(wb_path)
print('Available sheets:')
for sheet in xl_file.sheet_names:
    print(f'- {sheet}')

# Read the specific sheet
print('\n=== AGE POINTS APPLIED TO SEA AGEAY SHEET ===')
df = pd.read_excel(wb_path, sheet_name='Age Points Applied to SEA AgeAY', header=None)
print(f'Sheet shape: {df.shape}')
print('First 5 rows:')
for i in range(min(5, len(df))):
    print(f'Row {i}: {df.iloc[i].tolist()[:10]}')
