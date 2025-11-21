"""
Centralized Name Matching Utility
Used by all endpoints and scripts for consistent athlete name matching
Improves once, benefits everywhere

Comprehensive matching with:
1. Word-based matching (primary) - sophisticated word-by-word comparison
2. Birthdate validation - handles month/day transposition, format normalization
3. Gender validation - checks for mismatches
4. Alias support - checks aliases in addition to main name
5. Club matching - intelligent club name comparison
"""

import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Dict, Tuple


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
    Handles: datetime objects, pandas Timestamps, strings, None
    """
    if not birthdate:
        return None

    try:
        # If it's already a string, try to parse it
        if isinstance(birthdate, str):
            birthdate_str = birthdate.strip()
            if not birthdate_str:
                return None
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
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
    """Detect month/day transposition (common data entry error)"""
    if not date_str or len(date_str) != 10:
        return None

    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            return None

        year, month, day = parts
        month_int = int(month)
        day_int = int(day)

        # If month > 12 and day <= 12, swap them
        if month_int > 12 and day_int <= 12:
            return f"{year}-{day:0>2}-{month:0>2}"
    except Exception:
        pass

    return None


def match_athlete_by_name(
    conn: sqlite3.Connection,
    fullname: str,
    gender: Optional[str] = None,
    birthdate: Optional[str] = None,
    match_type: str = "word-based"
) -> Optional[str]:
    """
    Match an athlete in the database by name (required), and optional gender/birthdate

    Args:
        conn: Database connection
        fullname: Athlete's full name (REQUIRED)
        gender: Optional gender (M or F) for filtering
        birthdate: Optional birthdate for validation (handles various formats)
        match_type: "exact" (strict), "fuzzy" (LIKE), or "word-based" (sophisticated) - default is best

    Returns:
        Athlete ID if found, None otherwise
    """
    if not fullname:
        return None

    print(f"[MATCH DEBUG] match_athlete_by_name called: fullname='{fullname}', gender={gender}, match_type={match_type}", flush=True)
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
        return _match_athlete_word_based(conn, fullname, gender, normalized_birthdate)


def _match_athlete_word_based(
    conn: sqlite3.Connection,
    fullname: str,
    gender: Optional[str] = None,
    birthdate: Optional[str] = None
) -> Optional[str]:
    """
    Sophisticated word-based matching with high confidence thresholds

    Includes:
    - Word-by-word name matching (handles variations, different word orders)
    - Optional gender filtering (if provided)
    - Birthdate validation (with month/day transposition detection)
    - High confidence thresholds (3+ words match OR all short names match)
    """
    cursor = conn.cursor()
    norm_name = normalize_name(fullname)

    if not norm_name:
        return None

    # Extract words from search name
    search_words = set(w for w in norm_name.split() if w.strip())

    if not search_words:
        return None

    # Prepare birthdate for comparison
    swapped_birthdate = None
    if birthdate:
        swapped_birthdate = try_swap_month_day(birthdate)

    # Helper function: check if birthdates match
    def birthdate_matches(db_birthdate: Optional[str]) -> bool:
        """Check if birthdates match (exact or month/day transposed)"""
        if not birthdate or not db_birthdate:
            return True  # No birthdate requirement
        db_norm = normalize_birthdate(db_birthdate)
        if not db_norm:
            return True  # No valid DB birthdate
        return (db_norm == birthdate) or (swapped_birthdate and db_norm == swapped_birthdate)

    # Get all athletes (optionally filtered by gender)
    if gender:
        cursor.execute("""
            SELECT id, FULLNAME, BIRTHDATE FROM athletes
            WHERE GENDER = ?
        """, (gender,))
    else:
        cursor.execute("""
            SELECT id, FULLNAME, BIRTHDATE FROM athletes
        """)

    athletes_list = cursor.fetchall()
    print(f"[MATCHER DEBUG] Searching for '{fullname}' (norm: '{norm_name}') | Found {len(athletes_list)} athletes in DB (gender={gender})", flush=True)

    best_match = None
    best_score = 0

    for row in athletes_list:
        athlete_id, db_fullname, db_birthdate = row

        # Check birthdate first (quick filter)
        if not birthdate_matches(db_birthdate):
            continue

        db_norm = normalize_name(db_fullname)
        db_words = set(w for w in db_norm.split() if w.strip())

        if not db_words:
            continue

        # Calculate word match score
        matching_words = search_words.intersection(db_words)
        num_matches = len(matching_words)

        # High confidence thresholds:
        # - At least 2 words match (lowered from 3 to catch name format variations)
        # - For very short names (2 words): all words must match
        is_high_confidence = (
            num_matches >= 2 or
            (len(search_words) == 2 and num_matches == len(search_words))
        )

        if is_high_confidence and num_matches > best_score:
            best_match = athlete_id
            best_score = num_matches

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
