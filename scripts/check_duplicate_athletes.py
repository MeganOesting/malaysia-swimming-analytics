"""
Check for duplicate athletes in the athletes table.
Run this after every athlete import to ensure data integrity.

Duplicates defined as: same fullname + birthdate + gender

Usage: python scripts/check_duplicate_athletes.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'malaysia_swimming.db')

def check_duplicates(delete=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find duplicates: same fullname, birthdate, gender
    cursor.execute("""
        SELECT fullname, BIRTHDATE, Gender, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM athletes
        WHERE fullname IS NOT NULL
        GROUP BY UPPER(fullname), BIRTHDATE, Gender
        HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()

    print(f'Duplicate athlete sets found: {len(duplicates)}')

    if duplicates:
        print('')
        print('Duplicates (fullname, birthdate, gender, count, ids):')
        for d in duplicates[:20]:
            print(f'  {d}')
        if len(duplicates) > 20:
            print(f'  ... and {len(duplicates) - 20} more')

        if delete:
            deleted = 0
            for fullname, birthdate, gender, cnt, ids_str in duplicates:
                ids = [int(x) for x in ids_str.split(',')]
                ids.sort()
                ids_to_delete = ids[1:]
                for aid in ids_to_delete:
                    cursor.execute('DELETE FROM athletes WHERE id = ?', (str(aid),))
                    deleted += 1
            conn.commit()
            print(f'')
            print(f'[DELETED] Removed {deleted} duplicate athlete records')

    cursor.execute('SELECT COUNT(*) FROM athletes')
    total = cursor.fetchone()[0]
    print(f'')
    print(f'Total athletes in table: {total}')

    conn.close()
    return len(duplicates)

if __name__ == '__main__':
    import sys
    delete_mode = '--delete' in sys.argv
    if delete_mode:
        print('Running in DELETE mode - duplicates will be removed')
        print('')
    else:
        print('Running in CHECK mode - use --delete to remove duplicates')
        print('')
    check_duplicates(delete=delete_mode)
