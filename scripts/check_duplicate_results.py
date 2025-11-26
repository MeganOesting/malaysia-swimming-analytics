"""
Check for duplicate results in the results table.
Run this after every results upload to ensure data integrity.

Usage: python scripts/check_duplicate_results.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'malaysia_swimming.db')

def check_duplicates(delete=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Find duplicates: same meet_id, event_id, athlete_id, time_seconds
    cursor.execute('''
        SELECT meet_id, event_id, athlete_id, time_seconds, COUNT(*) as cnt
        FROM results
        WHERE athlete_id IS NOT NULL
        GROUP BY meet_id, event_id, athlete_id, time_seconds
        HAVING cnt > 1
    ''')
    duplicates = cursor.fetchall()

    print(f'Duplicate result sets found: {len(duplicates)}')

    if duplicates:
        print('\nDuplicates (meet_id, event_id, athlete_id, time_seconds, count):')
        for d in duplicates[:20]:
            print(f'  {d}')
        if len(duplicates) > 20:
            print(f'  ... and {len(duplicates) - 20} more')

        if delete:
            # Delete duplicates, keeping only one of each
            deleted = 0
            for meet_id, event_id, athlete_id, time_seconds, cnt in duplicates:
                # Get all IDs for this duplicate set
                cursor.execute('''
                    SELECT id FROM results
                    WHERE meet_id = ? AND event_id = ? AND athlete_id = ? AND time_seconds = ?
                    ORDER BY id
                ''', (meet_id, event_id, athlete_id, time_seconds))
                ids = [row[0] for row in cursor.fetchall()]

                # Keep first, delete rest
                ids_to_delete = ids[1:]
                for rid in ids_to_delete:
                    cursor.execute('DELETE FROM results WHERE id = ?', (rid,))
                    deleted += 1

            conn.commit()
            print(f'\n[DELETED] Removed {deleted} duplicate rows')

    # Total results count
    cursor.execute('SELECT COUNT(*) FROM results')
    total = cursor.fetchone()[0]
    print(f'\nTotal results in table: {total}')

    conn.close()
    return len(duplicates)

if __name__ == '__main__':
    import sys
    delete_mode = '--delete' in sys.argv
    if delete_mode:
        print('Running in DELETE mode - duplicates will be removed\n')
    else:
        print('Running in CHECK mode - use --delete to remove duplicates\n')

    check_duplicates(delete=delete_mode)
