import sqlite3

meets = [
    'Aquatics GB Swimming Championships',
    'Australian Age Group Championships',
    'Irish Open Championships',
    'International Meet',
    'National Arena League: Cup Final',
    'Legacy Meet - Finals',
    '67th Malaysian Open Championships'
]

def main():
    conn = sqlite3.connect('malaysia_swimming.db')
    cur = conn.cursor()
    for name in meets:
        cur.execute('SELECT COUNT(*) FROM results r JOIN meets m ON r.meet_id = m.id WHERE m.name = ?', (name,))
        total = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM results r JOIN meets m ON r.meet_id = m.id WHERE m.name = ? AND (r.year_age IS NOT NULL OR r.day_age IS NOT NULL)', (name,))
        with_age = cur.fetchone()[0]
        print(f'{name}: total={total}, with age={with_age}')
    conn.close()

if __name__ == '__main__':
    main()
