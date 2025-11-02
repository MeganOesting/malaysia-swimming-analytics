#!/usr/bin/env python3
"""
Check the actual column headers in row 2
"""

import pandas as pd
from pathlib import Path

# Check SUKMA file headers
file_path = Path("data/meets/SUKMA_2024_Men.xls")
sheet_name = "50m Fr"

print(f"Examining headers in: {file_path}")
print(f"Sheet: {sheet_name}")
print("=" * 50)

try:
    # Read with header=None to see raw structure
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='xlrd')
    print(f"Shape: {df.shape}")
    
    # Show row 1 (meet info)
    print("\nRow 1 (Meet info):")
    print(df.iloc[0].tolist())
    
    # Show row 2 (headers)
    print("\nRow 2 (Headers):")
    headers = df.iloc[1].tolist()
    for i, header in enumerate(headers):
        print(f"Column {i}: {header}")
    
    # Show first few data rows
    print("\nFirst 3 data rows (starting from row 3):")
    for i in range(2, min(5, len(df))):
        print(f"Row {i}: {df.iloc[i].tolist()}")
    
except Exception as e:
    print(f"Error: {e}")



