"""Update SEAG athletes with confirmed birthdate matches"""
import sqlite3

# Confirmed matches from the user's review
# Format: (SEAG_name, AthleteINFO_name, birthdate)
CONFIRMED_MATCHES = [
    ('ADAM MALIK BIN AZIZUR RIZA', 'AZIZUR RIZA, Adam Malik', '2009-07-02'),
    ('AEDON LIM WEI ZHE', 'LIM, Aedon, Wei Zhe', '2012-07-26'),
    ('BRANDON YEOH HSIEN KAI', 'YEOH, Brandon Hsien Kai', '2010-02-06'),
    ('BRYSTON LEE KHAI CHENG', 'LEE, Bryston Khai Cheng', '2011-02-26'),
    ('EMMANUEL LOH YUNG MING', 'LOH, Emmanuel Yung Ming', '2009-08-20'),
    ('EVITA TAN EE LIN', 'TAN, Evita Ee Lin', '2011-03-08'),
    ('FELICIA LEE QIAN HUI', 'LEE, Felicia Qian Hui', '2009-03-04'),
    ('HANNAH WONG', 'WONG YA TING, Hannah', '2012-07-16'),
    ('HERMANN TANG BOK YU', 'TANG, Hermann Bok Yu', '2011-09-17'),
    ('ISABELLE KAM ZI ZHEN', 'KAM, Isabelle', '2010-01-04'),
    ('JODIE YIP JI SHIN', 'YIP, Jodie Ji Shin', '2012-01-23'),
    ('JOELLE CHAN ZU EE', 'CHAN, Joelle Zu-Ee', '2009-07-08'),
    ('JOSHUA LIM JI SHEN', 'LIM, Joshua Ji-Shen', '2010-10-29'),
    ('JOVIAL CHAN ZEN EE', 'CHAN, Jovial Zen Ee', '2012-08-29'),
    ('KAELYN CHEE WEI YI', 'CHEE, Kaelyn Wei Yi', '2009-10-17'),
    ('KAYLEIGH ANG ZHI XUAN', 'ANG, Kayleigh Zhi Xuan', '2010-06-28'),
    ('KHOR YUE LYNN', 'KHOR, Mishya Yue Lynn', '2009-12-01'),
    ('LYNNA YEOW YI JING', 'YEOW, Lynna Yi Jing', '2009-04-03'),
    ('MORGAN ELEVEN TEO KAI CHENG', 'ELEVEN TEO, Morgan Kai Cheng', '2007-04-14'),
    ('MUHAMMAD DHUHA BIN ZULFIKRY', 'BIN ZULFIKRY, Muhd Dhuha', '2008-04-11'),
    ('NATHANIEL SHU JIA JUN', 'SHU, Nathaniel Jia Jun', '2011-11-05'),
    ('NISHAN CHRISTOPHER MANUEL', 'MANUEL, Nishan', '2010-09-27'),
    ('NOAH BIN ABDUL RIZAL', 'RIZAL, Noah Abdul', '2012-08-07'),
    ('ONG YHA ROU NATASHA', 'ONG, Yha Rou', '2010-02-17'),
    ('RYAN LIAW CHEE HENG', 'LIAW, Ryan Chee Heng', '2010-03-01'),
    ('SAMUEL LAI CHONG WENG', 'CHONG CHENG, Samuel Ng', '2006-04-25'),
    ('SEOW CUI YING', 'SEOW, Olivia Cui Ying', '2011-03-05'),
    ('SHANNON TAN YAN QING *', 'SHANNON TAN, Yan Qing', '2010-12-18'),
    ('SHEAMUS CHEW HENG YI', 'CHEW, Sheamus Heng Yi', '2012-02-21'),
    ('VIVIAN TEE XIN LING', 'TEE, Vivian Xin Ling', '2011-03-03'),
]

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

print("=" * 100)
print("Updating SEAG Athletes with Confirmed Birthdates")
print("=" * 100)

updated_count = 0
not_found = []

for seag_name, ai_name, birthdate in CONFIRMED_MATCHES:
    # Find the SEAG athlete
    cursor.execute("""
        SELECT DISTINCT a.id, a.name
        FROM athletes a
        JOIN results r ON a.id = r.athlete_id
        JOIN meets m ON r.meet_id = m.id
        WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
        AND UPPER(a.name) = UPPER(?)
        AND a.birth_date IS NULL
    """, (seag_name,))
    
    result = cursor.fetchone()
    if result:
        athlete_id, current_name = result
        cursor.execute("""
            UPDATE athletes 
            SET birth_date = ?
            WHERE id = ?
        """, (birthdate, athlete_id))
        updated_count += 1
        print(f"✅ Updated: {current_name} -> {birthdate}")
    else:
        not_found.append(seag_name)
        print(f"⚠️  Not found: {seag_name}")

conn.commit()

print(f"\n{'='*100}")
print(f"Update Summary:")
print(f"  Updated: {updated_count} athletes")
print(f"  Not found: {len(not_found)}")

# Now show who's left
print(f"\n{'='*100}")
print("Remaining SEAG Athletes Without Birthdates:")
print("=" * 100)

cursor.execute("""
    SELECT DISTINCT a.id, a.name
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
    AND a.birth_date IS NULL
    ORDER BY a.name
""")

remaining = cursor.fetchall()

if remaining:
    print(f"\nFound {len(remaining)} SEAG athletes still without birthdates:\n")
    for athlete_id, athlete_name in remaining:
        print(f"  - {athlete_name}")
else:
    print("\n✅ All SEAG athletes now have birthdates!")

conn.close()


