import pandas as pd
from pathlib import Path

# Check SUKMA file structure
sukma_file = Path("data/meets/SUKMA_2024_Men.xls")

print("=== SUKMA 2024 Men Excel File Analysis ===")
print()

try:
    # Get all sheet names
    excel_file = pd.ExcelFile(sukma_file)
    sheet_names = excel_file.sheet_names
    print(f"Sheet names in {sukma_file.name}:")
    for i, sheet in enumerate(sheet_names):
        print(f"  {i+1}. {sheet}")
    print()
    
    # Check each sheet
    for sheet_name in sheet_names:
        print(f"=== Sheet: {sheet_name} ===")
        df = pd.read_excel(sukma_file, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head(3))
        print()
        
except Exception as e:
    print(f"Error reading {sukma_file}: {e}")

# Also check the Women's file
sukma_women_file = Path("data/meets/SUKMA_2024_Women.xls")
print("=== SUKMA 2024 Women Excel File Analysis ===")
print()

try:
    excel_file = pd.ExcelFile(sukma_women_file)
    sheet_names = excel_file.sheet_names
    print(f"Sheet names in {sukma_women_file.name}:")
    for i, sheet in enumerate(sheet_names):
        print(f"  {i+1}. {sheet}")
    print()
    
    # Check first sheet
    if sheet_names:
        sheet_name = sheet_names[0]
        print(f"=== Sheet: {sheet_name} ===")
        df = pd.read_excel(sukma_women_file, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head(3))
        print()
        
except Exception as e:
    print(f"Error reading {sukma_women_file}: {e}")



