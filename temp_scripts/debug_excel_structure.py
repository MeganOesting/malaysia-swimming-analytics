#!/usr/bin/env python3
"""
Debug script to examine Excel file structure
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
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 10 rows:")
    print(df.head(10))
    
    print("\nColumn B (index 1) - Gender:")
    print(df.iloc[:10, 1])
    
    print("\nColumn C (index 2) - Distance:")
    print(df.iloc[:10, 2])
    
    print("\nColumn D (index 3) - Stroke:")
    print(df.iloc[:10, 3])
    
    print("\nColumn E (index 4) - Name:")
    print(df.iloc[:10, 4])
    
    print("\nColumn I (index 8) - Time:")
    print(df.iloc[:10, 8])
    
    print("\nColumn K (index 10) - AQUA:")
    print(df.iloc[:10, 10])
    
    print("\nColumn M (index 12) - Place:")
    print(df.iloc[:10, 12])
    
    print("\nColumn Q (index 16) - Team:")
    print(df.iloc[:10, 16])
    
except Exception as e:
    print(f"Error: {e}")



