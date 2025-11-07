#!/usr/bin/env python3
"""
Investigate F 100 Back data files to find where age 15 data actually is
"""
import pandas as pd
from pathlib import Path

script_dir = Path(__file__).parent
period_data_base = script_dir.parent / "data" / "Period Data"

# Check all files in period 9.1.21-8.31.22 for F 100 Back
period1_dir = period_data_base / "9.1.21-8.31.22" / "F 100 Back 9.1.21-8.31.22"
print("=" * 60)
print("Investigating F 100 Back files in period 9.1.21-8.31.22")
print("=" * 60)
print()

for file_path in period1_dir.glob("*.txt"):
    print(f"\nFile: {file_path.name}")
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8', errors='ignore')
        if 'Age' in df.columns:
            ages = df['Age'].unique()
            age_counts = df['Age'].value_counts()
            print(f"  Ages found: {sorted(ages)}")
            print(f"  Counts:")
            for age, count in age_counts.items():
                print(f"    Age {age}: {count} swimmers")
            
            # Check if age 15 is in this file
            if 15 in ages:
                print(f"  ✅ AGE 15 FOUND IN THIS FILE!")
                print(f"  Sample age 15 names:")
                age_15_names = df[df['Age'] == 15]['Name'].head(10).tolist()
                for name in age_15_names:
                    print(f"    - {name}")
        else:
            print(f"  ⚠️  No 'Age' column found")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")

print("\n" + "=" * 60)
print("Checking period 9.1.22-8.31.23 (where age 16 should be)")
print("=" * 60)
print()

period2_dir = period_data_base / "9.1.22-8.31.23" / "F 100 Back 9.1.22-8.31.23"
for file_path in period2_dir.glob("*.txt"):
    print(f"\nFile: {file_path.name}")
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8', errors='ignore')
        if 'Age' in df.columns:
            ages = df['Age'].unique()
            age_counts = df['Age'].value_counts()
            print(f"  Ages found: {sorted(ages)}")
            print(f"  Counts:")
            for age, count in age_counts.items():
                print(f"    Age {age}: {count} swimmers")
        else:
            print(f"  ⚠️  No 'Age' column found")
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")

print("\n" + "=" * 60)
print("Conclusion:")
print("=" * 60)
print("If age 15 data exists, we need to find which file it's in")
print("If age 15 data doesn't exist, the file needs to be collected")




