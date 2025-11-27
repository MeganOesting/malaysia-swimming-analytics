"""
Foreign Athlete Detection Utility

GLOBAL SOURCE OF TRUTH for determining if an unmatched athlete is likely foreign.
All scripts should import from here - DO NOT rewrite this logic elsewhere.

Usage:
    from src.web.utils.foreign_detection import is_likely_foreign, FOREIGN_INDICATORS, INTERNATIONAL_SCHOOL_PATTERNS
"""

from typing import Optional

# Core indicators that suggest foreign athlete (used in club name matching)
# These are checked with case-insensitive substring matching
FOREIGN_INDICATORS = [
    'mongolia', 'international', 'gis dragon', 'iskl'
]

# International school patterns - students at these schools are likely foreign/expat
INTERNATIONAL_SCHOOL_PATTERNS = [
    'ISKL', 'GIS', 'BIS', 'MKIS', 'MUWCI', 'ALICE SMITH',
    'GARDEN INTERNATIONAL', 'GIS DRAGONS',
    'INTERNATIONAL SCHOOL', 'BRITISH INTERNATIONAL', 'BRITISH SCHOOL',
    'AUSTRALIAN SCHOOL', 'AUSTRALIAN INTERNATIONAL',
    'AMERICAN SCHOOL', 'AMERICAN INTERNATIONAL',
    'MONT KIARA INTERNATIONAL', 'NEXUS', 'EPSOM', 'MARLBOROUGH',
]

# Known foreign club/country patterns
FOREIGN_CLUB_PATTERNS = [
    'SINGAPORE', 'SGP', 'INDONESIA', 'INA', 'THAILAND', 'THA',
    'PHILIPPINES', 'PHI', 'VIETNAM', 'VIE', 'BRUNEI', 'BRU',
    'HONG KONG', 'HKG', 'CHINA', 'CHN', 'JAPAN', 'JPN',
    'KOREA', 'KOR', 'TAIWAN', 'TPE', 'MONGOLIA', 'MGL',
]


def is_likely_foreign(
    excel_nation: Optional[str],
    club_name: Optional[str],
    full_name: Optional[str] = None
) -> bool:
    """
    Determine if an unmatched athlete is likely foreign based on multiple signals.

    Args:
        excel_nation: Nation code from results file (may be None or inaccurate)
        club_name: Club name from results file
        full_name: Athlete's full name (currently unused, reserved for future name-based detection)

    Returns:
        True if likely foreign, False if likely Malaysian

    Signals checked (in order):
        1. Excel nation is not MAS/Malaysia
        2. Club is an international school (likely expat students)
        3. Club contains foreign country indicators
    """
    # Signal 1: Excel nation is not MAS/Malaysia
    if excel_nation:
        nation_upper = excel_nation.upper().strip()
        if nation_upper and nation_upper not in ('MAS', 'MALAYSIA', ''):
            return True

    # Signal 2: International school students - flag as likely foreign
    if club_name:
        club_upper = club_name.upper()
        for pattern in INTERNATIONAL_SCHOOL_PATTERNS:
            if pattern in club_upper:
                return True

        # Also check the simple foreign indicators (case-insensitive)
        club_lower = club_name.lower()
        for indicator in FOREIGN_INDICATORS:
            if indicator in club_lower:
                return True

    # Signal 3: Known foreign club/country patterns (word boundary check)
    # Use word boundary to avoid false positives like "DOLPHIN" matching "PHI"
    if club_name:
        import re
        club_upper = club_name.upper()
        for pattern in FOREIGN_CLUB_PATTERNS:
            # Check for word boundary match (pattern as whole word)
            if re.search(r'\b' + re.escape(pattern) + r'\b', club_upper):
                return True

    # Default: assume Malaysian (MAS)
    return False
