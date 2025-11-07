import os
import csv
from typing import Dict, List
import pandas as pd


def norm_name(s: str) -> str:
    if s is None:
        return ''
    s = str(s).strip().lower()
    out = []
    for ch in s:
        if ch.isalpha() or ch.isspace():
            out.append(ch)
    return ' '.join(''.join(out).split())


def first_two_letters(name_as_written: str) -> str:
    s = (name_as_written or '').strip()
    return s[:2]


def pad_birthdate_digits(d: str) -> str:
    digits = ''.join(ch for ch in str(d) if ch.isdigit())
    if len(digits) == 7:
        return '0' + digits
    return digits


def load_clubs_map(clubs_xlsx: str) -> Dict[str, str]:
    """Return normalized/exact name -> state_code map.
    Exact map uses raw string as-is; normalized map uses lowercased, collapsed spaces.
    """
    try:
        import openpyxl
    except Exception:
        return {}
    if not os.path.exists(clubs_xlsx):
        return {}
    exact: Dict[str, str] = {}
    normd: Dict[str, str] = {}
    wb = openpyxl.load_workbook(clubs_xlsx, data_only=True)
    for ws in wb.worksheets:
        sheet_code = (ws.title or '').strip().upper()
        for r in ws.iter_rows(values_only=True):
            try:
                name = (str(r[0]) if r and len(r) >= 1 and r[0] is not None else '').strip()
                code_cell = (str(r[2]) if r and len(r) >= 3 and r[2] is not None else '').strip().upper()
            except Exception:
                continue
            if not name:
                continue
            code = code_cell or sheet_code
            exact[name] = code
            nn = ' '.join(str(name).lower().split())
            normd[nn] = code
    # Combine: prefer exact first, then normalized
    out = {}
    out.update(exact)
    # avoid overwriting exact with normed different key case
    for k, v in normd.items():
        out.setdefault(k, v)
    return out


def resolve_state_from_club(q_raw: str, clubs_map: Dict[str, str]) -> str:
    if not q_raw:
        return ''
    exact = clubs_map.get(q_raw)
    if exact:
        return exact
    nn = ' '.join(q_raw.lower().split())
    return clubs_map.get(nn, '')


def collect_january_rows() -> List[Dict[str, str]]:
    base = os.path.join('Meets')
    files = ['January2024StateMeetsMen.xls', 'January2024StateMeetsWomen.xls']
    out: List[Dict[str, str]] = []
    for fname in files:
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            continue
        engine = 'xlrd' if fname.lower().endswith('.xls') else None
        try:
            xl = pd.ExcelFile(path, engine=engine)
        except Exception:
            continue
        for sheet in xl.sheet_names:
            try:
                df = pd.read_excel(path, sheet_name=sheet, header=None, engine=engine)
            except Exception:
                continue
            if df is None or df.empty:
                continue
            # Columns of interest
            col_gender = df.get(1)
            col_name = df.get(4)
            col_birth = df.get(5)
            col_team = df.get(16)
            event_label = sheet
            for idx in df.index:
                name = (str(col_name.loc[idx]).strip() if col_name is not None and idx in col_name.index and pd.notna(col_name.loc[idx]) else '')
                if not name:
                    continue
                gender_val = ''
                try:
                    g = (col_gender.loc[idx] if col_gender is not None and idx in col_gender.index else '')
                    gs = str(g).strip().upper()
                    gender_val = 'M' if gs == 'M' else ('F' if gs == 'F' else '')
                except Exception:
                    gender_val = ''
                birth_raw = (str(col_birth.loc[idx]).strip() if col_birth is not None and idx in col_birth.index and pd.notna(col_birth.loc[idx]) else '')
                b8 = pad_birthdate_digits(birth_raw) if birth_raw else ''
                team_raw = (str(col_team.loc[idx]).strip() if col_team is not None and idx in col_team.index and pd.notna(col_team.loc[idx]) else '')
                out.append({
                    'name': name,
                    'gender': gender_val,
                    'birthdate_yyyymmdd': b8,
                    'team_name': team_raw,
                    'event': event_label,
                    'source': 'STATE 2024',
                })
    return out


def main():
    info_csv = os.path.join('Malaysia_Times_Database', 'AthleteINFO.csv')
    clubs_xlsx = os.path.join('Malaysia_Times_Database', 'Clubs_By_State.xlsx')
    clubs_map = load_clubs_map(clubs_xlsx)

    existing = set()
    if os.path.exists(info_csv):
        with open(info_csv, newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                nm = (row.get('name') or '').strip()
                if nm:
                    existing.add(norm_name(nm))

    rows = collect_january_rows()
    to_append: List[Dict[str, str]] = []
    for r in rows:
        nm_norm = norm_name(r['name'])
        if nm_norm in existing:
            continue
        state_code = resolve_state_from_club(r['team_name'], clubs_map)
        # Foreign: if mapped sheet code was HKG or MGL (we approximated via clubs_map value)
        foreign = 'Y' if state_code in ('HKG', 'MGL') else 'N'
        new_id = first_two_letters(r['name']) + (r['birthdate_yyyymmdd'] or '')
        to_append.append({
            'name': r['name'],
            'birthdate_yyyymmdd': r['birthdate_yyyymmdd'],
            'id_hint': new_id,
            'gender': r['gender'],
            'team_name': r['team_name'],
            'state_code': state_code,
            'foreign': foreign,
            'source': r['source'],
            'event': r['event'],
        })

    # Append
    fieldnames = ['name','birthdate_yyyymmdd','id_hint','gender','team_name','state_code','foreign','source','event']
    write_header = not os.path.exists(info_csv)
    with open(info_csv, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        for row in to_append:
            w.writerow(row)

    # Duplicate birthdates
    dup = {}
    with open(info_csv, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            b = (row.get('birthdate_yyyymmdd') or row.get('birthdate') or '').strip()
            n = (row.get('name') or '').strip()
            if not b:
                continue
            dup.setdefault(b, []).append(n)
    dup = {k: v for k, v in dup.items() if len(v) > 1}
    out_path = os.path.abspath('duplicate_birthdates_report.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        for b, names in sorted(dup.items()):
            f.write(b + ' : ' + '; '.join(names) + '\n')

    print('appended_count', len(to_append))
    print('duplicate_report', out_path)


if __name__ == '__main__':
    main()



