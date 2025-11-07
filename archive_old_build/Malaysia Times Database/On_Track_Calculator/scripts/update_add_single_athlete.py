import os
import csv

ROW = {
    'name': 'IBERLE, Felix Viktor',
    'birthdate_yyyymmdd': '20050204',
    'id_hint': 'IB20050204',
    'gender': 'M',
    'team_name': 'Chinese Swimming Club, Penang',
    'state_code': 'PNG',
    'foreign': 'Y',
    'source': 'STATE 2024',
    'event': '50m Fr',
}

def main():
    path = os.path.join('Malaysia_Times_Database', 'AthleteINFO.csv')
    write_header = not os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        fields = ['name','birthdate_yyyymmdd','id_hint','gender','team_name','state_code','foreign','source','event']
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        w.writerow(ROW)
    print('appended', ROW['name'])

if __name__ == '__main__':
    main()










