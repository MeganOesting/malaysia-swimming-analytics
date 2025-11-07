"""Check what dates are actually in the Excel files"""
import pandas as pd
from pathlib import Path

# Check MIAG file
print("=== MIAG 2025 Men ===")
miag_file = Path('data/meets/MIAG_2025_Men.xls')
df = pd.read_excel(miag_file, sheet_name='50m Fr', engine='xlrd')

print(f"Shape: {df.shape}")
print(f"\nFirst 5 rows, column 13 (MEETDATE):")
for i in range(min(5, len(df))):
    val = df.iloc[i, 13] if df.shape[1] > 13 else None
    print(f"  Row {i}: {repr(val)}")

print(f"\nRow 2 (header row, index 1):")
print(f"  Column 13: {repr(df.iloc[1, 13] if df.shape[1] > 13 else None)}")
print(f"  Column 13 type: {type(df.iloc[1, 13] if df.shape[1] > 13 else None)}")

# Check actual data rows
print(f"\nData rows (starting at row 3, index 2), column 13:")
for i in range(2, min(7, len(df))):
    val = df.iloc[i, 13] if df.shape[1] > 13 else None
    print(f"  Row {i}: {repr(val)} ({type(val).__name__})")

print("\n=== Malaysia Open 2025 Men ===")
mo_file = Path('data/meets/MO_2025_Men.xls')
df2 = pd.read_excel(mo_file, sheet_name='50m Fr', engine='xlrd')

print(f"Shape: {df2.shape}")
print(f"\nData rows, column 13 (MEETDATE):")
for i in range(2, min(7, len(df2))):
    val = df2.iloc[i, 13] if df2.shape[1] > 13 else None
    print(f"  Row {i}: {repr(val)} ({type(val).__name__})")














