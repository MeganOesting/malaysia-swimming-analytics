#!/usr/bin/env python3
"""
Delete state meet records and their associated results from the database
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
print("Deleting State Meet Records")
print("=" * 80)

# Identify state meets by name patterns (matching the logic from results.py)
state_meet_patterns = [
    "Selangor", "Sarawak", "Sabah", "Pasa", "Perak", "Johor", 
    "Milo/Akl", "Kedah", "Pahang", "Kelantan", "Melaka", "Negeri",
    "Terengganu", "Penang"
]

# Exclude national meets
national_meet_patterns = [
    "Malaysia Age Group", "MIAG", "Southeast Asian", "SEA Age"
]

# Find state meet IDs
cursor.execute("SELECT id, name FROM meets")
all_meets = cursor.fetchall()

state_meet_ids = []
for meet_id, meet_name in all_meets:
    is_national_meet = any(pattern.lower() in meet_name.lower() for pattern in national_meet_patterns)
    is_state_meet = (not is_national_meet) and (
        any(pattern.lower() in meet_name.lower() for pattern in state_meet_patterns)
    )
    
    if is_state_meet:
        state_meet_ids.append(meet_id)
        print(f"Found state meet: {meet_name} ({meet_id[:8]}...)")

if not state_meet_ids:
    print("\n⚠️  No state meets found to delete.")
    conn.close()
    exit(0)

print(f"\n📊 Summary:")
print(f"  State meets found: {len(state_meet_ids)}")

# Count results to be deleted
placeholders = ','.join(['?' for _ in state_meet_ids])
cursor.execute(f"""
    SELECT COUNT(*) FROM results 
    WHERE meet_id IN ({placeholders})
""", state_meet_ids)
result_count = cursor.fetchone()[0]
print(f"  Results to delete: {result_count}")

# Confirm deletion
response = input("\n⚠️  Are you sure you want to delete these state meets and all their results? (yes/no): ")
if response.lower() != 'yes':
    print("❌ Deletion cancelled.")
    conn.close()
    exit(0)

# Delete results first (due to foreign key constraints)
print("\n🗑️  Deleting results...")
cursor.execute(f"""
    DELETE FROM results 
    WHERE meet_id IN ({placeholders})
""", state_meet_ids)
results_deleted = cursor.rowcount

# Delete meets
print("🗑️  Deleting meets...")
cursor.execute(f"""
    DELETE FROM meets 
    WHERE id IN ({placeholders})
""", state_meet_ids)
meets_deleted = cursor.rowcount

conn.commit()

print(f"\n✅ Deletion complete!")
print(f"  Meets deleted: {meets_deleted}")
print(f"  Results deleted: {results_deleted}")

# Verify deletion
cursor.execute("SELECT COUNT(*) FROM meets")
remaining_meets = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM results")
remaining_results = cursor.fetchone()[0]

print(f"\n📊 Remaining in database:")
print(f"  Meets: {remaining_meets}")
print(f"  Results: {remaining_results}")

conn.close()

print("\n" + "=" * 80)
print("✅ State meets deleted successfully!")
print("=" * 80)
print("\nYou can now upload new state meet files through the admin panel.")












