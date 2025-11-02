import sqlite3

conn = sqlite3.connect('database/malaysia_swimming.db')
cursor = conn.cursor()

print('=== SUKMA DATA VERIFICATION ===')
print()

# Check meets table
cursor.execute("SELECT * FROM meets WHERE name LIKE '%SUK%' OR name LIKE '%Sukma%'")
meets = cursor.fetchall()
print('SUKMA meets in database:')
for meet in meets:
    print(f'  {meet}')
print()

# Check results for SUKMA
cursor.execute("SELECT COUNT(*) FROM results WHERE meet = 'SUK24'")
sukma_count = cursor.fetchone()[0]
print(f'SUKMA results count: {sukma_count}')
print()

# Sample SUKMA results
cursor.execute("SELECT name, gender, age, distance, stroke, time, place, aqua_points, meet FROM results WHERE meet = 'SUK24' LIMIT 10")
sample_results = cursor.fetchall()
print('Sample SUKMA results:')
for result in sample_results:
    print(f'  {result}')
print()

# Check unique events in SUKMA
cursor.execute("SELECT DISTINCT distance, stroke FROM results WHERE meet = 'SUK24' ORDER BY distance, stroke")
events = cursor.fetchall()
print('SUKMA events:')
for event in events:
    print(f'  {event[0]}m {event[1]}')
print()

# Check gender distribution
cursor.execute("SELECT gender, COUNT(*) FROM results WHERE meet = 'SUK24' GROUP BY gender")
gender_dist = cursor.fetchall()
print('SUKMA gender distribution:')
for gender, count in gender_dist:
    print(f'  {gender}: {count} results')
print()

# Check age distribution
cursor.execute("SELECT age, COUNT(*) FROM results WHERE meet = 'SUK24' GROUP BY age ORDER BY age")
age_dist = cursor.fetchall()
print('SUKMA age distribution:')
for age, count in age_dist:
    print(f'  Age {age}: {count} results')
print()

conn.close()



