"""
Load Additional Games Info Excel to Supabase
Updates athletes with passport, school, medical info, etc.
"""
import pandas as pd
import requests
import re

SUPABASE_URL = 'https://bvmqstoeahseklvmvdlx.supabase.co'
SUPABASE_KEY = 'sb_publishable_-0n963Zy08gBMJPMse2V8A_xAyHgKZM'
headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

# Load Excel
file_path = r'C:\Users\megan\Downloads\Additional Games Info (Passport,School, Sizes) (2).xlsx'
df = pd.read_excel(file_path)
print(f'Loaded {len(df)} rows from Excel')

# Get all athletes from Supabase
print('Fetching athletes from Supabase...')
all_athletes = []
offset = 0
while True:
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/athletes?select=id,fullname,birthdate,gender&limit=1000&offset={offset}',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    )
    batch = response.json()
    if not batch:
        break
    all_athletes.extend(batch)
    offset += 1000
print(f'Loaded {len(all_athletes)} athletes from database')

# WRONG MATCHES to skip (identified earlier)
WRONG_MATCHES = {
    'Elson Lee Chun Hong',
    'Ho Wei Yan (Megan)',
    'HO WEI YAN',
    'Bryan Leong Xin Ren',
    'Isabelle Kam Zi Zhen',
    'Andrew Goh Zheng Yen',
    'Sophocles Ng Xin Xian',
    'Mark Chua Yu Foong',
    'Albert Yeap Jin Teik',
}

# Normalize name for matching
def normalize_name(name):
    if pd.isna(name):
        return ''
    name = str(name).upper().strip()
    name = re.sub(r'[,.\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name

# Build lookup dict
db_lookup = {}
for a in all_athletes:
    norm_name = normalize_name(a['fullname'])
    words = set(norm_name.split())
    db_lookup[norm_name] = {
        'id': a['id'],
        'fullname': a['fullname'],
        'words': words
    }

# Track stats
updated = 0
skipped_coaches = 0
skipped_wrong_match = 0
skipped_not_found = 0
errors = 0

# Process each row
for idx, row in df.iterrows():
    excel_name = str(row['Name']).strip()
    role = str(row['Role']).strip() if pd.notna(row['Role']) else 'Athlete'

    # Skip coaches (already in coaches table)
    if role == 'Coach':
        skipped_coaches += 1
        continue

    # Skip known wrong matches
    if excel_name in WRONG_MATCHES or excel_name.strip() in WRONG_MATCHES:
        print(f'  Skipping wrong match: {excel_name}')
        skipped_wrong_match += 1
        continue

    # Find matching athlete
    excel_norm = normalize_name(excel_name)
    excel_words = set(excel_norm.split())

    matched_id = None

    # Exact match first
    if excel_norm in db_lookup:
        matched_id = db_lookup[excel_norm]['id']
    else:
        # Word-based match
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
            matched_id = best_match['id']

    if not matched_id:
        skipped_not_found += 1
        continue

    # Build update payload
    update_data = {}

    # Role and Sport
    update_data['role'] = 'Athlete'
    if pd.notna(row['Sport']):
        update_data['sport'] = str(row['Sport'])
    else:
        update_data['sport'] = 'Swimming'  # Default for SEA Age

    # Passport
    if pd.notna(row['MAS Passport No']):
        update_data['passport_number'] = str(row['MAS Passport No'])

    # Passport expiry
    if pd.notna(row['Passport Expiry Date (ddmmYYYY)']):
        exp = str(row['Passport Expiry Date (ddmmYYYY)'])
        # Try to normalize date format
        exp = exp.replace('.', '/').replace(' ', '/')
        if len(exp) == 8 and exp.replace('/', '').isdigit():
            # ddmmyyyy
            update_data['passport_expiry_date'] = f'{exp[4:8]}-{exp[2:4]}-{exp[0:2]}T00:00:00Z'
        elif '/' in exp:
            parts = exp.split('/')
            if len(parts) == 3:
                d, m, y = parts[0], parts[1], parts[2]
                if len(y) == 4:
                    update_data['passport_expiry_date'] = f'{y}-{m.zfill(2)}-{d.zfill(2)}T00:00:00Z'

    # Shirt/Shoe sizes
    if pd.notna(row['ShirtSize']):
        size = str(row['ShirtSize'])
        # Clean up phone numbers that got into size field
        if not any(c.isdigit() for c in size) or size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
            update_data['tshirt_size'] = size

    if pd.notna(row['ShoeSize']):
        size = str(row['ShoeSize'])
        if not size.startswith('+') and not size.startswith('6'):  # Skip phone numbers
            update_data['shoe_size'] = size

    # School info
    if pd.notna(row['School / University Name']):
        update_data['school_university_name'] = str(row['School / University Name'])
    if pd.notna(row['School / University Address details']):
        update_data['school_university_address'] = str(row['School / University Address details'])

    # Medical/Dietary
    if pd.notna(row['Any Medical Conditions']) and str(row['Any Medical Conditions']).upper() not in ['NO', 'NAN', 'N/A']:
        medical = str(row['Any Medical Conditions'])
        if pd.notna(row['If YES, please elaborate (or N/A if not applicable)']):
            medical += ': ' + str(row['If YES, please elaborate (or N/A if not applicable)'])
        update_data['medical_conditions'] = medical

    if pd.notna(row['Any Dietary Restrictions']) and str(row['Any Dietary Restrictions']).upper() not in ['NO', 'NAN', 'N/A']:
        dietary = str(row['Any Dietary Restrictions'])
        if pd.notna(row.get('If YES, please elaborate (or N/A if not applicable).1')):
            dietary += ': ' + str(row['If YES, please elaborate (or N/A if not applicable).1'])
        update_data['dietary_restrictions'] = dietary

    # Supporters info
    if pd.notna(row["Supporters' Full Names and Relationship to Swimmer"]):
        update_data['supporters_info'] = str(row["Supporters' Full Names and Relationship to Swimmer"])

    # Acceptance
    update_data['acceptance_intention'] = 'YES'

    # Upload URLs (passport photos, IC)
    if pd.notna(row['Uploaded passport sized photo']):
        update_data['passport_photo'] = str(row['Uploaded passport sized photo'])
    if pd.notna(row['Uploaded passport info page']):
        update_data['passport_info_page'] = str(row['Uploaded passport info page'])
    if pd.notna(row['Uploaded IC card']):
        update_data['ic_card_copy'] = str(row['Uploaded IC card'])

    # Only update if we have data
    if update_data:
        response = requests.patch(
            f'{SUPABASE_URL}/rest/v1/athletes?id=eq.{matched_id}',
            headers={**headers, 'Prefer': 'return=minimal'},
            json=update_data
        )
        if response.status_code in [200, 204]:
            updated += 1
            if updated % 20 == 0:
                print(f'  Updated {updated} athletes...')
        else:
            errors += 1
            print(f'  Error updating {excel_name}: {response.text}')

print()
print('='*50)
print('LOAD COMPLETE')
print('='*50)
print(f'Updated athletes: {updated}')
print(f'Skipped coaches: {skipped_coaches}')
print(f'Skipped wrong matches: {skipped_wrong_match}')
print(f'Skipped not found: {skipped_not_found}')
print(f'Errors: {errors}')
