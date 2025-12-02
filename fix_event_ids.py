#!/usr/bin/env python3
"""
Fix orphaned event_ids in results table by mapping them to correct events
"""

import sqlite3
from collections import defaultdict

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

print("=" * 80)
print("Fixing orphaned event_ids in results table")
print("=" * 80)

# First, get all valid events with their keys
cursor.execute("SELECT id, event_distance, event_stroke, gender FROM events")
valid_events = {}
event_key_to_id = {}
for row in cursor.fetchall():
    event_id, distance, stroke, gender = row
    valid_events[event_id] = (distance, stroke, gender)
    event_key = f"{distance}_{stroke}_{gender}"
    event_key_to_id[event_key] = event_id

print(f"\nFound {len(valid_events)} valid events in events table")

# Get all results with their current event_ids
cursor.execute("""
    SELECT r.id, r.event_id, e.event_distance, e.event_stroke, e.gender, a.gender as athlete_gender
    FROM results r
    LEFT JOIN events e ON r.event_id = e.id
    JOIN athletes a ON r.athlete_id = a.id
""")

results_to_fix = []
valid_results = 0

for row in cursor.fetchall():
    result_id, event_id, distance, stroke, gender, athlete_gender = row
    
    if event_id in valid_events:
        # Event ID is valid
        valid_results += 1
    else:
        # Event ID is orphaned - need to find correct event
        results_to_fix.append((result_id, distance, stroke, gender, athlete_gender))

print(f"Results with valid event_ids: {valid_results}")
print(f"Results with orphaned event_ids: {len(results_to_fix)}")

# Fix orphaned results
fixed_count = 0
not_found_count = 0

for result_id, distance, stroke, gender, athlete_gender in results_to_fix:
    # Use athlete_gender if gender is None (from orphaned event)
    if not gender and athlete_gender:
        gender = athlete_gender
    
    # Create event key
    event_key = f"{distance}_{stroke}_{gender}"
    
    # Find matching event
    if event_key in event_key_to_id:
        correct_event_id = event_key_to_id[event_key]
        cursor.execute("UPDATE results SET event_id = ? WHERE id = ?", (correct_event_id, result_id))
        fixed_count += 1
    else:
        print(f"  Warning: Could not find event for result {result_id}: distance={distance}, stroke={stroke}, gender={gender}")
        not_found_count += 1

conn.commit()

print(f"\nFixed {fixed_count} results")
if not_found_count > 0:
    print(f"Could not fix {not_found_count} results (event not found)")

# Verify fix
cursor.execute("""
    SELECT COUNT(*) FROM results r
    LEFT JOIN events e ON r.event_id = e.id
    WHERE e.id IS NULL
""")
still_orphaned = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM results r
    JOIN events e ON r.event_id = e.id
    JOIN athletes a ON r.athlete_id = a.id
    JOIN meets m ON r.meet_id = m.id
""")
joinable_results = cursor.fetchone()[0]

print(f"\nAfter fix:")
print(f"  Results still with orphaned event_ids: {still_orphaned}")
print(f"  Results joinable (results + events + athletes + meets): {joinable_results}")

conn.close()

print("\n" + "=" * 80)
print("✅ Event ID fix complete!")
print("=" * 80)



















