"""
Centralized Name Matching Utility
Used by all endpoints and scripts for consistent athlete name matching
Improves once, benefits everywhere

Comprehensive matching with:
1. Word-based matching (primary) - sophisticated word-by-word comparison
2. Spelling variations - MUHD=Muhammad, etc.
3. Nickname mappings - Nick=Nicholas, etc.
4. Birthdate validation - handles month/day transposition, format normalization
5. Gender validation - checks for mismatches
6. Alias support - checks aliases in addition to main name
7. Club matching - intelligent club name comparison
"""

import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Set, Any


# ============================================================
# COMMON NAMES - Low identifier value in Malaysian naming
# These words appear frequently and don't uniquely identify a person
# Matching on these alone should NOT confirm identity
# ============================================================
COMMON_NAMES = {
    # Muhammad variants (extremely common)
    'muhammad', 'muhd', 'mohd', 'mohamad', 'mohamed', 'mohammad', 'mohammed', 'muhamad', 'md',

    # Patronymic connectors
    'bin', 'binti', 'b', 'bt', 'ibn',

    # Abdul variants
    'abdul', 'abd',

    # Common prefixes
    'nur', 'noor', 'nurul', 'siti', 'wan', 'nik', 'che', 'tengku', 'raja',

    # Ahmad variants
    'ahmad', 'ahmed',

    # Common Malay names
    'ali', 'hassan', 'hussein', 'ibrahim', 'ismail', 'omar', 'osman', 'yusof', 'yusuf',
    'fatimah', 'aishah', 'khadijah', 'zainab', 'aminah',

    # Common Chinese surnames (very common, low identifier value alone)
    'tan', 'lee', 'lim', 'ng', 'wong', 'chen', 'ong', 'goh', 'chua', 'teh', 'koh', 'yap', 'ooi',
    'chan', 'chong', 'low', 'tay', 'sim', 'ho', 'lai', 'ang', 'loh', 'yong', 'khoo', 'teo',

    # Common Indian name elements
    'kumar', 'singh', 'kaur', 'devi', 'raj', 'ram', 'lal',

    # Titles/honorifics that sometimes appear in names
    'haji', 'hajjah', 'dato', 'datin', 'tun', 'tan', 'sri',
}

# Weight for common names (lower = less important for matching)
COMMON_NAME_WEIGHT = 0.3
IDENTIFIER_NAME_WEIGHT = 1.0

# ============================================================
# SPELLING VARIATIONS - Common Malaysian name variants
# All variations map to a canonical form for matching
# ============================================================
SPELLING_VARIATIONS = {
    # Muhammad variants (very common in Malaysia)
    'muhd': 'muhammad',
    'mohd': 'muhammad',
    'mohamad': 'muhammad',
    'mohamed': 'muhammad',
    'mohammad': 'muhammad',
    'mohammed': 'muhammad',
    'muhamad': 'muhammad',
    'muhammad': 'muhammad',
    'md': 'muhammad',

    # Abdul variants
    'abd': 'abdul',
    'abdul': 'abdul',

    # Bin/Binti variants
    'b': 'bin',
    'bin': 'bin',
    'binti': 'binti',
    'bt': 'binti',

    # Nur variants
    'nur': 'nur',
    'noor': 'nur',
    'nurul': 'nurul',

    # Ahmad variants
    'ahmad': 'ahmad',
    'ahmed': 'ahmad',

    # Common Malay name variants
    'nik': 'nik',
    'wan': 'wan',
    'che': 'che',

    # Chinese name romanization variants
    'lee': 'lee',
    'li': 'lee',
    'tan': 'tan',
    'chen': 'tan',  # Sometimes romanized differently
    'ng': 'ng',
    'huang': 'ng',  # Hokkien vs Mandarin
    'ong': 'ong',
    'wang': 'ong',  # Hokkien vs Mandarin
    'lim': 'lim',
    'lin': 'lim',
    'wong': 'wong',
    'wang': 'wong',
    'chong': 'chong',
    'zhang': 'chong',
    'chua': 'chua',
    'cai': 'chua',
    'goh': 'goh',
    'wu': 'goh',
    'teh': 'teh',
    'zheng': 'teh',
    'koh': 'koh',
    'xu': 'koh',
    'yap': 'yap',
    'ye': 'yap',
    'ooi': 'ooi',
    'huang': 'ooi',
}

# ============================================================
# NICKNAME MAPPINGS - Common nicknames to full names
# Bidirectional: Nick matches Nicholas, Nicholas matches Nick
# ============================================================
NICKNAME_MAPPINGS = {
    # Common English nicknames
    'nick': ['nicholas', 'nick'],
    'nicholas': ['nicholas', 'nick'],
    'mike': ['michael', 'mike'],
    'michael': ['michael', 'mike'],
    'chris': ['christopher', 'christian', 'chris'],
    'christopher': ['christopher', 'chris'],
    'christian': ['christian', 'chris'],
    'dan': ['daniel', 'dan'],
    'daniel': ['daniel', 'dan'],
    'dave': ['david', 'dave'],
    'david': ['david', 'dave'],
    'tom': ['thomas', 'tom'],
    'thomas': ['thomas', 'tom'],
    'tim': ['timothy', 'tim'],
    'timothy': ['timothy', 'tim'],
    'jim': ['james', 'jim', 'jimmy'],
    'james': ['james', 'jim', 'jimmy'],
    'jimmy': ['james', 'jim', 'jimmy'],
    'joe': ['joseph', 'joe'],
    'joseph': ['joseph', 'joe'],
    'bob': ['robert', 'bob'],
    'robert': ['robert', 'bob'],
    'bill': ['william', 'bill'],
    'william': ['william', 'bill'],
    'alex': ['alexander', 'alexandra', 'alex'],
    'alexander': ['alexander', 'alex'],
    'alexandra': ['alexandra', 'alex'],
    'sam': ['samuel', 'samantha', 'sam'],
    'samuel': ['samuel', 'sam'],
    'samantha': ['samantha', 'sam'],
    'ben': ['benjamin', 'ben'],
    'benjamin': ['benjamin', 'ben'],
    'matt': ['matthew', 'matt'],
    'matthew': ['matthew', 'matt'],
    'josh': ['joshua', 'josh'],
    'joshua': ['joshua', 'josh'],
    'jon': ['jonathan', 'jon'],
    'jonathan': ['jonathan', 'jon'],
    'jeff': ['jeffrey', 'jeff'],
    'jeffrey': ['jeffrey', 'jeff'],
    'steve': ['steven', 'stephen', 'steve'],
    'steven': ['steven', 'steve'],
    'stephen': ['stephen', 'steve'],
    'andy': ['andrew', 'andy'],
    'andrew': ['andrew', 'andy'],
    'tony': ['anthony', 'tony'],
    'anthony': ['anthony', 'tony'],
    'ed': ['edward', 'ed', 'eddie'],
    'edward': ['edward', 'ed', 'eddie'],
    'eddie': ['edward', 'ed', 'eddie'],
    'charlie': ['charles', 'charlie'],
    'charles': ['charles', 'charlie'],
    'max': ['maximilian', 'maxwell', 'max'],
    'maximilian': ['maximilian', 'max'],
    'maxwell': ['maxwell', 'max'],
    'will': ['william', 'will'],
    'rick': ['richard', 'rick'],
    'richard': ['richard', 'rick'],
    'greg': ['gregory', 'greg'],
    'gregory': ['gregory', 'greg'],

    # Common female nicknames
    'kate': ['katherine', 'catherine', 'kate', 'katie'],
    'katherine': ['katherine', 'kate', 'katie'],
    'catherine': ['catherine', 'kate', 'katie'],
    'katie': ['katherine', 'catherine', 'kate', 'katie'],
    'liz': ['elizabeth', 'liz', 'lizzy', 'beth'],
    'elizabeth': ['elizabeth', 'liz', 'lizzy', 'beth'],
    'beth': ['elizabeth', 'beth'],
    'jen': ['jennifer', 'jen', 'jenny'],
    'jennifer': ['jennifer', 'jen', 'jenny'],
    'jenny': ['jennifer', 'jen', 'jenny'],
    'meg': ['megan', 'margaret', 'meg'],
    'megan': ['megan', 'meg'],
    'margaret': ['margaret', 'meg'],
    'sara': ['sarah', 'sara'],
    'sarah': ['sarah', 'sara'],
    'mandy': ['amanda', 'mandy'],
    'amanda': ['amanda', 'mandy'],
    'vicky': ['victoria', 'vicky'],
    'victoria': ['victoria', 'vicky'],
    'becky': ['rebecca', 'becky'],
    'rebecca': ['rebecca', 'becky'],
    'abby': ['abigail', 'abby'],
    'abigail': ['abigail', 'abby'],
}


def expand_word_variants(word: str) -> Set[str]:
    """
    Expand a word to include all its spelling variants and nicknames.
    Returns a set of all equivalent words for matching.
    """
    word_lower = word.lower()
    variants = {word_lower}

    # Add spelling variations
    if word_lower in SPELLING_VARIATIONS:
        canonical = SPELLING_VARIATIONS[word_lower]
        variants.add(canonical)
        # Add all words that map to the same canonical form
        for variant, canon in SPELLING_VARIATIONS.items():
            if canon == canonical:
                variants.add(variant)

    # Add nickname mappings
    if word_lower in NICKNAME_MAPPINGS:
        variants.update(NICKNAME_MAPPINGS[word_lower])

    return variants


def is_common_name(word: str) -> bool:
    """
    Check if a word is a common/low-identifier-value name.
    Common names like Muhammad, Bin, Tan contribute less to matching confidence.
    """
    word_lower = word.lower()

    # Check if word itself is common
    if word_lower in COMMON_NAMES:
        return True

    # Check if any variant of this word is common
    variants = expand_word_variants(word_lower)
    return bool(variants.intersection(COMMON_NAMES))


# ============================================================
# CORE SEARCH FUNCTION - Used by both admin panel and imports
# Single source of truth for name-based athlete search
# ============================================================

def search_athletes_by_name(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 50,
    include_aliases: bool = True
) -> List[Dict]:
    """
    Core athlete search function - single source of truth for name matching.

    Used by:
    - Admin panel athlete search (direct results for user selection)
    - Global name matcher (candidate retrieval before scoring)

    Features:
    - Word splitting (handles commas, multiple spaces)
    - Spelling variation expansion (muhd->muhammad, li->lee, etc.)
    - Nickname expansion (steve->steven/stephen, mike->michael, etc.)
    - Alias searching (athlete_alias_1, athlete_alias_2)
    - Case-insensitive matching

    Args:
        conn: Database connection
        query: Search query string
        limit: Maximum results to return (default 50)
        include_aliases: Whether to search alias fields (default True)

    Returns:
        List of athlete dicts with keys:
        id, name, gender, birth_date, club_name, club_code, nation, state_code,
        athlete_alias_1, athlete_alias_2
    """
    query = (query or "").strip()
    if not query:
        return []

    # Split query into words (remove commas, handle multiple spaces)
    words = re.split(r'[,\s]+', query.upper())
    words = [w for w in words if w]

    if not words:
        return []

    # Build WHERE clause - each word must match in at least one field
    # Each word is expanded to include all spelling variants and nicknames
    where_clauses = []
    params = []

    for word in words:
        # Expand word to all variants
        variants = expand_word_variants(word)

        # Build OR clause for all variants of this word
        variant_clauses = []
        for variant in variants:
            variant_upper = variant.upper()
            if include_aliases:
                variant_clauses.append(
                    "(UPPER(FULLNAME) LIKE ? OR UPPER(COALESCE(athlete_alias_1, '')) LIKE ? OR UPPER(COALESCE(athlete_alias_2, '')) LIKE ?)"
                )
                params.extend([f"%{variant_upper}%", f"%{variant_upper}%", f"%{variant_upper}%"])
            else:
                variant_clauses.append("UPPER(FULLNAME) LIKE ?")
                params.append(f"%{variant_upper}%")

        # All variants for this word joined with OR
        where_clauses.append("(" + " OR ".join(variant_clauses) + ")")

    # All words must match (AND)
    where_sql = " AND ".join(where_clauses)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, FULLNAME, Gender, BIRTHDATE, club_name, club_code, nation, state_code,
               athlete_alias_1, athlete_alias_2
        FROM athletes
        WHERE {where_sql}
        ORDER BY FULLNAME
        LIMIT ?
        """,
        params + [limit]
    )

    rows = cursor.fetchall()
    athletes = []
    for row in rows:
        athletes.append({
            "id": row[0],
            "name": row[1] or "",
            "gender": row[2] or "",
            "birth_date": row[3] or None,
            "club_name": row[4] or None,
            "club_code": row[5] or None,
            "nation": row[6] or None,
            "state_code": row[7] or None,
            "athlete_alias_1": row[8] or None,
            "athlete_alias_2": row[9] or None,
        })

    return athletes


def get_word_weight(word: str) -> float:
    """
    Get the matching weight for a word.
    Common names get lower weight, identifier names get full weight.
    """
    if is_common_name(word):
        return COMMON_NAME_WEIGHT
    return IDENTIFIER_NAME_WEIGHT


def normalize_name(name: str) -> str:
    """Normalize name for matching: lowercase, remove punctuation, extra spaces"""
    if not name:
        return ""
    # Remove punctuation except spaces, lowercase, collapse spaces
    normalized = re.sub(r"[^\w\s]", " ", str(name)).lower()
    normalized = " ".join(normalized.split())
    return normalized


def normalize_birthdate(birthdate) -> Optional[str]:
    """
    Normalize birthdate to YYYY-MM-DD format
    Handles: datetime objects, pandas Timestamps, strings (various formats), None
    """
    if not birthdate:
        return None

    try:
        # If it's already a string, try to parse it
        if isinstance(birthdate, str):
            birthdate_str = birthdate.strip()
            if not birthdate_str or birthdate_str == '(blank)':
                return None

            # Handle ISO format with T and Z (e.g., 2014-08-19T00:00:00Z)
            if 'T' in birthdate_str:
                birthdate_str = birthdate_str.split('T')[0]

            # Handle space-separated datetime (e.g., 2010-07-08 00:00:00)
            if ' ' in birthdate_str:
                birthdate_str = birthdate_str.split(' ')[0]

            # Handle dot-separated format (e.g., 2008.10.09)
            if '.' in birthdate_str:
                birthdate_str = birthdate_str.replace('.', '-')

            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y']:
                try:
                    dt = datetime.strptime(birthdate_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        else:
            # Handle datetime objects and pandas Timestamps
            if hasattr(birthdate, 'strftime'):
                return birthdate.strftime('%Y-%m-%d')
            elif hasattr(birthdate, 'date'):
                return birthdate.date().strftime('%Y-%m-%d')
    except Exception:
        pass

    return None


def try_swap_month_day(date_str: str) -> Optional[str]:
    """
    Create alternate date by swapping month and day.
    Use this to check if a date might have month/day transposed during data entry.

    Returns the swapped date if:
    - Both month and day are valid after swap (both <= 12 and day <= 31)
    - The swapped date is different from the original
    """
    if not date_str or len(date_str) != 10:
        return None

    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            return None

        year, month, day = parts
        month_int = int(month)
        day_int = int(day)

        # Only swap if:
        # - The day value is valid as a month (1-12)
        # - The month value is valid as a day (1-31)
        # - They're different (otherwise no point swapping)
        if day_int <= 12 and month_int <= 31 and month_int != day_int:
            return f"{year}-{day:0>2}-{month:0>2}"
    except Exception:
        pass

    return None


def preload_athletes_for_matching(conn: sqlite3.Connection) -> List[Tuple]:
    """
    Preload all athletes for batch matching.
    Call this ONCE, then pass the result to match_athlete_by_name() for each row.

    Returns:
        List of tuples: (id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX, PreferredName, alias_1, alias_2, Gender)
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX, PreferredName, athlete_alias_1, athlete_alias_2, Gender
        FROM athletes
    """)
    return cursor.fetchall()


def match_athlete_by_name(
    conn: sqlite3.Connection,
    fullname: str,
    gender: Optional[str] = None,
    birthdate: Optional[str] = None,
    match_type: str = "word-based",
    preloaded_athletes: Optional[List[Tuple]] = None
) -> Optional[str]:
    """
    Match an athlete in the database by name (required), and optional gender/birthdate

    Args:
        conn: Database connection
        fullname: Athlete's full name (REQUIRED)
        gender: Optional gender (M or F) for filtering
        birthdate: Optional birthdate for validation (handles various formats)
        match_type: "exact" (strict), "fuzzy" (LIKE), or "word-based" (sophisticated) - default is best
        preloaded_athletes: Optional preloaded athlete list for BATCH processing
            Use preload_athletes_for_matching(conn) to get this list

    Returns:
        Athlete ID if found, None otherwise
    """
    if not fullname:
        return None

    cursor = conn.cursor()
    fullname_upper = fullname.upper().strip()

    # Normalize birthdate if provided
    normalized_birthdate = normalize_birthdate(birthdate) if birthdate else None

    if match_type == "exact":
        # Exact match - must match completely
        if gender:
            cursor.execute("""
                SELECT id FROM athletes
                WHERE UPPER(TRIM(FULLNAME)) = ?
                AND GENDER = ?
                LIMIT 1
            """, (fullname_upper, gender))
        else:
            cursor.execute("""
                SELECT id FROM athletes
                WHERE UPPER(TRIM(FULLNAME)) = ?
                LIMIT 1
            """, (fullname_upper,))
        row = cursor.fetchone()
        return row[0] if row else None

    elif match_type == "fuzzy":
        # Fuzzy match - partial/LIKE match
        if gender:
            cursor.execute("""
                SELECT id FROM athletes
                WHERE UPPER(FULLNAME) LIKE ?
                AND GENDER = ?
                LIMIT 1
            """, (f"%{fullname_upper}%", gender))
        else:
            cursor.execute("""
                SELECT id FROM athletes
                WHERE UPPER(FULLNAME) LIKE ?
                LIMIT 1
            """, (f"%{fullname_upper}%",))
        row = cursor.fetchone()
        return row[0] if row else None

    else:  # word-based (default, most sophisticated)
        # Word-based matching: extract words, find high-confidence matches
        return _match_athlete_word_based(conn, fullname, gender, normalized_birthdate, preloaded_athletes)


def _match_athlete_word_based(
    conn: sqlite3.Connection,
    fullname: str,
    gender: Optional[str] = None,
    birthdate: Optional[str] = None,
    preloaded_athletes: Optional[List[Tuple]] = None
) -> Optional[str]:
    """
    Sophisticated word-based matching with weighted scoring for common vs identifier names.

    Key features:
    - Word-by-word name matching (handles variations, different word orders)
    - Spelling variations (MUHD=Muhammad, MOHD=Muhammad, etc.)
    - Nickname mappings (Nick=Nicholas, etc.)
    - WEIGHTED SCORING: Common names (Muhammad, Bin, Tan) = 0.3 points, Identifier names = 1.0 points
    - REQUIRES at least 1 identifier (non-common) word to match
    - STRICT birthdate matching: if both have birthdates and they don't match, reject
    - Optional gender filtering (if provided)
    - BATCH MODE: If preloaded_athletes is provided, uses that instead of querying DB

    Args:
        preloaded_athletes: Optional list of tuples with same structure as DB query:
            (id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX, PreferredName, alias_1, alias_2, Gender)
            If provided, skips DB query for BATCH processing
    """
    norm_name = normalize_name(fullname)

    if not norm_name:
        return None

    # Extract words from search name
    search_words_raw = [w for w in norm_name.split() if w.strip()]

    if not search_words_raw:
        return None

    # Expand search words with all variants (spelling + nicknames)
    search_words_expanded = set()
    for word in search_words_raw:
        search_words_expanded.update(expand_word_variants(word))

    # Prepare birthdate for comparison
    swapped_birthdate = None
    if birthdate:
        swapped_birthdate = try_swap_month_day(birthdate)

    # Helper function: STRICT birthdate matching
    def birthdate_matches(db_birthdate: Optional[str]) -> Tuple[bool, bool]:
        """
        Check if birthdates match.
        Returns (matches, both_have_birthdate)
        - If both have birthdates and don't match: (False, True) → REJECT
        - If both have birthdates and match: (True, True) → STRONG MATCH
        - If either missing birthdate: (True, False) → OK but no bonus
        """
        if not birthdate or not db_birthdate:
            return (True, False)  # Missing birthdate, allow match but no bonus

        db_norm = normalize_birthdate(db_birthdate)
        if not db_norm:
            return (True, False)  # Invalid DB birthdate, allow match

        matches = (db_norm == birthdate) or (swapped_birthdate and db_norm == swapped_birthdate)
        return (matches, True)

    # Get all athletes - use preloaded if available (BATCH MODE), otherwise query DB
    if preloaded_athletes is not None:
        # BATCH MODE: Use preloaded data (much faster for processing many rows)
        # Filter by gender if specified
        if gender:
            athletes_list = [a for a in preloaded_athletes if len(a) > 10 and a[10] == gender]
        else:
            athletes_list = preloaded_athletes
    else:
        # DB MODE: Query database (slower, but works without preloading)
        cursor = conn.cursor()
        if gender:
            cursor.execute("""
                SELECT id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX, PreferredName, athlete_alias_1, athlete_alias_2, Gender
                FROM athletes
                WHERE Gender = ?
            """, (gender,))
        else:
            cursor.execute("""
                SELECT id, FULLNAME, BIRTHDATE, FIRSTNAME, LASTNAME, MIDDLEINITIAL, SUFFIX, PreferredName, athlete_alias_1, athlete_alias_2, Gender
                FROM athletes
            """)
        athletes_list = cursor.fetchall()

    best_match = None
    best_score = 0

    for row in athletes_list:
        athlete_id = row[0]
        db_fullname = row[1]
        db_birthdate = row[2]
        db_firstname = row[3]
        db_lastname = row[4]
        db_middlename = row[5]
        db_suffix = row[6]
        db_preferred_name = row[7]
        db_alias_1 = row[8]
        db_alias_2 = row[9]

        # STRICT birthdate check: if both have birthdates and don't match, SKIP
        bday_matches, both_have_bday = birthdate_matches(db_birthdate)
        if not bday_matches:
            continue  # Birthdates don't match - definitely not the same person

        # Build comprehensive word set from all name fields
        all_name_fields = [
            db_fullname,
            db_firstname,
            db_lastname,
            db_middlename,
            db_suffix,
            db_preferred_name,
            db_alias_1,
            db_alias_2
        ]

        db_words_raw = []
        db_words_expanded = set()

        for field in all_name_fields:
            if field:
                field_norm = normalize_name(field)
                field_words = [w for w in field_norm.split() if w.strip()]
                for word in field_words:
                    db_words_raw.append(word)
                    db_words_expanded.update(expand_word_variants(word))

        if not db_words_expanded:
            continue

        # Calculate WEIGHTED score
        # Common names = 0.3 points, Identifier names = 1.0 points
        weighted_score = 0.0
        identifier_matches = 0  # Count of non-common words that matched
        common_matches = 0  # Count of common words that matched

        for word in search_words_raw:
            word_variants = expand_word_variants(word)
            if word_variants.intersection(db_words_expanded):
                # This word matched
                weight = get_word_weight(word)
                weighted_score += weight

                if is_common_name(word):
                    common_matches += 1
                else:
                    identifier_matches += 1

        # CRITICAL: Require at least 1 identifier (non-common) word to match
        # This prevents "Muhammad Bin" matching every "Muhammad Bin X"
        if identifier_matches == 0:
            continue  # No unique identifier matched, skip

        # Bonus for matching birthdates (strong confirmation)
        if both_have_bday and bday_matches:
            weighted_score += 2.0  # Significant bonus for birthdate match

        # High confidence thresholds:
        # - At least 1 identifier word + 1 other word (common or identifier)
        # - OR birthdate matches + at least 2 words total
        # - OR single-word search with identifier (not common) + exact birthdate
        #   e.g., "NEELKANTHA, ." matches "ARJOO SEGAR, Neelkantha" if birthdates match
        #   but "LEE, ." would NOT match because LEE is a common name
        total_matches = identifier_matches + common_matches
        is_single_word_identifier_search = (len(search_words_raw) == 1 and identifier_matches >= 1)
        is_high_confidence = (
            (identifier_matches >= 1 and total_matches >= 2) or
            (both_have_bday and total_matches >= 2) or
            (both_have_bday and is_single_word_identifier_search)
        )

        if is_high_confidence and weighted_score > best_score:
            best_match = athlete_id
            best_score = weighted_score

    return best_match


def search_athlete_by_name_with_suggestions(
    conn: sqlite3.Connection,
    fullname: str,
    gender: str
) -> Dict:
    """
    Search for an athlete and return match info plus suggestions

    Args:
        conn: Database connection
        fullname: Athlete's full name
        gender: Gender (M or F)

    Returns:
        Dict with keys:
        - matched: bool (found exact match)
        - athlete_id: str or None
        - suggestions: list of possible matches for manual review
    """
    cursor = conn.cursor()
    fullname_upper = fullname.upper().strip()

    result = {
        "matched": False,
        "athlete_id": None,
        "suggestions": []
    }

    # Try exact match first
    athlete_id = match_athlete_by_name(conn, fullname, gender, match_type="exact")
    if athlete_id:
        result["matched"] = True
        result["athlete_id"] = athlete_id
        return result

    # Try fuzzy match
    athlete_id = match_athlete_by_name(conn, fullname, gender, match_type="fuzzy")
    if athlete_id:
        result["matched"] = True
        result["athlete_id"] = athlete_id
        return result

    # No match found - provide suggestions by searching name parts
    name_parts = [p.strip() for p in fullname.split() if p.strip()]

    for part in name_parts:
        if len(part) < 2:  # Skip single letters
            continue

        cursor.execute("""
            SELECT id, FULLNAME FROM athletes
            WHERE UPPER(FULLNAME) LIKE ?
            AND GENDER = ?
            LIMIT 5
        """, (f"%{part.upper()}%", gender))

        for row in cursor.fetchall():
            suggestion = {
                "athlete_id": row[0],
                "fullname": row[1],
                "match_reason": f"Contains name part: '{part}'"
            }
            # Avoid duplicates
            if not any(s["athlete_id"] == suggestion["athlete_id"] for s in result["suggestions"]):
                result["suggestions"].append(suggestion)

    return result


# Backward compatibility - function name as per usage
def get_athlete_id_by_name(
    conn: sqlite3.Connection,
    fullname: str,
    gender: str
) -> Optional[str]:
    """
    Backward compatible function name
    Matches the interface used in test_seag_athlete_matching.py
    """
    return match_athlete_by_name(conn, fullname, gender, match_type="fuzzy")
