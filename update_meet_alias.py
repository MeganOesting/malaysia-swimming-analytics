#!/usr/bin/env python3
"""
Update a meet's alias (meet_code) in the database
"""

import sqlite3
from pathlib import Path

# Database path
db_path = Path('malaysia_swimming.db')
if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("Update Meet Alias (meet_code)")
print("=" * 80)

# Show all meets
cursor.execute("SELECT id, name, meet_type FROM meets ORDER BY name")
meets = cursor.fetchall()

if not meets:
    print("\nNo meets found in database.")
    conn.close()
    exit(0)

print("\nCurrent meets in database:")
print("-" * 80)
for i, (meet_id, name, meet_code) in enumerate(meets, 1):
    print(f"{i}. {name}")
    print(f"   ID: {meet_id[:20]}...")
    print(f"   Current alias: {meet_code or '(none)'}")
    print()

# Get meet to update
try:
    choice = input("Enter the number of the meet to update (or 'q' to quit): ").strip()
    if choice.lower() == 'q':
        print("Cancelled.")
        conn.close()
        exit(0)
    
    choice_num = int(choice) - 1
    if choice_num < 0 or choice_num >= len(meets):
        print("❌ Invalid selection.")
        conn.close()
        exit(1)
    
    selected_meet = meets[choice_num]
    meet_id = selected_meet[0]
    current_name = selected_meet[1]
    current_alias = selected_meet[2]
    
    print(f"\nSelected meet: {current_name}")
    print(f"Current alias: {current_alias or '(none)'}")
    
    # Get new alias
    new_alias = input("\nEnter new alias/code (e.g., MO25): ").strip()
    if not new_alias:
        print("❌ Alias cannot be empty.")
        conn.close()
        exit(1)
    
    # Confirm
    print(f"\n⚠️  About to update:")
    print(f"   Meet: {current_name}")
    print(f"   Alias: {current_alias or '(none)'} -> {new_alias}")
    confirm = input("\nConfirm update? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Update cancelled.")
        conn.close()
        exit(0)
    
    # Update the meet
    cursor.execute("""
        UPDATE meets 
        SET meet_type = ? 
        WHERE id = ?
    """, (new_alias, meet_id))
    
    conn.commit()
    
    print(f"\n✅ Successfully updated meet alias to: {new_alias}")
    
    # Verify
    cursor.execute("SELECT name, meet_type FROM meets WHERE id = ?", (meet_id,))
    updated = cursor.fetchone()
    print(f"   Verified: {updated[0]} -> {updated[1]}")
    
except ValueError:
    print("❌ Invalid input. Please enter a number.")
except KeyboardInterrupt:
    print("\n\nCancelled.")
except Exception as e:
    print(f"\n❌ Error: {e}")

conn.close()

print("\n" + "=" * 80)


