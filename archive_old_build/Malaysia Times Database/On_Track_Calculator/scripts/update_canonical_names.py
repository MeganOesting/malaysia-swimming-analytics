import os
import csv

CANON = {
    '08062011': 'CHAN, Sophie Yilin',
    '09092008': 'YAP, You Quan Ethan',
    '11022010': "CH'NG, Kay Qing",
    '13062012': 'KOK, Yun Yi',
    '18012004': 'AHMAD, Muhammad Zulhilmi b',
    '18092010': 'NGO, YI Rui Chereen',
    '18122001': 'NG, Tze Xiang George',
    '20032009': 'CHUA, Evan Min Hao',
    '21122009': 'YIJIAN, Wan Oliver',
}

def main():
    path = os.path.join('Malaysia_Times_Database', 'AthleteINFO.csv')
    if not os.path.exists(path):
        print('missing', path)
        return 1
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        fieldnames = r.fieldnames or []
        for row in r:
            b = (row.get('birthdate_yyyymmdd') or row.get('birthdate') or '').strip()
            if b in CANON:
                row['name'] = CANON[b]
            rows.append(row)
    # Write back preserving header
    with open(path, 'w', newline='', encoding='utf-8') as f:
        if rows:
            fieldnames = list(rows[0].keys())
        else:
            fieldnames = ['name','birthdate_yyyymmdd','id_hint','gender','team_name','state_code','foreign','source','event']
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print('updated canonical names for', len(CANON), 'birthdates')

if __name__ == '__main__':
    main()












