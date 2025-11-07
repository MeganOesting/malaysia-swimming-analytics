import os
import csv

TARGETS = {
    'kil, hyeonjoong': 'Y',
    'iberle, felix viktor': 'Y',
    'stepanov, elisei': 'Y',
}

def main():
    path = os.path.join('Malaysia_Times_Database', 'AthleteINFO.csv')
    if not os.path.exists(path):
        print('missing', path)
        return 1
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames or []
    # Ensure 'foreign' column exists
    if 'foreign' not in fieldnames:
        fieldnames.append('foreign')
    # Normalize/patch rows
    for row in rows:
        name = (row.get('name') or '').strip().lower()
        if name in TARGETS:
            row['foreign'] = TARGETS[name]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print('updated foreign flags for targets')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())












