"""Find potential matches for SEAG athletes without birthdates"""
import sqlite3
from difflib import SequenceMatcher

def normalize_name(name):
    """Normalize name for matching"""
    if not name:
        return ""
    # Remove punctuation, convert to uppercase, strip whitespace
    name = str(name).upper().strip()
    # Remove common punctuation
    for char in ".,'-":
        name = name.replace(char, " ")
    # Collapse multiple spaces
    name = " ".join(name.split())
    return name

def name_similarity(name1, name2):
    """Calculate similarity between two names (0-1)"""
    return SequenceMatcher(None, normalize_name(name1), normalize_name(name2)).ratio()

def create_name_variations(name):
    """Create variations of a name for matching"""
    if not name:
        return []
    
    variations = set()
    normalized = normalize_name(name)
    variations.add(normalized)
    
    # If name has comma, try both orders
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        if len(parts) == 2:
            # "Last, First" -> "First Last"
            variations.add(normalize_name(f"{parts[1]} {parts[0]}"))
            # Also try without comma
            variations.add(normalize_name(f"{parts[0]} {parts[1]}"))
    
    # Try without middle names/initials (first word + last word)
    words = normalized.split()
    if len(words) > 2:
        variations.add(f"{words[0]} {words[-1]}")
    
    return variations

conn = sqlite3.connect('malaysia_swimming.db')
cursor = conn.cursor()

# Get SEAG athletes without birthdates
cursor.execute("""
    SELECT DISTINCT a.id, a.name
    FROM athletes a
    JOIN results r ON a.id = r.athlete_id
    JOIN meets m ON r.meet_id = m.id
    WHERE (m.name LIKE '%Southeast Asian%' OR m.name LIKE '%SEAG%')
    AND a.birth_date IS NULL
    ORDER BY a.name
""")

seag_athletes = cursor.fetchall()

# Get all AthleteINFO records with birthdates
cursor.execute("""
    SELECT name, birthdate, gender
    FROM athleteinfo
    WHERE birthdate IS NOT NULL
    ORDER BY name
""")

athleteinfo_records = cursor.fetchall()

print("=" * 100)
print("SEAG Athletes Without Birthdates - Potential Matches")
print("=" * 100)
print(f"\nFound {len(seag_athletes)} SEAG athletes without birthdates")
print(f"Found {len(athleteinfo_records)} AthleteINFO records with birthdates\n")

for seag_id, seag_name in seag_athletes:
    print(f"\n{'='*100}")
    print(f"SEAG Athlete: {seag_name}")
    print("-" * 100)
    
    # Create variations of SEAG name
    seag_variations = create_name_variations(seag_name)
    
    # Find potential matches
    matches = []
    for ai_name, ai_birthdate, ai_gender in athleteinfo_records:
        ai_variations = create_name_variations(ai_name)
        
        # Check if any variations match
        best_similarity = 0
        for seag_var in seag_variations:
            for ai_var in ai_variations:
                similarity = name_similarity(seag_var, ai_var)
                if similarity > best_similarity:
                    best_similarity = similarity
        
        # If similarity is decent, include as potential match
        if best_similarity > 0.7:  # 70% similarity threshold
            matches.append((ai_name, ai_birthdate, ai_gender, best_similarity))
    
    # Sort matches by similarity (highest first)
    matches.sort(key=lambda x: x[3], reverse=True)
    
    if matches:
        print(f"  Potential matches (showing top 5):")
        for ai_name, ai_birthdate, ai_gender, similarity in matches[:5]:
            print(f"    {similarity*100:.1f}% match: {ai_name} | Birthdate: {ai_birthdate} | Gender: {ai_gender}")
    else:
        print(f"  No matches found above 70% similarity threshold")
        print(f"  Showing closest matches (top 3):")
        # Get closest matches even if below threshold
        all_similarities = []
        for ai_name, ai_birthdate, ai_gender in athleteinfo_records:
            ai_variations = create_name_variations(ai_name)
            best_similarity = 0
            for seag_var in seag_variations:
                for ai_var in ai_variations:
                    similarity = name_similarity(seag_var, ai_var)
                    if similarity > best_similarity:
                        best_similarity = similarity
            all_similarities.append((ai_name, ai_birthdate, ai_gender, best_similarity))
        all_similarities.sort(key=lambda x: x[3], reverse=True)
        for ai_name, ai_birthdate, ai_gender, similarity in all_similarities[:3]:
            print(f"    {similarity*100:.1f}% match: {ai_name} | Birthdate: {ai_birthdate} | Gender: {ai_gender}")

print(f"\n{'='*100}")
print("\nSummary:")
print(f"  SEAG athletes without birthdates: {len(seag_athletes)}")
print(f"\nReview the matches above to identify which AthleteINFO records correspond to each SEAG athlete.")

conn.close()


