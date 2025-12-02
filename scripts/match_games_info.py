"""
Match Additional Games Info Excel to Supabase athletes
Find unmatched names and DOB discrepancies
"""
import pandas as pd
import requests
import re

SUPABASE_URL = 'https://bvmqstoeahseklvmvdlx.supabase.co'
SUPABASE_KEY = 'sb_publishable_-0n963Zy08gBMJPMse2V8A_xAyHgKZM'

headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

# Load Excel
file_path = r'C:\Users\megan\Downloads\Additional Games Info (Passport,School, Sizes) (2).xlsx'
df = pd.read_excel(file_path)

# Get all athletes from Supabase (paginated)
print('Fetching athletes from Supabase...')
all_athletes = []
offset = 0
while True:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/athletes?select=id,fullname,birthdate,gender&limit=1000&offset={offset}',
        headers=headers
    )
    batch = response.json()
    if not batch:
        break
    all_athletes.extend(batch)
    offset += 1000
print(f'Loaded {len(all_athletes)} athletes from database')

# Normalize name for matching
def normalize_name(name):
    if pd.isna(name):
        return ''
    name = str(name).upper().strip()
    # Remove punctuation and extra spaces
    name = re.sub(r'[,.\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name

# Normalize DOB to YYYY-MM-DD for comparison
def normalize_dob(dob):
    if pd.isna(dob):
        return None
    dob = str(dob).strip()

    # Handle ISO format: 2006-05-05T00:00:00Z
    if 'T' in dob:
        return dob.split('T')[0]

    # Handle various formats
    dob = dob.replace('.', '/').replace(' ', '/')

    # Try ddmmyyyy (no separators)
    if len(dob) == 8 and dob.isdigit():
        return f'{dob[4:8]}-{dob[2:4]}-{dob[0:2]}'

    # Try dd/mm/yyyy or similar
    parts = re.split(r'[/\-]', dob)
    if len(parts) == 3:
        d, m, y = parts
        if len(y) == 4:
            return f'{y}-{m.zfill(2)}-{d.zfill(2)}'
        elif len(d) == 4:
            return f'{d}-{m.zfill(2)}-{y.zfill(2)}'

    return dob  # Return as-is if can't parse

# Build lookup dict from database
db_lookup = {}
for a in all_athletes:
    norm_name = normalize_name(a['fullname'])
    # Get name words for matching
    words = set(norm_name.split())
    db_lookup[norm_name] = {
        'id': a['id'],
        'fullname': a['fullname'],
        'birthdate': normalize_dob(a['birthdate']),
        'gender': a['gender'],
        'words': words
    }

# Get unique Excel entries (dedup by name)
excel_unique = df.drop_duplicates(subset=['Name'], keep='first')
print(f'Unique names in Excel: {len(excel_unique)}')

# Match each Excel name
unmatched = []
dob_discrepancies = []
matched = []

for _, row in excel_unique.iterrows():
    excel_name = row['Name']
    excel_norm = normalize_name(excel_name)
    excel_words = set(excel_norm.split())
    excel_dob = normalize_dob(row['DOB (ddmmYYYY)'])
    excel_gender = row['Gender']

    # Try exact match first
    if excel_norm in db_lookup:
        db_entry = db_lookup[excel_norm]
        matched.append((excel_name, db_entry['fullname'], db_entry['id']))

        # Check DOB
        if db_entry['birthdate'] and excel_dob:
            if db_entry['birthdate'] != excel_dob:
                dob_discrepancies.append({
                    'name': excel_name,
                    'db_name': db_entry['fullname'],
                    'excel_dob': excel_dob,
                    'db_dob': db_entry['birthdate'],
                    'db_id': db_entry['id']
                })
        continue

    # Try word-based match (at least 2 words in common)
    best_match = None
    best_score = 0
    for norm_name, db_entry in db_lookup.items():
        common = excel_words & db_entry['words']
        if len(common) >= 2:
            score = len(common)
            if score > best_score:
                best_score = score
                best_match = db_entry

    if best_match and best_score >= 2:
        matched.append((excel_name, best_match['fullname'], best_match['id']))

        # Check DOB
        if best_match['birthdate'] and excel_dob:
            if best_match['birthdate'] != excel_dob:
                dob_discrepancies.append({
                    'name': excel_name,
                    'db_name': best_match['fullname'],
                    'excel_dob': excel_dob,
                    'db_dob': best_match['birthdate'],
                    'db_id': best_match['id']
                })
    else:
        unmatched.append({
            'name': excel_name,
            'dob': excel_dob,
            'gender': excel_gender,
            'role': row['Role'],
            'sport': row['Sport'] if pd.notna(row['Sport']) else 'Unknown'
        })

print()
print('='*60)
print(f'MATCHED: {len(matched)} of {len(excel_unique)}')
print(f'UNMATCHED: {len(unmatched)}')
print(f'DOB DISCREPANCIES: {len(dob_discrepancies)}')
print('='*60)
print()

if unmatched:
    print('=== UNMATCHED NAMES (not in database) ===')
    for u in unmatched:
        print(f"  {u['name']} | DOB: {u['dob']} | {u['gender']} | {u['role']} | {u['sport']}")
    print()

if dob_discrepancies:
    print('=== DOB DISCREPANCIES ===')
    for d in dob_discrepancies:
        print(f"  {d['name']}")
        print(f"    Excel DOB: {d['excel_dob']}")
        print(f"    DB DOB:    {d['db_dob']} (ID: {d['db_id']}, DB name: {d['db_name']})")
        print()
