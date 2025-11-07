#!/usr/bin/env python3
"""
Fix swapped data in F 100 Back files for period 9.1.21-8.31.22
The age 15 file has age 18 data, and age 18 file has age 15 data.
This script swaps them back.
"""
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent
period_data_base = script_dir.parent / "data" / "Period Data"

# File paths
period_dir = period_data_base / "9.1.21-8.31.22" / "F 100 Back 9.1.21-8.31.22"
file_15 = period_dir / "F 100 Back 15 9.1.21-8.31.22.txt"
file_18 = period_dir / "F 100 Back 18 9.1.21-8.31.22.txt"

print("=" * 60)
print("Fixing Swapped F 100 Back Data")
print("=" * 60)
print()

# Verify the swap issue
print("Verifying the problem...")
df_15_file = pd.read_csv(file_15, sep='\t', encoding='utf-8', dtype={'Name': str})
df_18_file = pd.read_csv(file_18, sep='\t', encoding='utf-8', dtype={'Name': str})

ages_in_15_file = df_15_file['Age'].unique()
ages_in_18_file = df_18_file['Age'].unique()

print(f"Ages in 'F 100 Back 15' file: {ages_in_15_file}")
print(f"Ages in 'F 100 Back 18' file: {ages_in_18_file}")
print()

if 15 in ages_in_15_file or 18 not in ages_in_15_file:
    print("⚠️  Warning: Age 15 file doesn't contain age 18 data as expected")
    print("   The problem might be different than expected")
    response = input("Continue with swap anyway? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        exit(0)

# Create backup
backup_dir = period_dir / "backup"
backup_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_15 = backup_dir / f"F 100 Back 15 9.1.21-8.31.22_backup_{timestamp}.txt"
backup_18 = backup_dir / f"F 100 Back 18 9.1.21-8.31.22_backup_{timestamp}.txt"

print(f"Creating backups...")
shutil.copy2(file_15, backup_15)
shutil.copy2(file_18, backup_18)
print(f"  ✅ Backed up to: {backup_15.name}")
print(f"  ✅ Backed up to: {backup_18.name}")
print()

# Swap the files
print("Swapping file contents...")
temp_file = period_dir / "F 100 Back TEMP 9.1.21-8.31.22.txt"

# Move 15 file to temp
shutil.move(str(file_15), str(temp_file))
# Move 18 file to 15 file location
shutil.move(str(file_18), str(file_15))
# Move temp (old 15) to 18 file location
shutil.move(str(temp_file), str(file_18))

print(f"  ✅ Swapped file contents")
print()

# Verify the fix
print("Verifying the fix...")
df_15_new = pd.read_csv(file_15, sep='\t', encoding='utf-8', dtype={'Name': str})
df_18_new = pd.read_csv(file_18, sep='\t', encoding='utf-8', dtype={'Name': str})

ages_in_15_new = df_15_new['Age'].unique()
ages_in_18_new = df_18_new['Age'].unique()

print(f"Ages in 'F 100 Back 15' file (after swap): {ages_in_15_new}")
print(f"Ages in 'F 100 Back 18' file (after swap): {ages_in_18_new}")
print()

# Verify counts
count_15_in_15_file = len(df_15_new[df_15_new['Age'] == 15])
count_18_in_18_file = len(df_18_new[df_18_new['Age'] == 18])

print(f"Age 15 swimmers in 'F 100 Back 15' file: {count_15_in_15_file}")
print(f"Age 18 swimmers in 'F 100 Back 18' file: {count_18_in_18_file}")
print()

if 15 in ages_in_15_new and count_15_in_15_file > 0:
    print("✅ SUCCESS! Age 15 file now contains age 15 data")
else:
    print("❌ ERROR: Age 15 file still doesn't have correct data")

if 18 in ages_in_18_new and count_18_in_18_file > 0:
    print("✅ SUCCESS! Age 18 file now contains age 18 data")
else:
    print("❌ ERROR: Age 18 file still doesn't have correct data")

print()
print("=" * 60)
print("Fix complete!")
print("=" * 60)
print()
print("Next steps:")
print("1. Re-run delta analysis: python scripts\\run_mot_delta_analysis.py")
print("2. Check that F 100 Back 15->16 delta is now calculated")

