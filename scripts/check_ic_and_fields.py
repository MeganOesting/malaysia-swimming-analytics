"""Check IC formats and registration fields"""
import sqlite3
import pandas as pd

# Check IC lengths in database
conn = sqlite3.connect(r'C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\malaysia_swimming.db')
cursor = conn.cursor()

print("=== IC DIGIT LENGTHS IN DATABASE ===")
cursor.execute("SELECT IC FROM athletes WHERE IC IS NOT NULL AND IC != '' AND LENGTH(IC) > 0")
ics = [row[0] for row in cursor.fetchall() if row[0]]
print(f"Total athletes with IC: {len(ics)}")

# Count by length
length_counts = {}
for ic in ics:
    ic_str = str(ic).strip()
    length = len(ic_str)
    length_counts[length] = length_counts.get(length, 0) + 1

print("\nIC lengths distribution:")
for length, count in sorted(length_counts.items()):
    print(f"  {length} digits: {count} athletes")

# Show samples
print("\nSample ICs:")
for ic in ics[:10]:
    print(f"  '{ic}' -> {len(str(ic))} chars")

conn.close()

# Check registration columns
print("\n\n=== REGISTRATION FILE COLUMNS ===")
df = pd.read_excel(r'C:\Users\megan\Downloads\REMAINING_UNMATCHED_RECORDS964_3815.xlsx')
regs = df[df['_match_category'] == 'leftover_registration']

print("Columns starting with 'reg_':")
reg_cols = [c for c in df.columns if c.startswith('reg_')]
for col in reg_cols:
    # Count non-null values
    non_null = regs[col].notna().sum()
    print(f"  {col}: {non_null} non-null values")

# Show sample registration record
print("\n\nSample registration record (first non-null values):")
sample = regs.iloc[0]
for col in reg_cols:
    val = sample.get(col)
    if pd.notna(val) and str(val).strip():
        print(f"  {col}: {val}")
