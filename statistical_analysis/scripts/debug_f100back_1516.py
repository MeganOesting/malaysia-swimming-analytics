#!/usr/bin/env python3
"""
Debug script for F 100 Back 15->16 missing delta
Investigates why there are 0 matched athletes
"""
import os
import pandas as pd
from pathlib import Path

# File paths
script_dir = Path(__file__).parent
if 'statistical_analysis' in str(script_dir):
    period_data_base = script_dir.parent / "data" / "Period Data"
else:
    period_data_base = Path("Period Data")

file_15 = period_data_base / "9.1.21-8.31.22" / "F 100 Back 9.1.21-8.31.22" / "F 100 Back 15 9.1.21-8.31.22.txt"
file_16 = period_data_base / "9.1.22-8.31.23" / "F 100 Back 9.1.22-8.31.23" / "F 100 Back 16 9.1.22-8.31.23.txt"

print("=" * 60)
print("Debugging F 100 Back 15->16 Delta Analysis")
print("=" * 60)
print()

# Check if files exist
print(f"File 15 exists: {file_15.exists()}")
print(f"File 16 exists: {file_16.exists()}")
print(f"File 15 path: {file_15}")
print(f"File 16 path: {file_16}")
print()

if not file_15.exists() or not file_16.exists():
    print("❌ Files not found!")
    exit(1)

# Load files
print("Loading files...")
try:
    df_15 = pd.read_csv(
        file_15,
        sep='\t',
        encoding='utf-8',
        errors='ignore',
        dtype={'Name': str}
    )
    df_16 = pd.read_csv(
        file_16,
        sep='\t',
        encoding='utf-8',
        errors='ignore',
        dtype={'Name': str}
    )
    print(f"✅ Loaded age 15: {len(df_15)} rows")
    print(f"✅ Loaded age 16: {len(df_16)} rows")
except Exception as e:
    print(f"❌ Error loading files: {e}")
    exit(1)

print()

# Check columns
print("Columns in age 15 file:")
print(df_15.columns.tolist())
print()
print("Columns in age 16 file:")
print(df_16.columns.tolist())
print()

# Check for Name column
if 'Name' not in df_15.columns:
    print("⚠️  'Name' column not found in age 15 file. Available columns:")
    print(df_15.columns.tolist())
    print("\nFirst few rows:")
    print(df_15.head())
    
if 'Name' not in df_16.columns:
    print("⚠️  'Name' column not found in age 16 file. Available columns:")
    print(df_16.columns.tolist())
    print("\nFirst few rows:")
    print(df_16.head())

# Get names
df_15['name_lower'] = df_15['Name'].astype(str).str.lower().str.strip()
df_16['name_lower'] = df_16['Name'].astype(str).str.lower().str.strip()

print(f"\nUnique names in age 15: {df_15['name_lower'].nunique()}")
print(f"Unique names in age 16: {df_16['name_lower'].nunique()}")

# Find common names
common_names = set(df_15['name_lower']) & set(df_16['name_lower'])
print(f"\nCommon names found: {len(common_names)}")

if len(common_names) == 0:
    print("\n❌ NO COMMON NAMES FOUND!")
    print("\nInvestigating name differences...")
    
    # Show sample names from each
    print("\nSample names from age 15 (first 10):")
    for name in df_15['name_lower'].head(10):
        print(f"  '{name}'")
    
    print("\nSample names from age 16 (first 10):")
    for name in df_16['name_lower'].head(10):
        print(f"  '{name}'")
    
    # Check for similar names (fuzzy matching)
    print("\nChecking for similar names...")
    from difflib import get_close_matches
    
    sample_15 = df_15['name_lower'].head(20).tolist()
    sample_16 = df_16['name_lower'].head(20).tolist()
    
    print("\nPossible matches (similar names):")
    matches_found = 0
    for name_15 in sample_15:
        matches = get_close_matches(name_15, sample_16, n=1, cutoff=0.8)
        if matches:
            print(f"  '{name_15}' might match '{matches[0]}'")
            matches_found += 1
    
    if matches_found == 0:
        print("  No similar names found (cutoff: 0.8)")
    
    # Check data ranges
    print("\nData summary:")
    print(f"Age 15 file shape: {df_15.shape}")
    print(f"Age 16 file shape: {df_16.shape}")
    
else:
    print("\n✅ Common names found!")
    print(f"\nSample common names (first 10):")
    for name in list(common_names)[:10]:
        print(f"  '{name}'")
    
    # Show matched athletes
    print(f"\nMatched athletes (first 10):")
    for name in list(common_names)[:10]:
        row_15 = df_15[df_15['name_lower'] == name].iloc[0]
        row_16 = df_16[df_16['name_lower'] == name].iloc[0]
        time_15 = row_15.get('Time', 'N/A')
        time_16 = row_16.get('Time', 'N/A')
        print(f"  {name}: {time_15} -> {time_16}")

print()
print("=" * 60)
print("Debug complete")
print("=" * 60)
