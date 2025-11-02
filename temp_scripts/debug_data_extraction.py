#!/usr/bin/env python3
"""
Debug script to examine data extraction
"""

import pandas as pd
from pathlib import Path

# Check SUKMA file structure
file_path = Path("data/meets/SUKMA_2024_Men.xls")
sheet_name = "50m Fr"

print(f"Examining: {file_path}")
print(f"Sheet: {sheet_name}")
print("=" * 50)

try:
    # Read with header=None to see raw structure
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine='xlrd')
    print(f"Shape: {df.shape}")
    
    # Skip header rows (row 1: meet info, row 2: headers, row 3+: data)
    df_data = df.iloc[2:].copy() if len(df) > 2 else df
    print(f"Data section shape: {df_data.shape}")
    
    if len(df_data) > 0:
        # Check the first few rows of data
        print("\nFirst 5 rows of data:")
        print(df_data.head())
        
        # Check gender column (index 1)
        print(f"\nGender column (index 1) unique values:")
        print(df_data.iloc[:, 1].unique())
        
        # Check distance column (index 2)
        print(f"\nDistance column (index 2) unique values:")
        print(df_data.iloc[:, 2].unique())
        
        # Check stroke column (index 3)
        print(f"\nStroke column (index 3) unique values:")
        print(df_data.iloc[:, 3].unique())
        
        # Check name column (index 4)
        print(f"\nName column (index 4) first 5 values:")
        print(df_data.iloc[:5, 4].tolist())
        
        # Test the filtering logic
        gender_col = df_data.iloc[:, 1].astype(str).str.strip().str.upper()
        distance_col = pd.to_numeric(df_data.iloc[:, 2], errors='coerce')
        stroke_col = df_data.iloc[:, 3].astype(str).str.strip().str.upper()
        name_col = df_data.iloc[:, 4].astype(str).str.strip()
        
        print(f"\nFiltering test:")
        print(f"Gender 'M' matches: {(gender_col == 'M').sum()}")
        print(f"Gender 'F' matches: {(gender_col == 'F').sum()}")
        print(f"Non-empty names: {(name_col != '').sum()}")
        print(f"Valid distances: {distance_col.isin([50, 100, 200, 400, 800, 1500]).sum()}")
        
        # Combined mask
        mask = (
            (gender_col == 'M') &
            (name_col != "") &
            (distance_col.isin([50, 100, 200, 400, 800, 1500]))
        )
        print(f"Combined mask matches: {mask.sum()}")
        
        if mask.sum() > 0:
            print(f"\nFirst matching row:")
            matching_row = df_data[mask].iloc[0]
            print(f"Gender: {matching_row.iloc[1]}")
            print(f"Distance: {matching_row.iloc[2]}")
            print(f"Stroke: {matching_row.iloc[3]}")
            print(f"Name: {matching_row.iloc[4]}")
            print(f"Time: {matching_row.iloc[8]}")
            print(f"AQUA: {matching_row.iloc[10]}")
            print(f"Place: {matching_row.iloc[12]}")
    
except Exception as e:
    print(f"Error: {e}")



