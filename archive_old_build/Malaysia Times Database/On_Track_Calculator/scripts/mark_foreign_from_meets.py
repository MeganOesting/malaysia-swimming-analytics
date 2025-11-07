import os
import csv
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


def detect_columns(df: pd.DataFrame):
    # Try a header row to detect column names
    # If row 1 exists with strings, find indices for FULLNAME and NATION
    name_idx = None
    nation_idx = None
    try:
        if df is None or df.empty:
            return name_idx, nation_idx
        # scan first 5 rows to find header labels
        for hdr_row in range(min(5, len(df))):
            row_vals = [str(df.iat[hdr_row, j]).strip().lower() if j < df.shape[1] else '' for j in range(df.shape[1])]
            for j, v in enumerate(row_vals):
                if v == 'fullname':
                    name_idx = j
                if v == 'nation':
                    nation_idx = j
            if name_idx is not None and nation_idx is not None:
                return name_idx, nation_idx
    except Exception:
        return None, None
    return name_idx, nation_idx


def collect_foreign_names(meets_dir: str) -> set:
    foreign_names = set()
    for fn in os.listdir(meets_dir):
        if not fn.lower().endswith(('.xls', '.xlsx')):
            continue
        path = os.path.join(meets_dir, fn)
        engine = 'xlrd' if fn.lower().endswith('.xls') else None
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
            name_col, nation_col = detect_columns(df)
            if name_col is None or nation_col is None:
                continue
            for i in df.index:
                nm = (str(df.iat[i, name_col]).strip() if name_col < df.shape[1] and pd.notna(df.iat[i, name_col]) else '')
                if not nm or nm.lower() == 'fullname':
                    continue
                nat = (str(df.iat[i, nation_col]).strip().upper() if nation_col < df.shape[1] and pd.notna(df.iat[i, nation_col]) else '')
                if nat and nat != 'MAS':
                    foreign_names.add(norm_name(nm))
    return foreign_names


def main():
    meets_dir = os.path.join('Meets')
    ai_csv = os.path.join('Malaysia_Times_Database', 'AthleteINFO.csv')
    if not os.path.exists(ai_csv):
        print('missing', ai_csv)
        return 1
    foreign_from_meets = collect_foreign_names(meets_dir)
    updated = 0
    with open(ai_csv, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames or []
    if 'foreign' not in fieldnames:
        fieldnames.append('foreign')
    for row in rows:
        nm = norm_name(row.get('name') or '')
        if nm in foreign_from_meets:
            if (row.get('foreign') or '').strip().upper() != 'Y':
                row['foreign'] = 'Y'
                updated += 1
    with open(ai_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print('foreign_marked', updated)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())












