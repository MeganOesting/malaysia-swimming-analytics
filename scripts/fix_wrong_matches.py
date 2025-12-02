"""
Fix wrong matches and add remaining coaches
"""
import requests
import pandas as pd

SUPABASE_URL = 'https://bvmqstoeahseklvmvdlx.supabase.co'
SUPABASE_KEY = 'sb_publishable_-0n963Zy08gBMJPMse2V8A_xAyHgKZM'
headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

# Load Excel for full data
file_path = r'C:\Users\megan\Downloads\Additional Games Info (Passport,School, Sizes) (2).xlsx'
df = pd.read_excel(file_path)

# =============================================
# 1. UPDATE HO WEI YAN (ID 1771)
# =============================================
print('=== UPDATING HO WEI YAN (ID 1771) ===')
ho_rows = df[df['Name'].str.contains('Ho Wei Yan', case=False, na=False)]
if len(ho_rows) > 0:
    ho_row = ho_rows.iloc[0]
    update_data = {
        'passport_number': str(ho_row['MAS Passport No']) if pd.notna(ho_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    if pd.notna(ho_row['School / University Name']):
        update_data['school_university_name'] = str(ho_row['School / University Name'])

    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.1771',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 2. UPDATE BRYAN LEONG (ID 2102) + ADD ALIAS
# =============================================
print()
print('=== UPDATING BRYAN LEONG (ID 2102) ===')
bryan_rows = df[df['Name'].str.contains('Bryan Leong', case=False, na=False)]
if len(bryan_rows) > 0:
    bryan_row = bryan_rows.iloc[0]
    update_data = {
        'athlete_alias_1': 'Bryan Leong Xin Ren',
        'birthdate': '2003-02-25T00:00:00Z',
        'passport_number': str(bryan_row['MAS Passport No']) if pd.notna(bryan_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    if pd.notna(bryan_row['School / University Name']):
        update_data['school_university_name'] = str(bryan_row['School / University Name'])

    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.2102',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 3. UPDATE ELSON LEE (ID 940)
# =============================================
print()
print('=== UPDATING ELSON LEE (ID 940) ===')
elson_rows = df[df['Name'].str.contains('Elson Lee', case=False, na=False)]
if len(elson_rows) > 0:
    elson_row = elson_rows.iloc[0]
    update_data = {
        'passport_number': str(elson_row['MAS Passport No']) if pd.notna(elson_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.940',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 4. UPDATE ISABELLE KAM (ID 3042)
# =============================================
print()
print('=== UPDATING ISABELLE KAM (ID 3042) ===')
isabelle_rows = df[df['Name'].str.contains('Isabelle Kam', case=False, na=False)]
if len(isabelle_rows) > 0:
    isabelle_row = isabelle_rows.iloc[0]
    update_data = {
        'passport_number': str(isabelle_row['MAS Passport No']) if pd.notna(isabelle_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.3042',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 5. UPDATE ANDREW GOH (ID 2534)
# =============================================
print()
print('=== UPDATING ANDREW GOH (ID 2534) ===')
andrew_rows = df[df['Name'].str.contains('Andrew Goh', case=False, na=False)]
if len(andrew_rows) > 0:
    andrew_row = andrew_rows.iloc[0]
    update_data = {
        'passport_number': str(andrew_row['MAS Passport No']) if pd.notna(andrew_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.2534',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 6. UPDATE SOPHOCLES NG (ID 2372)
# =============================================
print()
print('=== UPDATING SOPHOCLES NG (ID 2372) ===')
sophocles_rows = df[df['Name'].str.contains('Sophocles', case=False, na=False)]
if len(sophocles_rows) > 0:
    sophocles_row = sophocles_rows.iloc[0]
    update_data = {
        'passport_number': str(sophocles_row['MAS Passport No']) if pd.notna(sophocles_row['MAS Passport No']) else None,
        'role': 'Athlete',
        'sport': 'Swimming',
        'acceptance_intention': 'YES'
    }
    response = requests.patch(
        f'{SUPABASE_URL}/rest/v1/athletes?id=eq.2372',
        headers={**headers, 'Prefer': 'return=minimal'},
        json=update_data
    )
    print(f'  Status: {response.status_code}')

# =============================================
# 7. ADD MARK CHUA as Coach (Selangor State Coach, PADE)
# =============================================
print()
print('=== ADDING MARK CHUA YU FOONG (Coach) ===')
mark_rows = df[df['Name'].str.contains('Mark Chua', case=False, na=False)]
if len(mark_rows) > 0:
    mark_row = mark_rows.iloc[0]
    mark_coach = {
        'coach_name': 'Mark Chua Yu Foong',
        'birthdate': '1977-12-13T00:00:00Z',
        'gender': 'M',
        'nation': 'MAS',
        'club_name': 'PADE',
        'coach_role': 'State Coach',
        'state_coach': 1,
    }
    if pd.notna(mark_row['MAS Passport No']):
        mark_coach['coach_passport_number'] = str(mark_row['MAS Passport No'])

    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/coaches',
        headers={**headers, 'Prefer': 'return=representation'},
        json=mark_coach
    )
    print(f'  Status: {response.status_code}')
    if response.status_code == 201:
        print(f'  Added as ID: {response.json()[0]["id"]}')

# =============================================
# 8. ADD ALBERT YEAP as Coach (Penang State Coach, WAHOO)
# =============================================
print()
print('=== ADDING ALBERT YEAP JIN TEIK (Coach) ===')
albert_rows = df[df['Name'].str.contains('Albert Yeap', case=False, na=False)]
if len(albert_rows) > 0:
    albert_row = albert_rows.iloc[0]
    albert_coach = {
        'coach_name': 'Albert Yeap Jin Teik',
        'birthdate': '1979-11-18T00:00:00Z',
        'gender': 'M',
        'nation': 'MAS',
        'club_name': 'WAHOO',
        'coach_role': 'State Coach',
        'state_coach': 1,
    }
    if pd.notna(albert_row['MAS Passport No']):
        albert_coach['coach_passport_number'] = str(albert_row['MAS Passport No'])

    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/coaches',
        headers={**headers, 'Prefer': 'return=representation'},
        json=albert_coach
    )
    print(f'  Status: {response.status_code}')
    if response.status_code == 201:
        print(f'  Added as ID: {response.json()[0]["id"]}')

# =============================================
# VERIFY
# =============================================
print()
print('=== VERIFICATION ===')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/coaches?select=id,coach_name,coach_role,club_name,state_coach',
    headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
)
print('Coaches:')
for c in response.json():
    print(f'  {c}')

# Check Bryan
print()
print('Bryan Leong (ID 2102):')
response = requests.get(
    f'{SUPABASE_URL}/rest/v1/athletes?id=eq.2102&select=id,fullname,athlete_alias_1,birthdate,passport_number',
    headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
)
print(f'  {response.json()}')
