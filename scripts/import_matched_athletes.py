"""
Import 612 matched athletes into the athletes table

Field mapping:
- Results file (authoritative): FULLNAME, BIRTHDATE, Gender, nation, club_name
- Registration file (supplemental): All other fields
- IC: Strip dashes, only load if exactly 12 digits
- Duplicate check: Fuzzy match against existing athletes
"""

import sqlite3
import pandas as pd
import re
from datetime import datetime

# File paths
MATCHES_FILE = r'C:\Users\megan\Downloads\POTENTIAL_MATCHES.xlsx'
ORIGINAL_FILE = r'C:\Users\megan\Downloads\REMAINING_UNMATCHED_RECORDS964_3815.xlsx'
DB_PATH = r'C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\malaysia_swimming.db'

def normalize_name(name):
    """Normalize name for matching"""
    if pd.isna(name) or not name:
        return ''
    return re.sub(r'[^a-z\s]', '', str(name).lower()).strip()

def get_name_words(name):
    """Extract words from name"""
    return set(w for w in normalize_name(name).split() if len(w) >= 2)

def levenshtein_distance(s1, s2):
    """Calculate edit distance"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def fuzzy_word_match(word1, word2, max_distance=1):
    """Check if two words are similar"""
    if word1 == word2:
        return True
    if len(word1) < 4 or len(word2) < 4:
        return False
    return levenshtein_distance(word1, word2) <= max_distance

def count_matching_words(words1, words2):
    """Count matches including fuzzy"""
    exact_matches = words1.intersection(words2)
    fuzzy_matches = set()
    unmatched1 = words1 - exact_matches
    unmatched2 = words2 - exact_matches
    for w1 in unmatched1:
        for w2 in unmatched2:
            if fuzzy_word_match(w1, w2):
                fuzzy_matches.add(w1)
                break
    return len(exact_matches) + len(fuzzy_matches)

def clean_ic(ic_value):
    """Strip dashes, return only if exactly 12 digits"""
    if pd.isna(ic_value) or not ic_value:
        return None
    # Remove all non-digits
    digits_only = re.sub(r'[^0-9]', '', str(ic_value))
    if len(digits_only) == 12:
        return digits_only
    return None

def birthdates_match(bday1, bday2):
    """Check if birthdates match (exact or month/day transposed)"""
    if not bday1 or not bday2:
        return False

    # Normalize both dates to YYYY-MM-DD
    def to_ymd(d):
        if pd.isna(d) or not d:
            return None
        try:
            if hasattr(d, 'strftime'):
                return d.strftime('%Y-%m-%d')
            s = str(d).strip()[:10]
            for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y.%m.%d', '%m/%d/%Y']:
                try:
                    return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
                except:
                    continue
        except:
            pass
        return None

    d1 = to_ymd(bday1)
    d2 = to_ymd(bday2)

    if not d1 or not d2:
        return False

    # Exact match
    if d1 == d2:
        return True

    # Try transposing month/day on d1
    try:
        parts1 = d1.split('-')
        if len(parts1) == 3:
            year, month, day = parts1
            # Only transpose if both values are valid as month (<=12)
            if int(month) <= 12 and int(day) <= 12:
                transposed1 = f"{year}-{day}-{month}"
                if transposed1 == d2:
                    return True
    except:
        pass

    # Try transposing month/day on d2
    try:
        parts2 = d2.split('-')
        if len(parts2) == 3:
            year, month, day = parts2
            if int(month) <= 12 and int(day) <= 12:
                transposed2 = f"{year}-{day}-{month}"
                if transposed2 == d1:
                    return True
    except:
        pass

    return False

def normalize_date(date_val):
    """Normalize date to ISO format"""
    if pd.isna(date_val) or not date_val:
        return None
    try:
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y-%m-%dT00:00:00Z')
        date_str = str(date_val).strip()
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y.%m.%d']:
            try:
                dt = datetime.strptime(date_str[:10], fmt)
                return dt.strftime('%Y-%m-%dT00:00:00Z')
            except:
                continue
    except:
        pass
    return None

def get_str(val):
    """Get string value or None"""
    if pd.isna(val) or not val:
        return None
    s = str(val).strip()
    return s if s else None

def main():
    print("=" * 60)
    print("IMPORTING MATCHED ATHLETES TO DATABASE")
    print("=" * 60)

    # Load matches
    print("\nLoading matches file...")
    matches_df = pd.read_excel(MATCHES_FILE, sheet_name='Potential Matches')
    print(f"  Found {len(matches_df)} matches to import")

    # Load original file for full registration data
    print("\nLoading original file for full registration data...")
    original_df = pd.read_excel(ORIGINAL_FILE)
    regs = original_df[original_df['_match_category'] == 'leftover_registration'].copy()
    print(f"  Found {len(regs)} registration records")

    # Build registration lookup by first+last name + birthday
    print("\nBuilding registration lookup...")
    reg_lookup = {}
    for idx, row in regs.iterrows():
        first = get_str(row.get('reg_Memb. First Name')) or ''
        last = get_str(row.get('reg_Memb. Last Name')) or ''
        bday = get_str(row.get('reg_Birthday')) or ''
        key = f"{first.lower()}|{last.lower()}|{bday}"
        reg_lookup[key] = row
    print(f"  Built lookup with {len(reg_lookup)} keys")

    # Connect to database
    print("\nConnecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current max ID
    cursor.execute("SELECT MAX(CAST(id AS INTEGER)) FROM athletes")
    max_id = cursor.fetchone()[0] or 0
    print(f"  Current max athlete ID: {max_id}")

    # Load existing athletes for duplicate check
    print("\nLoading existing athletes for duplicate check...")
    cursor.execute("SELECT id, FULLNAME, BIRTHDATE, Gender FROM athletes")
    existing_athletes = cursor.fetchall()
    print(f"  Loaded {len(existing_athletes)} existing athletes")

    # Build existing athlete index
    existing_index = {}
    for athlete in existing_athletes:
        aid, fullname, bday, gender = athlete
        words = get_name_words(fullname or '')
        for word in words:
            if word not in existing_index:
                existing_index[word] = []
            existing_index[word].append((aid, fullname, bday, gender))

    # Process matches
    print("\n" + "=" * 60)
    print("PROCESSING MATCHES")
    print("=" * 60)

    imported = 0
    skipped_duplicate = 0
    skipped_no_reg = 0
    errors = 0

    for idx, match in matches_df.iterrows():
        # Results data (authoritative)
        result_fullname = get_str(match.get('result_name'))
        result_bday = match.get('result_bday')
        result_gender = get_str(match.get('result_gender'))
        result_club = get_str(match.get('result_club'))
        result_nation = get_str(match.get('result_nation'))

        # Registration lookup key
        reg_first = get_str(match.get('reg_first')) or ''
        reg_last = get_str(match.get('reg_last')) or ''
        reg_bday_str = get_str(match.get('reg_bday')) or ''
        reg_key = f"{reg_first.lower()}|{reg_last.lower()}|{reg_bday_str}"

        # Try alternate key formats
        reg_row = reg_lookup.get(reg_key)
        if reg_row is None:
            # Try with different date format
            for key, row in reg_lookup.items():
                parts = key.split('|')
                if len(parts) == 3:
                    if parts[0] == reg_first.lower() and parts[1] == reg_last.lower():
                        reg_row = row
                        break

        if reg_row is None:
            skipped_no_reg += 1
            if skipped_no_reg <= 5:
                print(f"  [SKIP] No reg data found for: {result_fullname}")
            continue

        # Check for duplicates in existing athletes
        # REQUIRE: 2+ name words match AND birthdate match (exact or transposed) AND same gender
        result_words = get_name_words(result_fullname or '')
        is_duplicate = False
        duplicate_reason = ""

        for word in result_words:
            if word in existing_index:
                for existing in existing_index[word]:
                    existing_id, existing_name, existing_bday, existing_gender = existing
                    existing_words = get_name_words(existing_name or '')
                    match_count = count_matching_words(result_words, existing_words)

                    # Must have 2+ word matches
                    if match_count < 2:
                        continue

                    # Must have same gender
                    if not (result_gender and existing_gender and result_gender.upper() == existing_gender.upper()):
                        continue

                    # Must have birthdate match (exact or transposed)
                    if birthdates_match(result_bday, existing_bday):
                        is_duplicate = True
                        duplicate_reason = f"name:{match_count}words + bday match"
                        if skipped_duplicate < 10:
                            print(f"  [DUP] {result_fullname} ({result_bday}) matches: {existing_name} ({existing_bday}) ID:{existing_id} - {duplicate_reason}")
                        break
                if is_duplicate:
                    break

        if is_duplicate:
            skipped_duplicate += 1
            continue

        # Prepare insert data
        max_id += 1
        new_id = str(max_id)

        # IC validation
        ic_raw = reg_row.get('reg_Malaysian IC/or Passport Number (For non-Malaysians only)')
        ic_clean = clean_ic(ic_raw)

        acct_ic_raw = reg_row.get('reg_Malaysian IC/or Passport Number (For non-Malaysians only).1')
        acct_ic_clean = clean_ic(acct_ic_raw)

        # Normalize birthdate
        birthdate_normalized = normalize_date(result_bday)

        try:
            cursor.execute("""
                INSERT INTO athletes (
                    id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX,
                    IC, nation, MembEmail, PreferredName, Phone,
                    AcctFirstName, AcctLastName, AcctMiddleInitial,
                    Address, Address2, City,
                    EmergencyContact, EmergencyPhone,
                    Guardian1FirstName, Guardian1HomePhone, Guardian1LastName,
                    Guardian1MobilePhone, Guardian1WorkPhone,
                    Guardian2FirstName, Guardian2HomePhone, Guardian2LastName,
                    Guardian2MobilePhone, Guardian2WorkPhone,
                    AcctIC, Gender, club_name, state_code
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?
                )
            """, (
                new_id,
                result_fullname,  # FULLNAME from results
                birthdate_normalized,  # BIRTHDATE from results
                get_str(reg_row.get('reg_Memb. First Name')),
                get_str(reg_row.get('reg_Memb. Last Name')),
                get_str(reg_row.get('reg_Memb. Middle Initial')),
                get_str(reg_row.get('reg_Memb. Suffix')),
                ic_clean,  # IC - cleaned, 12 digits only
                result_nation,  # nation from results
                get_str(reg_row.get('reg_Memb. Email')),
                get_str(reg_row.get('reg_Preferred Name')),
                get_str(reg_row.get('reg_Phone')),
                get_str(reg_row.get('reg_Acct. First Name')),
                get_str(reg_row.get('reg_Acct. Last Name')),
                get_str(reg_row.get('reg_Acct. Middle Initial')),
                get_str(reg_row.get('reg_Address')),
                get_str(reg_row.get('reg_Address 2')),
                get_str(reg_row.get('reg_City')),
                get_str(reg_row.get('reg_Emergency Contact')),
                get_str(reg_row.get('reg_Emergency Phone')),
                get_str(reg_row.get('reg_Guardian 1 First Name')),
                get_str(reg_row.get('reg_Guardian 1 Home Phone')),
                get_str(reg_row.get('reg_Guardian 1 Last Name')),
                get_str(reg_row.get('reg_Guardian 1 Mobile Phone')),
                get_str(reg_row.get('reg_Guardian 1 Work Phone')),
                get_str(reg_row.get('reg_Guardian 2 First Name')),
                get_str(reg_row.get('reg_Guardian 2 Home Phone')),
                get_str(reg_row.get('reg_Guardian 2 Last Name')),
                get_str(reg_row.get('reg_Guardian 2 Mobile Phone')),
                get_str(reg_row.get('reg_Guardian 2 Work Phone')),
                acct_ic_clean,  # AcctIC - cleaned, 12 digits only
                result_gender,  # Gender from results
                result_club,  # club_name from results
                get_str(reg_row.get('reg_Location')),  # state_code
            ))

            imported += 1
            if imported <= 10 or imported % 100 == 0:
                print(f"  [OK] #{imported}: {result_fullname} (ID: {new_id})")

        except Exception as e:
            errors += 1
            print(f"  [ERROR] {result_fullname}: {str(e)}")

    # Commit
    print("\n" + "=" * 60)
    print("COMMITTING TO DATABASE")
    print("=" * 60)
    conn.commit()

    # Final counts
    cursor.execute("SELECT COUNT(*) FROM athletes")
    final_count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"  Imported: {imported}")
    print(f"  Skipped (duplicate): {skipped_duplicate}")
    print(f"  Skipped (no reg data): {skipped_no_reg}")
    print(f"  Errors: {errors}")
    print(f"  Total athletes now: {final_count}")
    print("=" * 60)

if __name__ == '__main__':
    main()
