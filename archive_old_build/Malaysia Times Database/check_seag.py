#!/usr/bin/env python3
"""
Check SEAG_2025_ALL.xlsx file quality
"""

import pandas as pd

def check_seag_file():
    """Check the SEAG file for data quality"""
    df = pd.read_excel('Meets/SEAG_2025_ALL.xlsx')
    
    print("=== SEAG_2025_ALL.xlsx VERIFICATION ===")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    print("\n=== KEY COLUMNS CHECK ===")
    print(f"Gender (B): {df['B'].value_counts().to_dict()}")
    print(f"Distance (C): {df['C'].value_counts().to_dict()}")
    print(f"Stroke (D): {df['D'].value_counts().to_dict()}")
    
    print("\n=== SAMPLE ROWS ===")
    for i in range(3):
        name = str(df['E'].iloc[i])[:20] + "..." if len(str(df['E'].iloc[i])) > 20 else str(df['E'].iloc[i])
        print(f"Row {i}: {df['B'].iloc[i]} | {df['C'].iloc[i]} | {df['D'].iloc[i]} | {name} | Age:{df['G'].iloc[i]} | Time:{df['I'].iloc[i]} | AQUA:{df['K'].iloc[i]}")
    
    print("\n=== MEET INFO ===")
    print(f"Meet Date (N): {df['N'].iloc[0]}")
    print(f"Team/State (Q) - blank rows: {df['Q'].isna().sum()} out of {len(df)}")
    print(f"AQUA Points (K) - calculated: {df['K'].notna().sum()} out of {len(df)}")
    
    print("\n=== DATA QUALITY ===")
    print(f"Missing names: {df['E'].isna().sum()}")
    print(f"Missing ages: {df['G'].isna().sum()}")
    print(f"Missing times: {df['I'].isna().sum()}")
    print(f"Missing places: {df['M'].isna().sum()}")
    
    print("\n✅ SEAG file verification complete!")

if __name__ == "__main__":
    check_seag_file()


