import os
import re
import shutil
import datetime as _dt
import pandas as pd

SEAG_FILE = 'SEAG_2025_ALL.xlsx'
SEAG_SHEET = 'SEAG_2025_ALL'
INFO_PREFIX = 'SEA Age Swimmer Info'
BACKUP = 'SEAG_2025_ALL.birthdate_backup.xlsx'

# SEAG sheet columns (0-based): E=4 (Name), F=5 (Birthdate target)
COL_E_NAME = 4
COL_F_BIRTHDATE = 5

# INFO book columns (0-based): B=1 (Name), C=2 (day), D=3 (month), E=4 (year)
INFO_COL_NAME = 1
INFO_COL_D = 2
INFO_COL_M = 3
INFO_COL_Y = 4

def norm_name(s: str) -> str:
    if s is None:
        return ''
    s = str(s).strip().lower()
    s = re.sub(r'[^a-z\s]+', ' ', s)
    s = ' '.join(s.split())
    return s

def try_int(v):
    try:
        iv = int(float(str(v)))
        return iv
    except Exception:
        return None

def parse_triplet(d, m, y):
    dd = try_int(d)
    mm = try_int(m)
    yy = try_int(y)
    if dd and mm and yy and 1900 <= yy <= 2100 and 1 <= mm <= 12 and 1 <= dd <= 31:
        try:
            return _dt.date(yy, mm, dd)
        except Exception:
            return None
    return None

def find_info_file():
    for fn in os.listdir('.'):
        low = fn.lower()
        if low.startswith(INFO_PREFIX.lower()) and low.endswith(('.xlsx', '.xls')):
            return fn
    return None

def main():
    if not os.path.exists(SEAG_FILE):
        print(f"Missing {SEAG_FILE} in project root")
        return 1
    info_file = find_info_file()
    if not info_file:
        print(f"Could not find an info file matching '{INFO_PREFIX}*.xlsx' in the project root")
        return 1
    # Build name->DOB mapping
    try:
        xl = pd.ExcelFile(info_file)
        info_sheet = xl.sheet_names[0]
        info = pd.read_excel(xl, sheet_name=info_sheet, header=None)
    except Exception as e:
        print(f"Failed reading info workbook: {e}")
        return 1
    mapping = {}
    for i in info.index:
        name = info.iat[i, INFO_COL_NAME] if INFO_COL_NAME < info.shape[1] else None
        if pd.isna(name):
            continue
        d = info.iat[i, INFO_COL_D] if INFO_COL_D < info.shape[1] else None
        m = info.iat[i, INFO_COL_M] if INFO_COL_M < info.shape[1] else None
        y = info.iat[i, INFO_COL_Y] if INFO_COL_Y < info.shape[1] else None
        dob = parse_triplet(d, m, y)
        if dob is None:
            for val in (d, m, y):
                try:
                    ts = pd.to_datetime(val, dayfirst=True, errors='coerce')
                    if pd.notna(ts):
                        dob = ts.date()
                        break
                except Exception:
                    pass
        if dob is not None:
            mapping[norm_name(name)] = dob
    if not mapping:
        print("No name->DOB mappings built from info file; aborting.")
        return 1

    # Read SEAG sheet
    try:
        xl2 = pd.ExcelFile(SEAG_FILE)
        seag_sheet_name = next((n for n in xl2.sheet_names if n.strip().lower() == SEAG_SHEET.lower()), xl2.sheet_names[0])
        df = pd.read_excel(xl2, sheet_name=seag_sheet_name, header=None)
    except Exception as e:
        print(f"Failed reading {SEAG_FILE}: {e}")
        return 1
    before = int(df[COL_F_BIRTHDATE].notna().sum()) if COL_F_BIRTHDATE < df.shape[1] else 0
    updates = 0
    missing = 0
    for i in df.index:
        name_e = df.iat[i, COL_E_NAME] if COL_E_NAME < df.shape[1] else None
        if pd.isna(name_e):
            continue
        if COL_F_BIRTHDATE < df.shape[1] and pd.notna(df.iat[i, COL_F_BIRTHDATE]) and str(df.iat[i, COL_F_BIRTHDATE]).strip() != '':
            continue
        key = norm_name(name_e)
        dob = mapping.get(key)
        if dob is not None:
            df.iat[i, COL_F_BIRTHDATE] = dob
            updates += 1
        else:
            missing += 1
    try:
        shutil.copyfile(SEAG_FILE, BACKUP)
        print(f"Backup created: {BACKUP}")
    except Exception as e:
        print(f"Warning: could not create backup: {e}")
    try:
        with pd.ExcelWriter(SEAG_FILE, engine='openpyxl', datetime_format='yyyy-mm-dd', date_format='yyyy-mm-dd') as writer:
            df.to_excel(writer, index=False, header=False, sheet_name=seag_sheet_name)
        after = int(df[COL_F_BIRTHDATE].notna().sum()) if COL_F_BIRTHDATE < df.shape[1] else 0
        print(f"Filled Birthdate (F) for {updates} rows (non-empty before: {before}, after: {after}).")
        if missing:
            print(f"Note: {missing} name(s) in SEAG sheet did not match the info book.")
        return 0
    except Exception as e:
        print(f"Failed to write updated SEAG workbook: {e}")
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
