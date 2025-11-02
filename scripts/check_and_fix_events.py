#!/usr/bin/env python3
"""
Check and fix event data in the database
"""

import sqlite3
import os

def check_and_fix_events():
    """Check current event data and fix stroke case issues"""
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'malaysia_swimming.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== CURRENT EVENT DATA ===")
    
    # Check current stroke values
    cursor.execute("SELECT DISTINCT stroke FROM events ORDER BY stroke")
    strokes = cursor.fetchall()
    print("Current stroke values:")
    for stroke in strokes:
        print(f"  '{stroke[0]}'")
    
    # Check current distance values
    cursor.execute("SELECT DISTINCT distance FROM events ORDER BY distance")
    distances = cursor.fetchall()
    print(f"\nCurrent distance values: {[d[0] for d in distances]}")
    
    # Check how many results have each stroke
    cursor.execute("""
        SELECT e.stroke, COUNT(r.id) as count
        FROM events e
        LEFT JOIN results r ON e.id = r.event_id
        GROUP BY e.stroke
        ORDER BY e.stroke
    """)
    stroke_counts = cursor.fetchall()
    print("\nResults per stroke:")
    for stroke, count in stroke_counts:
        print(f"  {stroke}: {count} results")
    
    # Check for case sensitivity issues
    print("\n=== CHECKING FOR CASE ISSUES ===")
    
    # Check if we have both 'Fr' and 'FR'
    cursor.execute("SELECT COUNT(*) FROM events WHERE stroke = 'Fr'")
    fr_lower = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE stroke = 'FR'")
    fr_upper = cursor.fetchone()[0]
    
    print(f"Events with 'Fr': {fr_lower}")
    print(f"Events with 'FR': {fr_upper}")
    
    if fr_lower > 0 and fr_upper == 0:
        print("\n=== FIXING CASE ISSUE ===")
        print("Converting 'Fr' to 'FR'...")
        cursor.execute("UPDATE events SET stroke = 'FR' WHERE stroke = 'Fr'")
        conn.commit()
        print("Fixed!")
        
        # Check results after fix
        cursor.execute("""
            SELECT COUNT(*) FROM results r
            JOIN events e ON r.event_id = e.id
            WHERE e.distance = 50 AND e.stroke = 'FR'
        """)
        count_after = cursor.fetchone()[0]
        print(f"50m FR results after fix: {count_after}")
    
    conn.close()

if __name__ == "__main__":
    check_and_fix_events()








