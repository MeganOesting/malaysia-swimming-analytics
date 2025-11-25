#!/usr/bin/env python3
"""
Malaysia Swimming Analytics – meet conversion pipeline.

This module rebuilds the meet ingestion logic so that uploads:
  * trust `SWIMTIME_N` for numeric timing while keeping `SWIMTIME` for display,
  * require that every athlete already exists in the curated `athletes` table,
  * stop and surface actionable validation errors (athlete, nation, club, event),
  * validate relay sheets (team rows) alongside individual events,
  * enrich results with team metadata sourced from `clubs`.

All validation issues are accumulated and raised together as a
`ConversionValidationError` so the admin UI can show precise next steps.
"""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

# --------------------------------------------------------------------------- #
# Constants & simple helpers
# --------------------------------------------------------------------------- #

ALLOWED_COURSES = {"LCM", "SCM"}

STROKE_MAP = {
    "FR": "Free",
    "FREE": "Free",
    "FREESTYLE": "Free",
    "BK": "Back",
    "BACK": "Back",
    "BR": "Breast",
    "BRE": "Breast",
    "BREAST": "Breast",
    "BU": "Fly",
    "FLY": "Fly",
    "BUTTERFLY": "Fly",
    "ME": "IM",
    "IM": "IM",
}

RELAY_STROKE_MAP = {
    "FR": "Free",
    "FREE": "Free",
    "FREESTYLE": "Free",
    "MEDLEY": "Medley",
    "ME": "Medley",
    "IM": "Medley",
}

COLUMN_INDEXES = {
    "COURSE": 0,
    "GENDER": 1,
    "DISTANCE": 2,
    "STROKE": 3,
    "FULLNAME": 4,
    "BIRTHDATE": 5,
    "NATION": 6,
    "CLUBCODE": 7,
    "SWIMTIME": 8,
    "SWIMTIME_N": 9,
    "PTS_FINA": 10,
    "PTS_RUDOLPH": 11,
    "PLACE": 12,
    "MEETDATE": 13,
    "MEETCITY": 14,
    "MEETNAME": 15,
    "CLUBNAME": 16,
}

USECOLS = sorted(set(COLUMN_INDEXES.values()))
POSITION_MAP = {original_idx: pos for pos, original_idx in enumerate(USECOLS)}

RELAY_PATTERN = re.compile(r"4\s*[xX]\s*(\d{2,4})")


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass
class AthleteRecord:
    id: str
    full_name: str
    birthdate: str
    nation: str
    gender: Optional[str] = None
    club_name: Optional[str] = None  # Club name from athlete's record


@dataclass
class ClubRecord:
    club_name: str
    club_code: Optional[str]
    state_code: Optional[str]
    nation: Optional[str]
    alias: Optional[str] = None  # Alternative name for matching


@dataclass
class RelayMeta:
    leg_distance: int  # e.g. 100 or 200
    stroke_kind: str   # "Free" or "Medley"


class ConversionValidationError(Exception):
    """Raised when validation detects issues that require manual intervention."""

    def __init__(self, message: str, details: Dict[str, List[Dict[str, str]]]):
        super().__init__(message)
        self.details = details


class ValidationCollector:
    """Collects validation issues to report them in one shot."""

    def __init__(self) -> None:
        self.missing_athletes: List[Dict[str, str]] = []
        self.birthdate_mismatches: List[Dict[str, str]] = []
        self.birthdate_updates: List[Dict[str, str]] = []  # Birthdate updates to apply (transposed birthdates)
        self.nation_mismatches: List[Dict[str, str]] = []
        self.gender_mismatches: List[Dict[str, str]] = []
        self.name_format_mismatches: List[Dict[str, str]] = []  # Exact FULLNAME doesn't match but normalized does
        self.fullname_updates: List[Dict[str, str]] = []  # FULLNAME updates to apply (results name overwrites registration name)
        self.club_misses: List[Dict[str, str]] = []
        self.event_misses: List[Dict[str, str]] = []
        self.time_errors: List[Dict[str, str]] = []
        self.course_errors: List[Dict[str, str]] = []
        self.general_errors: List[Dict[str, str]] = []
        self.skipped_rows: List[Dict[str, str]] = []  # Track skipped rows with reasons

    # ---- collection helpers ------------------------------------------------ #

    def add_missing_athlete(
        self, sheet: str, row: int, full_name: str, birthdate: str, gender: str, meet_name: str = None, club_name: str = None
    ) -> None:
        """Report when athlete is not found in database - NEEDS TO BE ADDED"""
        self.missing_athletes.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "birthdate": birthdate or "(blank)",
                "gender": gender or "(blank)",
                "meet_name": meet_name or "(unknown)",
                "club_name": club_name or "(blank)",
                "action_needed": "ADD TO DATABASE",  # Emphasize this needs action
            }
        )

    def add_birthdate_update(
        self,
        athlete_id: str,
        new_birthdate: str,
        old_birthdate: str,
        sheet: str,
        row: int,
        meet_name: str = None,
    ) -> None:
        """Track birthdate updates: results birthdate will overwrite database birthdate (for transposed dates)"""
        self.birthdate_updates.append(
            {
                "athlete_id": athlete_id,
                "new_birthdate": new_birthdate,
                "old_birthdate": old_birthdate,
                "sheet": sheet,
                "row": str(row),
                "meet_name": meet_name or "",
            }
        )

    def add_birthdate_mismatch(
        self,
        sheet: str,
        row: int,
        full_name: str,
        workbook_birthdate: str,
        database_birthdate: str,
        meet_name: str = None,
        athlete_id: str = None,
    ) -> None:
        # Include both birthdates so user can see what didn't match
        self.birthdate_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "message": f"Name matched exactly: '{full_name}' but birthdate mismatch - Excel: {workbook_birthdate or '(blank)'}, Database: {database_birthdate or '(blank)'}",
                "workbook_birthdate": workbook_birthdate or "(blank)",
                "database_birthdate": database_birthdate or "(blank)",
                "meet_name": meet_name or "(unknown)",
                "athlete_id": athlete_id or "(unknown)",
            }
        )

    def add_nation_mismatch(
        self, sheet: str, row: int, full_name: str, workbook_nation: str, database_nation: str, athlete_id: str = None
    ) -> None:
        self.nation_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "workbook_nation": workbook_nation or "(blank)",
                "database_nation": database_nation or "(blank)",
                "athlete_id": athlete_id or "(unknown)",
            }
        )

    def add_gender_mismatch(
        self, sheet: str, row: int, full_name: str, workbook_gender: str, database_gender: str
    ) -> None:
        self.gender_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "workbook_gender": workbook_gender or "(blank)",
                "database_gender": database_gender or "(blank)",
            }
        )

    def add_name_format_mismatch(
        self, sheet: str, row: int, upload_fullname: str, database_fullname: str, athlete_id: str = None, meet_name: str = None
    ) -> None:
        """Report when FULLNAME from upload doesn't match exactly but normalized match found"""
        self.name_format_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "upload_fullname": upload_fullname,
                "database_fullname": database_fullname,
                "athlete_id": athlete_id,
                "meet_name": meet_name or "(unknown)",
            }
        )

    def add_fullname_update(
        self, athlete_id: str, new_fullname: str, old_fullname: str, sheet: str, row: int, meet_name: str = None
    ) -> None:
        """Track FULLNAME updates: results FULLNAME will overwrite registration FULLNAME"""
        self.fullname_updates.append(
            {
                "athlete_id": athlete_id,
                "old_fullname": old_fullname,
                "new_fullname": new_fullname,
                "sheet": sheet,
                "row": str(row),
                "meet_name": meet_name or "(unknown)",
            }
        )

    def add_club_missing(self, sheet: str, row: int, club_name: str, full_name: str = None, meet_name: str = None, meet_city: str = None, athlete_id: str = None) -> None:
        self.club_misses.append(
            {
                "sheet": sheet,
                "row": str(row),
                "club_name": club_name or "(blank)",
                "full_name": full_name or "(unknown)",
                "meet_name": meet_name or "(unknown)",
                "meet_city": meet_city or "(unknown)",
                "athlete_id": athlete_id or "(unknown)",
            }
        )

    def add_event_missing(self, sheet: str, row: int, description: str) -> None:
        self.event_misses.append(
            {
                "sheet": sheet,
                "row": str(row),
                "description": description,
            }
        )

    def add_time_error(
        self,
        sheet: str,
        row: int,
        full_name: str,
        swimtime: str,
        swimtime_n: str,
    ) -> None:
        self.time_errors.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "swimtime": swimtime or "(blank)",
                "swimtime_n": swimtime_n or "(blank)",
            }
        )

    def add_course_error(self, sheet: str, row: int, full_name: str, value: str) -> None:
        self.course_errors.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "value": value or "(blank)",
            }
        )

    def add_general_error(self, sheet: str, row: int, message: str) -> None:
        self.general_errors.append(
            {
                "sheet": sheet,
                "row": str(row),
                "message": message,
            }
        )

    def add_skipped_row(self, sheet: str, row: int, full_name: str, reason: str) -> None:
        """Track skipped rows during insertion with specific reason."""
        self.skipped_rows.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name or "(unknown)",
                "reason": reason,
            }
        )

    # ---- aggregation ------------------------------------------------------- #

    def has_errors(self) -> bool:
        return any(
            (
                self.missing_athletes,
                self.birthdate_mismatches,
                self.nation_mismatches,
                self.gender_mismatches,
                self.name_format_mismatches,
                self.club_misses,
                self.event_misses,
                self.time_errors,
                self.course_errors,
                self.general_errors,
                self.skipped_rows,
            )
        )

    def summary(self) -> str:
        if not self.has_errors():
            return ""

        def _line(label: str, items: List[Any]) -> str:
            return f"- {label}: {len(items)} issue(s)"

        lines = ["Conversion halted due to data validation issues."]
        if self.missing_athletes:
            lines.append(_line("Missing athletes - NEED TO BE ADDED TO DATABASE", self.missing_athletes))
        if self.birthdate_mismatches:
            lines.append(_line("Birthdate mismatches", self.birthdate_mismatches))
            # Add line-by-line details for birthdate mismatches showing both birthdates
            for mismatch in self.birthdate_mismatches[:50]:  # Limit to first 50 to avoid huge output
                sheet = mismatch.get("sheet", "Unknown")
                row = mismatch.get("row", "?")
                full_name = mismatch.get("full_name", "Unknown")
                excel_bday = mismatch.get("workbook_birthdate", "(blank)")
                db_bday = mismatch.get("database_birthdate", "(blank)")
                lines.append(f"  - {sheet} row {row}: '{full_name}' - Excel birthdate: {excel_bday}, Database birthdate: {db_bday}")
            if len(self.birthdate_mismatches) > 50:
                lines.append(f"  ... and {len(self.birthdate_mismatches) - 50} more birthdate mismatches")
        if self.nation_mismatches:
            lines.append(_line("Nation mismatches", self.nation_mismatches))
        if self.gender_mismatches:
            lines.append(_line("Gender mismatches", self.gender_mismatches))
        if self.name_format_mismatches:
            lines.append(_line("Name format mismatches", self.name_format_mismatches))
            # Add line-by-line details for name format mismatches
            for mismatch in self.name_format_mismatches[:50]:  # Limit to first 50
                sheet = mismatch.get("sheet", "Unknown")
                row = mismatch.get("row", "?")
                upload_name = mismatch.get("upload_fullname", "Unknown")
                db_name = mismatch.get("database_fullname", "Unknown")
                lines.append(f"  - {sheet} row {row}: Upload='{upload_name}' but Database='{db_name}' (case/format difference)")
            if len(self.name_format_mismatches) > 50:
                lines.append(f"  ... and {len(self.name_format_mismatches) - 50} more name format mismatches")
        if self.club_misses:
            lines.append(_line("Unknown clubs/teams", self.club_misses))
        if self.event_misses:
            lines.append(_line("Unknown events", self.event_misses))
        if self.time_errors:
            lines.append(_line("Time parsing issues", self.time_errors))
        if self.course_errors:
            lines.append(_line("Course issues", self.course_errors))
        if self.general_errors:
            lines.append(_line("Other issues", self.general_errors))
        if self.skipped_rows:
            lines.append(_line("Skipped result rows", self.skipped_rows))
            # Add line-by-line details for skipped rows
            for skip in self.skipped_rows:
                sheet = skip.get("sheet", "Unknown")
                row = skip.get("row", "?")
                full_name = skip.get("full_name", "Unknown")
                reason = skip.get("reason", "Unknown reason")
                lines.append(f"  - {sheet} row {row}: {full_name} - {reason}")
        lines.append("Review the detailed payload, correct the data, and retry the upload.")
        return "\n".join(lines)

    def payload(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "missing_athletes": self.missing_athletes,
            "birthdate_mismatches": self.birthdate_mismatches,
            "nation_mismatches": self.nation_mismatches,
            "gender_mismatches": self.gender_mismatches,
            "name_format_mismatches": self.name_format_mismatches,
            "club_misses": self.club_misses,
            "event_misses": self.event_misses,
            "time_errors": self.time_errors,
            "course_errors": self.course_errors,
            "general_errors": self.general_errors,
            "skipped_rows": self.skipped_rows,
        }

    def raise_if_errors(self) -> None:
        if self.has_errors():
            raise ConversionValidationError(self.summary(), self.payload())


# --------------------------------------------------------------------------- #
# Low-level helpers
# --------------------------------------------------------------------------- #


def as_clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "nat"}:
        return ""
    return text


def normalize_name(value: Any) -> str:
    return " ".join(as_clean_str(value).upper().split())


def normalize_state_code(state_code: Optional[str]) -> Optional[str]:
    """
    Normalize state codes to standard format.
    WPKL, KUL -> KL (Kuala Lumpur)
    SGR -> SEL (Selangor)
    etc.
    """
    if not state_code:
        return None
    state_upper = state_code.upper().strip()
    
    # Normalize variants to standard codes
    if state_upper in ['WPKL', 'KUL']:
        return 'KL'
    elif state_upper == 'SGR':
        return 'SEL'
    elif state_upper == 'JOHOR':
        return 'JHR'
    elif state_upper == 'PENANG':
        return 'PNG'
    elif state_upper == 'PERAK':
        return 'PRK'
    elif state_upper == 'SABAH':
        return 'SBH'
    elif state_upper == 'SARAWAK':
        return 'SWK'
    elif state_upper == 'KEDAH':
        return 'KDH'
    elif state_upper == 'KELANTAN':
        return 'KTN'
    elif state_upper in ['MELAKA', 'MALACCA']:
        return 'MLK'
    elif state_upper == 'NEGERI SEMBILAN':
        return 'NSN'
    elif state_upper == 'PAHANG':
        return 'PHG'
    elif state_upper == 'PERLIS':
        return 'PLS'
    elif state_upper == 'TERENGGANU':
        return 'TRG'
    elif state_upper == 'PUTRAJAYA':
        return 'PJY'
    elif state_upper == 'LABUAN':
        return 'LBN'
    else:
        return state_upper


def clean_club_name_and_extract_state(club_name: str) -> Tuple[str, Optional[str]]:
    """
    Remove state codes/names from club name and extract state code if present.
    
    Returns:
        (cleaned_club_name, state_code)
    
    Examples:
        "Blue Marlin Swimming Club Sabah" -> ("BLUE MARLIN SWIMMING CLUB", "SBH")
        "Aquasplash Swimming Club Sel" -> ("AQUASPLASH SWIMMING CLUB", "SEL")
        "British International School KL" -> ("BRITISH INTERNATIONAL SCHOOL", "KL")
    """
    if not club_name:
        return "", None
    
    norm = normalize_name(club_name)
    
    # State codes (3-4 letter codes)
    state_codes = [
        'SEL', 'WPKL', 'KL', 'JHR', 'PNG', 'PRK', 'KDH', 'KTN', 'MLK', 
        'NSN', 'PHG', 'PLS', 'SBH', 'SWK', 'TRG', 'KUL', 'LBN', 'PJY',
        'SGR', 'JOHOR', 'PENANG', 'PERAK', 'SABAH', 'SARAWAK', 'KEDAH',
        'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN', 'PAHANG', 'PERLIS',
        'TERENGGANU', 'PUTRAJAYA', 'LABUAN'
    ]
    
    # Full state names (need to check these too)
    state_names = {
        'SABAH': 'SBH',
        'SELANGOR': 'SEL',
        'KUALA LUMPUR': 'KL',
        'JOHOR': 'JHR',
        'PENANG': 'PNG',
        'PERAK': 'PRK',
        'KEDAH': 'KDH',
        'KELANTAN': 'KTN',
        'MELAKA': 'MLK',
        'MALACCA': 'MLK',
        'NEGERI SEMBILAN': 'NSN',
        'PAHANG': 'PHG',
        'PERLIS': 'PLS',
        'SARAWAK': 'SWK',
        'TERENGGANU': 'TRG',
        'PUTRAJAYA': 'PJY',
        'LABUAN': 'LBN'
    }
    
    extracted_state = None
    cleaned = norm
    
    # Try to find and remove state codes/names from the end
    # Check state codes first (shorter, more common)
    for code in sorted(state_codes, key=len, reverse=True):  # Check longer codes first
        if cleaned.endswith(code):
            cleaned = cleaned[:-len(code)].strip()
            # Normalize state code using the normalization function
            extracted_state = normalize_state_code(code)
            break
    
    # If no state code found, try state names
    if not extracted_state:
        for state_name, state_code in sorted(state_names.items(), key=lambda x: len(x[0]), reverse=True):
            if cleaned.endswith(state_name):
                cleaned = cleaned[:-len(state_name)].strip()
                extracted_state = state_code
                break
    
    # Clean up any extra spaces
    cleaned = " ".join(cleaned.split())
    
    return cleaned, extracted_state


def parse_excel_date(value: Any) -> Optional[datetime]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    try:
        if isinstance(value, (int, float)):
            parsed = pd.to_datetime(value, origin="1899-12-30", unit="D", errors="coerce")
            if pd.notna(parsed):
                return parsed.to_pydatetime()
    except Exception:
        pass
    text = as_clean_str(value)
    if not text:
        return None
    if " " in text:
        text = text.split(" ", 1)[0]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.to_pydatetime()
    except Exception:
        pass
    return None


def try_swap_month_day(birthdate_str: str) -> Optional[str]:
    """Try swapping month and day in birthdate (for dd.mm vs mm.dd issues).
    
    Input: YYYY.MM.DD format
    Output: YYYY.DD.MM format (if valid), None otherwise
    """
    if not birthdate_str or '.' not in birthdate_str:
        return None
    parts = birthdate_str.split('.')
    if len(parts) == 3:
        year, month, day = parts
        # Only swap if both month and day are valid (month <= 12, day <= 31)
        # But we'll be lenient - just swap and let the comparison happen
        return f"{year}.{day.zfill(2)}.{month.zfill(2)}"
    return None

def is_birthdate_transposed(excel_bday: str, db_bday: str) -> bool:
    """Check if birthdates are transposed (same year, month/day swapped).
    
    Returns True if:
    - Same year
    - Month and day are swapped (e.g., 2008.02.01 vs 2008.01.02)
    
    Examples:
    - Excel: 2008.02.01, DB: 2008.01.02 - transposed (Feb 1 vs Jan 2)
    - Excel: 2008.01.04, DB: 2008.04.01 - transposed (Jan 4 vs Apr 1)
    - Excel: 2011.05.09, DB: 2011.09.05 - transposed (May 9 vs Sep 5)
    """
    if not excel_bday or not db_bday:
        return False
    try:
        excel_parts = excel_bday.split('.')
        db_parts = db_bday.split('.')
        if len(excel_parts) == 3 and len(db_parts) == 3:
            excel_year, excel_month, excel_day = excel_parts
            db_year, db_month, db_day = db_parts
            # Check if year matches and month/day are swapped
            if excel_year == db_year:
                if excel_month == db_day and excel_day == db_month:
                    return True
    except:
        pass
    return False

def should_use_excel_day(excel_bday: str, db_bday: str) -> bool:
    """Check if we should use Excel day (when name, year, and month match).
    
    Returns True if:
    - Same year
    - Same month
    - Different day
    
    Example: Excel: 2012.05.05, DB: 2012.05.08 -> use Excel day (05)
    """
    if not excel_bday or not db_bday:
        return False
    try:
        excel_parts = excel_bday.split('.')
        db_parts = db_bday.split('.')
        if len(excel_parts) == 3 and len(db_parts) == 3:
            excel_year, excel_month, excel_day = excel_parts
            db_year, db_month, db_day = db_parts
            # Check if year and month match, but day is different
            if excel_year == db_year and excel_month == db_month and excel_day != db_day:
                return True
    except:
        pass
    return False

def should_use_excel_birthdate_when_year_matches(excel_bday: str, db_bday: str) -> bool:
    """Check if we should use Excel birthdate when name matches exactly and year matches.
    
    Returns True if:
    - Same year
    - Month or day is different (or both)
    
    This is for cases where the name matches exactly, so we trust the Excel birthdate
    even if month/day are different, as long as the year matches.
    
    Example: Excel: 2009.01.27, DB: 2009.02.02 -> use Excel birthdate (2009.01.27)
    """
    if not excel_bday or not db_bday:
        return False
    try:
        excel_parts = excel_bday.split('.')
        db_parts = db_bday.split('.')
        if len(excel_parts) == 3 and len(db_parts) == 3:
            excel_year, excel_month, excel_day = excel_parts
            db_year, db_month, db_day = db_parts
            # Check if year matches but month or day is different
            if excel_year == db_year and (excel_month != db_month or excel_day != db_day):
                return True
    except:
        pass
    return False

def normalize_birthdate(value: Any) -> str:
    """Normalize birthdate to ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ), handling various input formats.

    This function handles:
    - Already normalized strings (ISO 8601) - returns as-is
    - Old format (YYYY.MM.DD) - converts to ISO 8601
    - Datetime objects (pd.Timestamp, datetime)
    - Strings with time components ("2005-10-29 00:00:00")
    - Various date formats (YYYY-MM-DD, DD/MM/YYYY, etc.)
    - None/NaN values - returns empty string

    Returns format: YYYY-MM-DDTHH:MM:SSZ (ISO 8601 with UTC timezone)
    """
    # Handle None/NaN
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    # Handle already-normalized strings (ISO 8601 format) - return as-is
    if isinstance(value, str):
        # Check if already in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        if "T" in value and value.endswith("Z"):
            return value  # Already normalized to ISO 8601

        # Convert from old YYYY.MM.DD format to ISO 8601
        if "." in value and len(value) == 10:
            parts = value.split(".")
            if len(parts) == 3 and all(p.isdigit() for p in parts) and len(parts[0]) == 4:
                return f"{parts[0]}-{parts[1]}-{parts[2]}T00:00:00Z"  # Convert old format to ISO 8601

        # Remove time component if present (e.g., "2005-10-29 00:00:00" -> "2005-10-29")
        if " " in value:
            value = value.split(" ", 1)[0]

    # Handle datetime/Timestamp objects directly
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT00:00:00Z")
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().strftime("%Y-%m-%dT00:00:00Z")

    # Parse and normalize
    dt = parse_excel_date(value)
    if not dt:
        text = "".join(ch for ch in as_clean_str(value) if ch.isdigit())
        if len(text) == 8:
            return f"{text[:4]}-{text[4:6]}-{text[6:]}T00:00:00Z"
        return ""
    return dt.strftime("%Y-%m-%dT00:00:00Z")


def convert_time_to_seconds(time_str: str) -> Optional[float]:
    text = as_clean_str(time_str)
    if not text:
        return None
    if ":" in text:
        parts = text.split(":")
        try:
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_optional_int(value: Any) -> Optional[int]:
    text = as_clean_str(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_optional_float(value: Any) -> Optional[float]:
    text = as_clean_str(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_swimtime_numeric(raw_numeric: Any, raw_string: str) -> Optional[float]:
    numeric_text = as_clean_str(raw_numeric)
    if numeric_text:
        try:
            return float(numeric_text)
        except ValueError:
            candidate = convert_time_to_seconds(numeric_text)
            if candidate is not None:
                return candidate
    string_candidate = convert_time_to_seconds(raw_string)
    if string_candidate is not None:
        return string_candidate
    return None


def compute_ages(birthdate_str: str, meet_date: Optional[datetime]) -> Tuple[Optional[int], Optional[int]]:
    if not birthdate_str or not meet_date:
        return None, None
    try:
        birth_dt = datetime.strptime(birthdate_str, "%Y.%m.%d")
    except ValueError:
        parsed = parse_excel_date(birthdate_str)
        if not parsed:
            return None, None
        birth_dt = parsed
    day_age = meet_date.year - birth_dt.year
    if (meet_date.month, meet_date.day) < (birth_dt.month, birth_dt.day):
        day_age -= 1
    year_age = meet_date.year - birth_dt.year
    return day_age, year_age


def parse_course(value: Any) -> Optional[str]:
    text = as_clean_str(value).upper()
    if text in ALLOWED_COURSES:
        return text
    return None


def parse_gender(value: Any) -> Optional[str]:
    text = as_clean_str(value).upper()
    if not text:
        return None
    gender = text[0]
    if gender in {"M", "F", "X"}:
        return gender
    return None


def detect_relay(distance_value: Any, stroke_value: Any, sheet_name: str) -> Optional[RelayMeta]:
    combined = " ".join(
        part
        for part in [as_clean_str(distance_value), as_clean_str(stroke_value), as_clean_str(sheet_name)]
        if part
    ).upper()
    match = RELAY_PATTERN.search(combined)
    if not match:
        return None
    leg_distance = int(match.group(1))
    stroke_source = as_clean_str(stroke_value).upper()
    stroke_kind = RELAY_STROKE_MAP.get(stroke_source)
    if not stroke_kind:
        if "FREE" in combined:
            stroke_kind = "Free"
        elif "MEDLEY" in combined or "IM" in combined:
            stroke_kind = "Medley"
    if not stroke_kind or leg_distance not in (100, 200):
        return None
    return RelayMeta(leg_distance=leg_distance, stroke_kind=stroke_kind)


def relay_description(meta: RelayMeta, course: str, gender: str) -> str:
    return f"{course} 4x{meta.leg_distance} {meta.stroke_kind} relay ({gender})"


def get_value(row: pd.Series, column_key: str) -> Any:
    idx = COLUMN_INDEXES[column_key]
    pos = POSITION_MAP.get(idx)
    if pos is None:
        return None
    try:
        return row.iloc[pos]
    except (IndexError, AttributeError):
        return None


# --------------------------------------------------------------------------- #
# Lookup indexes sourced from the database
# --------------------------------------------------------------------------- #


def load_roster_mapping(roster_file_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load Roster (club name) mapping from SportEngine file.
    Returns a dict mapping normalized athlete names to club names.
    """
    if not roster_file_path:
        # Default path
        roster_file_path = Path("data/manual_matching/Database Athlete Sort/SportEngine Data 17.11.25.xlsx")
    
    if not roster_file_path.exists():
        return {}
    
    try:
        df = pd.read_excel(roster_file_path, sheet_name='Sheet0', engine='openpyxl')
        
        # Check if required columns exist
        if 'Roster' not in df.columns:
            return {}
        
        # Build mapping: normalized name -> club name
        roster_map = {}
        for _, row in df.iterrows():
            # Build name from available fields
            first = str(row.get('Memb. First Name', '') or '').strip()
            last = str(row.get('Memb. Last Name', '') or '').strip()
            middle = str(row.get('Memb. Middle Initial', '') or '').strip()
            preferred = str(row.get('Preferred Name', '') or '').strip()
            roster = str(row.get('Roster', '') or '').strip()
            
            if not roster:
                continue
            
            # Try different name formats (order doesn't matter - create all variations)
            if last and first:
                # Format: "LAST, FIRST MIDDLE" (e.g., "KOH, Isaac Yue Jian")
                full_name = f"{last}, {first}"
                if middle and middle != '-':
                    full_name += f" {middle}"
                norm_name = normalize_name(full_name)
                if norm_name:
                    roster_map[norm_name] = roster
                
                # Also try "LAST, MIDDLE FIRST" (order doesn't matter - e.g., "KOH, Yue Jian Isaac")
                if middle and middle != '-':
                    full_name_reversed = f"{last}, {middle} {first}"
                    norm_name_reversed = normalize_name(full_name_reversed)
                    if norm_name_reversed and norm_name_reversed != norm_name:
                        roster_map[norm_name_reversed] = roster
                
                # Also try "LAST, FIRST" without middle (e.g., "KOH, Isaac")
                full_name_no_middle = f"{last}, {first}"
                norm_name_no_middle = normalize_name(full_name_no_middle)
                if norm_name_no_middle and norm_name_no_middle != norm_name:
                    roster_map[norm_name_no_middle] = roster
                
                # Also try reversed format: "FIRST MIDDLE, LAST" (for cases like "XI FONG, Nga")
                if middle and middle != '-':
                    reversed_name = f"{middle} {last}, {first}"
                    norm_reversed = normalize_name(reversed_name)
                    if norm_reversed:
                        roster_map[norm_reversed] = roster
                    # Also try "FIRST, MIDDLE LAST" (order doesn't matter)
                    reversed_name2 = f"{first}, {middle} {last}"
                    norm_reversed2 = normalize_name(reversed_name2)
                    if norm_reversed2:
                        roster_map[norm_reversed2] = roster
                
                # Handle cases where first name is multi-word but Excel has it as single word
                # Example: "WENBO, Gao" (Excel) should match "Gao, Wen Bo" (Database)
                # Try "LAST, FIRSTNOSPACE" format (e.g., "GAO, WENBO")
                first_no_space = first.replace(" ", "").upper()
                if first_no_space != first.upper():  # Only if first name has spaces
                    combined_name = f"{last}, {first_no_space}"
                    norm_combined = normalize_name(combined_name)
                    if norm_combined:
                        roster_map[norm_combined] = roster
                    # Also try reversed: "FIRSTNOSPACE, LAST" (e.g., "WENBO, GAO")
                    reversed_combined = f"{first_no_space}, {last}"
                    norm_reversed_combined = normalize_name(reversed_combined)
                    if norm_reversed_combined:
                        roster_map[norm_reversed_combined] = roster
            
            # Also try with preferred name (handle cases like "HANNES WAN, Khai Hern" where "Hannes" is preferred name)
            if preferred and last:
                # Standard format: "LAST, PREFERRED"
                pref_name = f"{last}, {preferred}"
                norm_pref = normalize_name(pref_name)
                if norm_pref:
                    roster_map[norm_pref] = roster
                # Reversed format: "PREFERRED, LAST"
                pref_name2 = f"{preferred}, {last}"
                norm_pref2 = normalize_name(pref_name2)
                if norm_pref2:
                    roster_map[norm_pref2] = roster
                # Format with first name: "PREFERRED LAST, FIRST" (e.g., "HANNES WAN, Khai Hern")
                if first:
                    pref_name3 = f"{preferred} {last}, {first}"
                    norm_pref3 = normalize_name(pref_name3)
                    if norm_pref3:
                        roster_map[norm_pref3] = roster
                    # Also try "LAST, PREFERRED FIRST" format
                    pref_name4 = f"{last}, {preferred} {first}"
                    norm_pref4 = normalize_name(pref_name4)
                    if norm_pref4:
                        roster_map[norm_pref4] = roster
        
        return roster_map
    except Exception as e:
        print(f"[WARNING] Could not load Roster mapping from {roster_file_path}: {e}", flush=True)
        return {}


class AthleteIndex:
    def __init__(self, records: List[AthleteRecord], roster_map: Optional[Dict[str, str]] = None):
        self.records: List[AthleteRecord] = records  # Store records for exact matching
        self.roster_map: Dict[str, str] = roster_map or {}  # Mapping of normalized names to club names
        self.by_name: Dict[str, List[AthleteRecord]] = {}
        for record in records:
            # Index by FULLNAME
            key = normalize_name(record.full_name)
            if key:
                self.by_name.setdefault(key, []).append(record)
            # Also index by aliases if they exist
            if hasattr(record, 'alias_1') and record.alias_1:
                alias_key = normalize_name(record.alias_1)
                if alias_key:
                    self.by_name.setdefault(alias_key, []).append(record)
            if hasattr(record, 'alias_2') and record.alias_2:
                alias_key = normalize_name(record.alias_2)
                if alias_key:
                    self.by_name.setdefault(alias_key, []).append(record)

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "AthleteIndex":
        columns = {row[1].lower() for row in conn.execute("PRAGMA table_info(athletes)")}
        columns_original = {row[1] for row in conn.execute("PRAGMA table_info(athletes)")}
        select_cols = ["id", "FULLNAME", "BIRTHDATE", "NATION"]
        gender_present = "gender" in columns
        gender_col = "GENDER"  # Default, will be updated if present
        if gender_present:
            # Use original case for column name
            gender_col = next((col for col in columns_original if col.lower() == "gender"), "GENDER")
            select_cols.append(gender_col)
        # Check if CLUBNAME column exists in athletes table
        clubname_present = "clubname" in columns
        clubname_col = None
        if clubname_present:
            clubname_col = next((col for col in columns_original if col.lower() == "clubname"), "CLUBNAME")
            select_cols.append(clubname_col)
        # Also load alias fields if they exist
        alias_1_present = "athlete_alias_1" in columns  # columns is already lowercase set
        alias_2_present = "athlete_alias_2" in columns  # columns is already lowercase set
        if alias_1_present:
            alias_1_col = next((col for col in columns_original if col.lower() == "athlete_alias_1"), "athlete_alias_1")
            select_cols.append(alias_1_col)
        if alias_2_present:
            alias_2_col = next((col for col in columns_original if col.lower() == "athlete_alias_2"), "athlete_alias_2")
            select_cols.append(alias_2_col)
        query = f"SELECT {', '.join(select_cols)} FROM athletes"
        df = pd.read_sql_query(query, conn)
        records: List[AthleteRecord] = []
        alias_count = 0
        for _, row in df.iterrows():
            gender_value = row.get(gender_col) if gender_present else None
            club_name_value = None
            if clubname_present and clubname_col:
                club_name_value = as_clean_str(row.get(clubname_col))
            
            # IMPORTANT: Normalize birthdate consistently - handle all data types
            # pandas might return datetime, Timestamp, string, or None
            birthdate_raw = row["BIRTHDATE"]
            birthdate_normalized = normalize_birthdate(birthdate_raw)
            
            # Get nation column - handle both old (NATION) and new (nation) column names
            nation_value = row.get("nation") or row.get("NATION") or ""

            record = AthleteRecord(
                id=str(row["id"]),
                full_name=str(row["FULLNAME"] or ""),
                birthdate=birthdate_normalized,  # Always store normalized format
                nation=as_clean_str(nation_value).upper(),
                gender=as_clean_str(gender_value).upper() or None,
                club_name=club_name_value,
            )
            # Add alias fields as attributes if they exist
            if alias_1_present:
                alias_1_col = next((col for col in columns_original if col.lower() == "athlete_alias_1"), "athlete_alias_1")
                alias_1_value = row.get(alias_1_col)
                record.alias_1 = as_clean_str(alias_1_value) if alias_1_value else None
            if alias_2_present:
                alias_2_col = next((col for col in columns_original if col.lower() == "athlete_alias_2"), "athlete_alias_2")
                alias_2_value = row.get(alias_2_col)
                record.alias_2 = as_clean_str(alias_2_value) if alias_2_value else None
                if record.alias_2:
                    alias_count += 1
            if alias_1_present and record.alias_1:
                alias_count += 1
            records.append(record)
        # print(f"[AthleteIndex] Loaded {len(records)} athletes, {alias_count} with aliases (alias_1={alias_1_present}, alias_2={alias_2_present})")  # Removed to reduce noise
        # Load Roster mapping
        roster_map = load_roster_mapping()
        # Create instance
        instance = cls(records, roster_map=roster_map)
        return instance

    def find(
        self,
        full_name: str,
        birthdate: str,
        gender: Optional[str],
        sheet: str,
        row: int,
        collector: ValidationCollector,
        meet_name: str = None,
        club_name: Optional[str] = None,  # Club name from results file for additional matching
    ) -> Optional[AthleteRecord]:
        # Store club_name for use in add_missing_athlete calls
        self._current_club_name = club_name
        # Step 1: Normalize Excel fullname (no case, no commas, keep words whole)
        norm_name = normalize_name(full_name)
        if not norm_name:
            collector.add_general_error(sheet, row, "Blank FULLNAME encountered.")
            return None
        
        # Step 2: Normalize birthdate
        normalized_birthdate = normalize_birthdate(birthdate)
        if not normalized_birthdate:
            collector.add_missing_athlete(sheet, row, full_name, "(blank)", gender or "", meet_name, getattr(self, '_current_club_name', None))
            return None
        
        # Also try swapped birthdate (for month/day transpose)
        swapped_birthdate = try_swap_month_day(normalized_birthdate)
        
        # Helper function to check if birthdate matches (exact or transposed)
        def birthdate_matches(excel_bday: str, db_bday: Optional[str]) -> bool:
            """Check if birthdates match exactly or are month/day transposed"""
            if not db_bday:
                return False
            db_bday_norm = normalize_birthdate(db_bday)
            if not db_bday_norm:
                return False
            # Exact match or swapped match
            return (db_bday_norm == excel_bday) or (swapped_birthdate and db_bday_norm == swapped_birthdate)
        
        # Helper function to check if club names match
        def club_names_match(excel_club: Optional[str], db_club: Optional[str], roster_club: Optional[str] = None) -> bool:
            """Check if club names match (case-insensitive, handles variations and codes)"""
            if not excel_club:
                return False
            
            excel_norm = normalize_name(excel_club)
            # Extract club code from parentheses if present (e.g., "Kota Permai GCC Swim Team (KPGCC)" -> "KPGCC")
            excel_code = None
            if "(" in excel_club and ")" in excel_club:
                try:
                    excel_code = excel_club[excel_club.index("(")+1:excel_club.index(")")].strip()
                except:
                    pass
            
            # Check against database club
            if db_club:
                db_norm = normalize_name(db_club)
                # Exact match
                if excel_norm == db_norm:
                    return True
                # Substring match
                if excel_norm in db_norm or db_norm in excel_norm:
                    return True
                # Check if club code matches
                if excel_code and excel_code in db_norm:
                    return True
                if "(" in db_club and ")" in db_club:
                    try:
                        db_code = db_club[db_club.index("(")+1:db_club.index(")")].strip()
                        if excel_code and excel_code == db_code:
                            return True
                        if excel_norm and excel_norm in normalize_name(db_code):
                            return True
                    except:
                        pass
            
            # Check against roster club
            if roster_club:
                roster_norm = normalize_name(roster_club)
                if excel_norm == roster_norm or excel_norm in roster_norm or roster_norm in excel_norm:
                    return True
                if excel_code and excel_code in roster_norm:
                    return True
                if "(" in roster_club and ")" in roster_club:
                    try:
                        roster_code = roster_club[roster_club.index("(")+1:roster_club.index(")")].strip()
                        if excel_code and excel_code == roster_code:
                            return True
                    except:
                        pass
            
            return False
        
        # Get expected club name from Roster mapping
        expected_roster_club = self.roster_map.get(norm_name)
        
        # Step 3: Check for exact match on normalized fullname or normalized aliases
        # Use the by_name index for O(1) lookup instead of iterating all records
        exact_candidates = []
        candidates = self.by_name.get(norm_name, [])
        for r in candidates:
            # All candidates in by_name already have matching normalized name (fullname or alias)
            if birthdate_matches(normalized_birthdate, r.birthdate):
                exact_candidates.append(r)
        
        if exact_candidates:
            # Found exact match with birthdate - use it
            selected = exact_candidates[0]
            # Check if names differ (case/format) - will update fullname
            if normalize_name(selected.full_name) != norm_name:
                # Check if Excel name is already in an alias
                is_alias = False
                if hasattr(selected, 'alias_1') and selected.alias_1 and normalize_name(selected.alias_1) == norm_name:
                    is_alias = True
                if not is_alias and hasattr(selected, 'alias_2') and selected.alias_2 and normalize_name(selected.alias_2) == norm_name:
                    is_alias = True
                
                if not is_alias:
                    collector.add_fullname_update(selected.id, full_name, selected.full_name, sheet, row, meet_name)
                    selected.full_name = full_name
            
            # Check gender mismatch
            if gender and selected.gender and gender != selected.gender:
                collector.add_gender_mismatch(sheet, row, full_name, gender, selected.gender)
                return None
            
            return selected
        
        # Step 4: If no exact match, try flexible word-based matching (high confidence only)
        # Extract all words from Excel name (ignoring commas)
        excel_words = set([normalize_name(w) for w in full_name.replace(",", " ").split() if w.strip()])
        
        if not excel_words:
            # No words to match - truly missing
            collector.add_missing_athlete(sheet, row, full_name, normalized_birthdate, gender or "", meet_name, getattr(self, '_current_club_name', None))
            return None
        
        # Find high-confidence word-based matches
        # Note: This still iterates through records, but exact matches (above) use the index
        # which handles the majority of cases efficiently
        high_confidence_matches = []
        for r in self.records:
            # Extract all words from DB name (ignoring commas)
            db_words = set([normalize_name(w) for w in r.full_name.replace(",", " ").split() if w.strip()])
            
            # Also check aliases
            if hasattr(r, 'alias_1') and r.alias_1:
                alias_words = set([normalize_name(w) for w in r.alias_1.replace(",", " ").split() if w.strip()])
                db_words.update(alias_words)
            if hasattr(r, 'alias_2') and r.alias_2:
                alias_words = set([normalize_name(w) for w in r.alias_2.replace(",", " ").split() if w.strip()])
                db_words.update(alias_words)
            
            # High confidence: at least 3 words match, or all words if name is short (2-3 words)
            matching_words = excel_words.intersection(db_words)
            if len(matching_words) >= 3 or (len(excel_words) <= 3 and len(matching_words) == len(excel_words) and len(matching_words) >= 2):
                # High confidence name match - check birthdate
                if birthdate_matches(normalized_birthdate, r.birthdate):
                    high_confidence_matches.append(r)
        
        if high_confidence_matches:
            # Found high confidence match with birthdate - use it
            selected = high_confidence_matches[0]
            
            # Update fullname if different
            if normalize_name(selected.full_name) != norm_name:
                collector.add_fullname_update(selected.id, full_name, selected.full_name, sheet, row, meet_name)
                selected.full_name = full_name
            
            # Check gender mismatch
            if gender and selected.gender and gender != selected.gender:
                collector.add_gender_mismatch(sheet, row, full_name, gender, selected.gender)
                return None
            
            return selected
        
        # No match found - truly missing athlete
        collector.add_missing_athlete(sheet, row, full_name, normalized_birthdate, gender or "", meet_name, getattr(self, '_current_club_name', None))
        return None


class ClubIndex:
    def __init__(self, mapping: Dict[str, ClubRecord]):
        self.mapping = mapping

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "ClubIndex":
        # Check if alias column exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clubs)")
        columns = {row[1].lower() for row in cursor.fetchall()}
        has_alias = 'club_alias' in columns

        if has_alias:
            df = pd.read_sql_query(
                "SELECT club_name, club_code, state_code, club_nation, club_alias FROM clubs", conn
            )
        else:
            df = pd.read_sql_query(
                "SELECT club_name, club_code, state_code, club_nation FROM clubs", conn
            )
        
        mapping: Dict[str, ClubRecord] = {}
        for _, row in df.iterrows():
            club_name_raw = as_clean_str(row["club_name"])
            if not club_name_raw:
                continue
            
            # Clean state codes from club name in database
            club_name_cleaned, state_from_name = clean_club_name_and_extract_state(club_name_raw)
            
            # Use state from name if extracted, otherwise use database state_code
            # Normalize state code to ensure consistency (WPKL -> KL, etc.)
            state_code_raw = state_from_name or as_clean_str(row.get("state_code")) or None
            state_code = normalize_state_code(state_code_raw)
            
            # Use cleaned club name (without state codes)
            club_name_final = club_name_cleaned if club_name_cleaned else club_name_raw
            
            # Get alias if it exists
            alias = as_clean_str(row.get("club_alias")) if has_alias else None

            record = ClubRecord(
                club_name=club_name_final,
                club_code=as_clean_str(row.get("club_code")) or None,
                state_code=state_code,
                nation=as_clean_str(row.get("club_nation")).upper() if row.get("club_nation") else None,
                alias=alias,
            )
            # Store in mapping using cleaned name (without state codes)
            norm_name = normalize_name(club_name_final)
            if norm_name:
                mapping[norm_name] = record
            
            # Also map alias if it exists
            if alias:
                cleaned_alias, _ = clean_club_name_and_extract_state(alias)
                alias_norm = normalize_name(cleaned_alias) if cleaned_alias else normalize_name(alias)
                if alias_norm and alias_norm not in mapping:
                    mapping[alias_norm] = record
        
        return cls(mapping)

    def resolve(
        self,
        club_name: str,
        sheet: str,
        row: int,
        collector: ValidationCollector,
    ) -> Optional[ClubRecord]:
        # Clean state codes from the search term
        club_name_cleaned, extracted_state = clean_club_name_and_extract_state(club_name)
        norm = normalize_name(club_name_cleaned) if club_name_cleaned else normalize_name(club_name)
        
        if not norm:
            collector.add_club_missing(sheet, row, club_name)
            return None
        
        # Normalize extracted state code (WPKL -> KL, etc.)
        extracted_state_normalized = normalize_state_code(extracted_state)
        
        # Try exact match first (with cleaned name)
        record = self.mapping.get(norm)
        if record:
            # Normalize record's state code for comparison
            record_state_normalized = normalize_state_code(record.state_code)
            
            # If we extracted a state from Excel but DB doesn't have one, update the record's state
            if extracted_state_normalized and not record_state_normalized:
                record.state_code = extracted_state_normalized
            return record
        
        # Try removing " CLUB", " SWIMMING", " SCHOOL" suffixes and matching
        common_suffixes = ['CLUB', 'SWIMMING', 'SCHOOL', 'ACADEMY', 'TEAM']
        for suffix in common_suffixes:
            if norm.endswith(suffix):
                norm_without_suffix = norm[:-len(suffix)].strip()
                # Try exact match without suffix
                record = self.mapping.get(norm_without_suffix)
                if record:
                    record_state_normalized = normalize_state_code(record.state_code)
                    if extracted_state_normalized and not record_state_normalized:
                        record.state_code = extracted_state_normalized
                    return record
        
        # Try partial matching: check if any club name in database is contained in the search term or vice versa
        for db_norm, db_record in self.mapping.items():
            # Check if database club name is contained in search term (e.g., "Aquasplash Swimming Club" in "Aquasplash Swimming Club Sel")
            if db_norm in norm and len(db_norm) > 10:  # Only if DB name is substantial (>10 chars)
                db_state_normalized = normalize_state_code(db_record.state_code)
                if extracted_state_normalized and not db_state_normalized:
                    db_record.state_code = extracted_state_normalized
                return db_record
            # Check if search term (without suffixes) is contained in database name
            norm_clean = norm
            for suffix in common_suffixes:
                if norm_clean.endswith(suffix):
                    norm_clean = norm_clean[:-len(suffix)].strip()
            if norm_clean and norm_clean in db_norm and len(norm_clean) > 5:  # Only if search term is substantial (>5 chars)
                db_state_normalized = normalize_state_code(db_record.state_code)
                if extracted_state_normalized and not db_state_normalized:
                    db_record.state_code = extracted_state_normalized
                return db_record
        
        # No match found
        collector.add_club_missing(sheet, row, club_name)
        return None


class EventIndex:
    def __init__(self, mapping: Dict[Tuple[str, int, str, str], str]):
        self.mapping = mapping

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "EventIndex":
        df = pd.read_sql_query("SELECT id, event_course, event_distance, event_stroke, gender FROM events", conn)
        mapping: Dict[Tuple[str, int, str, str], str] = {}
        for _, row in df.iterrows():
            course = as_clean_str(row["event_course"]).upper()
            distance = int(row["event_distance"])
            stroke = as_clean_str(row["event_stroke"])
            gender = as_clean_str(row["gender"]).upper()
            mapping[(course, distance, stroke, gender)] = row["id"]
        return cls(mapping)

    def resolve_individual(self, course: str, distance: int, stroke: str, gender: str) -> Optional[str]:
        return self.mapping.get((course, distance, stroke, gender))

    def resolve_relay(self, course: str, leg_distance: int, stroke_kind: str, gender: str) -> Optional[str]:
        key = (course, 4, f"{leg_distance}_{stroke_kind}", gender)
        return self.mapping.get(key)


# --------------------------------------------------------------------------- #
# Sheet processing
# --------------------------------------------------------------------------- #


def process_sheet(
    sheet_name: str,
    df: pd.DataFrame,
    meet_info: Dict[str, Any],
    athlete_index: AthleteIndex,
    club_index: ClubIndex,
    event_index: EventIndex,
    collector: ValidationCollector,
) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], Optional[str], Dict[str, int], Dict[str, List[str]]]:
    results: List[Dict[str, Any]] = []
    sheet_meet_name: Optional[str] = None
    sheet_meet_date: Optional[str] = None
    sheet_meet_city: Optional[str] = None
    
    # Early return if dataframe is empty or has no data rows
    if df.empty or len(df) <= 2:  # 2 rows = header + maybe one data row, but we need at least header + 2 data rows
        empty_skip_reasons = {
            "no_fullname": 0,
            "no_course": 0,
            "no_gender": 0,
            "no_event": 0,
            "no_athlete": 0,
            "no_time": 0,
            "nation_mismatch": 0,
        }
        empty_skip_details = {k: [] for k in empty_skip_reasons.keys()}
        return results, sheet_meet_name, sheet_meet_date, sheet_meet_city, empty_skip_reasons, empty_skip_details

    total_rows = len(df) - 2  # Subtract header rows
    progress_interval = max(1, total_rows // 10) if total_rows > 50 else 100  # Print every 10% for large sheets
    
    # Track skip reasons for debugging
    skip_reasons = {
        "no_fullname": 0,
        "no_course": 0,
        "no_gender": 0,
        "no_event": 0,
        "no_athlete": 0,
        "no_time": 0,
        "nation_mismatch": 0,
    }
    
    # Track skipped row details (first 10 of each type for debugging)
    skipped_rows_details = {
        "no_fullname": [],
        "no_course": [],
        "no_gender": [],
        "no_event": [],
        "no_athlete": [],
        "no_time": [],
        "nation_mismatch": [],
    }

    for row_idx in range(2, len(df)):
        try:
            row = df.iloc[row_idx]
            excel_row = row_idx + 1
            
            # Debug: Print first 3 data rows to see what's being extracted
            if row_idx <= 4:  # First 3 data rows (indices 2, 3, 4)
                full_name_debug = as_clean_str(get_value(row, "FULLNAME"))
                course_debug = get_value(row, "COURSE")
                print(f"    [DEBUG] Row {excel_row}: FULLNAME='{full_name_debug}', COURSE='{course_debug}'", flush=True)
            
            # Progress indicator for large sheets
            if total_rows > 50 and (row_idx - 2) % progress_interval == 0:
                processed = row_idx - 1
                skipped_so_far = sum(skip_reasons.values())
                print(f"    [Sheet Progress] Row {processed}/{total_rows} ({100*processed//total_rows}%) - Found {len(results)} results, Skipped: {skipped_so_far}", flush=True)

            full_name = as_clean_str(get_value(row, "FULLNAME"))
            
            if not full_name:
                skip_reasons["no_fullname"] += 1
                if len(skipped_rows_details["no_fullname"]) < 10:
                    skipped_rows_details["no_fullname"].append(f"Row {excel_row}: Empty FULLNAME")
                continue

            course = parse_course(get_value(row, "COURSE"))
            if not course:
                skip_reasons["no_course"] += 1
                course_raw = as_clean_str(get_value(row, "COURSE"))
                if len(skipped_rows_details["no_course"]) < 10:
                    skipped_rows_details["no_course"].append(f"Row {excel_row}: {full_name} - Course: '{course_raw}'")
                collector.add_course_error(sheet_name, excel_row, full_name, course_raw)
                continue

            gender = parse_gender(get_value(row, "GENDER"))
            if not gender:
                skip_reasons["no_gender"] += 1
                gender_raw = as_clean_str(get_value(row, "GENDER"))
                if len(skipped_rows_details["no_gender"]) < 10:
                    skipped_rows_details["no_gender"].append(f"Row {excel_row}: {full_name} - Gender: '{gender_raw}'")
                collector.add_general_error(sheet_name, excel_row, f"Unable to parse gender for '{full_name}'.")
                continue

            distance_value = get_value(row, "DISTANCE")
            stroke_value = get_value(row, "STROKE")
            relay_meta = detect_relay(distance_value, stroke_value, sheet_name)

            event_id: Optional[str] = None
            distance_int: Optional[int] = None
            stroke_name: Optional[str] = None

            if relay_meta:
                # Silently skip relays - no age group data available for proper results table entry
                # TODO: Add relay support later when age group handling is implemented
                skip_reasons["no_event"] += 1
                continue
            else:
                distance_text = as_clean_str(distance_value)
                if not distance_text:
                    skip_reasons["no_event"] += 1
                    if len(skipped_rows_details["no_event"]) < 10:
                        skipped_rows_details["no_event"].append(f"Row {excel_row}: {full_name} - Missing distance")
                    collector.add_event_missing(sheet_name, excel_row, f"{course} event missing distance for {full_name}.")
                    continue
                try:
                    distance_int = int(float(distance_text))
                except ValueError:
                    skip_reasons["no_event"] += 1
                    if len(skipped_rows_details["no_event"]) < 10:
                        skipped_rows_details["no_event"].append(f"Row {excel_row}: {full_name} - Invalid distance: '{distance_text}'")
                    collector.add_event_missing(sheet_name, excel_row, f"Invalid distance '{distance_text}' for {full_name}.")
                    continue
                stroke_symbol = as_clean_str(stroke_value).upper()
                stroke_name = STROKE_MAP.get(stroke_symbol)
                if not stroke_name:
                    skip_reasons["no_event"] += 1
                    if len(skipped_rows_details["no_event"]) < 10:
                        skipped_rows_details["no_event"].append(f"Row {excel_row}: {full_name} - Unknown stroke: '{stroke_symbol}'")
                    collector.add_event_missing(sheet_name, excel_row, f"Unknown stroke '{stroke_symbol}' for {full_name}.")
                    continue
                if stroke_name == "IM" and distance_int == 100 and course != "SCM":
                    skip_reasons["no_event"] += 1
                    if len(skipped_rows_details["no_event"]) < 10:
                        skipped_rows_details["no_event"].append(f"Row {excel_row}: {full_name} - 100 IM only for SCM (found {course})")
                    collector.add_event_missing(
                        sheet_name,
                        excel_row,
                        f"100 IM only accepted for SCM (row shows {course}).",
                    )
                    continue
                event_id = event_index.resolve_individual(course, distance_int, stroke_name, gender)
                if not event_id:
                    skip_reasons["no_event"] += 1
                    event_desc = f"{course} {distance_int}m {stroke_name} {gender}"
                    if len(skipped_rows_details["no_event"]) < 10:
                        skipped_rows_details["no_event"].append(f"Row {excel_row}: {full_name} - Event: {event_desc}")
                    collector.add_event_missing(sheet_name, excel_row, event_desc)
                    continue

            if not event_id:
                continue

            meet_name_cell = as_clean_str(get_value(row, "MEETNAME"))
            # MEETNAME is always populated per row by design
            if meet_name_cell and not sheet_meet_name:
                sheet_meet_name = meet_name_cell
    
            # Get meet name for tracking validation issues - use the row's MEETNAME directly
            # This ensures validation issues are associated with the correct meet
            current_meet_name = meet_name_cell or sheet_meet_name or meet_info.get("name", "")
    
            # Debug: Track Mattioli rows early
            is_mattioli_row = 'mattioli' in meet_name_cell.lower() or 'victorian' in meet_name_cell.lower() if meet_name_cell else False

            meet_city_cell = as_clean_str(get_value(row, "MEETCITY"))
            if meet_city_cell and not sheet_meet_city:
                sheet_meet_city = meet_city_cell

            meet_date_cell = get_value(row, "MEETDATE")
            meet_date_obj = parse_excel_date(meet_date_cell)
            if not meet_date_obj and meet_info.get("meet_date"):
                meet_date_obj = parse_excel_date(meet_info.get("meet_date"))
            meet_date_str = meet_date_obj.strftime("%Y-%m-%d") if meet_date_obj else None
            if meet_date_str and not sheet_meet_date:
                sheet_meet_date = meet_date_str

            time_string = as_clean_str(get_value(row, "SWIMTIME"))
            time_numeric = parse_swimtime_numeric(get_value(row, "SWIMTIME_N"), time_string)
            if time_numeric is None:
                skip_reasons["no_time"] += 1
                time_n_raw = as_clean_str(get_value(row, "SWIMTIME_N"))
                if len(skipped_rows_details["no_time"]) < 10:
                    skipped_rows_details["no_time"].append(f"Row {excel_row}: {full_name} - Invalid time: '{time_string}' (SWIMTIME_N: '{time_n_raw}')")
                collector.add_time_error(sheet_name, excel_row, full_name, time_string, time_n_raw)
                continue

            place = parse_optional_int(get_value(row, "PLACE"))
            aqua_points = parse_optional_int(get_value(row, "PTS_FINA"))
            rudolph_points = parse_optional_float(get_value(row, "PTS_RUDOLPH"))

            club_name_value = as_clean_str(get_value(row, "CLUBNAME"))
            nation_value = as_clean_str(get_value(row, "NATION")).upper()
            birthdate_value = as_clean_str(get_value(row, "BIRTHDATE"))

            athlete_id: Optional[str] = None
            day_age: Optional[int] = None
            year_age: Optional[int] = None
            athlete_record: Optional[AthleteRecord] = None
        
            if not relay_meta:
                # Pass meet_name to the find method so it can be tracked correctly
                if is_mattioli_row and not birthdate_value:
                    print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - WARNING: No birthdate in Excel, cannot match athlete", flush=True)
                athlete_record = athlete_index.find(full_name, birthdate_value, gender, sheet_name, excel_row, collector, current_meet_name, club_name=club_name_value)
            if not athlete_record:
                skip_reasons["no_athlete"] += 1
                # Normalize birthdate for display
                birthdate_normalized_display = normalize_birthdate(birthdate_value) if birthdate_value else "(no birthdate)"
                birthdate_str = birthdate_normalized_display if birthdate_normalized_display else "(no birthdate)"
                if len(skipped_rows_details["no_athlete"]) < 10:
                    skipped_rows_details["no_athlete"].append(f"Row {excel_row}: {full_name} - Birthdate: {birthdate_str}, Gender: {gender}")
                if is_mattioli_row:
                    print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - SKIPPED: Athlete not found (birthdate: {birthdate_str})", flush=True)
                # Continue to next row immediately
                continue

            # If clubname is "Malaysia", just set it to None/blank and continue
            # Don't try to look up athlete's club - leave it blank for now
            club_lookup_value = club_name_value
            if normalize_name(club_name_value) == normalize_name("Malaysia"):
                # Just set club to None - don't try to look up athlete's club
                club_lookup_value = None
            
            if relay_meta and not club_lookup_value:
                club_lookup_value = full_name

            # Only try to resolve club if we have a club_lookup_value (not None/blank)
            club_record = None
            if club_lookup_value:
                club_record = club_index.resolve(club_lookup_value, sheet_name, excel_row, collector)
            if not club_record:
                # Don't skip - just log a warning and continue with null club fields
                athlete_id_for_club = athlete_record.id if athlete_record else None
                current_meet_city = meet_city_cell or sheet_meet_city or meet_info.get("city", "")
                collector.add_club_missing(sheet_name, excel_row, club_lookup_value, full_name, current_meet_name, current_meet_city, athlete_id_for_club)
                if is_mattioli_row:
                    print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - WARNING: Club not found (club: {club_lookup_value}), creating result with null club fields", flush=True)
            
            # If no club_record (either because clubname was "Malaysia" or club not found), create a dummy one
            if not club_record:
                club_record = ClubRecord(
                    club_name=None,
                    club_code=None,
                    state_code=None,
                    nation=None,
                )

            if not relay_meta:
                workbook_birthdate_norm = normalize_birthdate(birthdate_value)
                athlete_birthdate_norm = normalize_birthdate(athlete_record.birthdate) if athlete_record else None
                # Check for birthdate mismatch but don't skip - name matched exactly
                # Just log it as a warning, still create the result
                if (
                workbook_birthdate_norm
                and athlete_birthdate_norm
                and workbook_birthdate_norm != athlete_birthdate_norm
            ):
                    # Debug: Check if strings are actually different (might be whitespace or encoding issue)
                    if workbook_birthdate_norm.strip() == athlete_birthdate_norm.strip():
                        print(f"    [DEBUG] Row {excel_row}: Birthdate strings appear identical but comparison failed - Excel: '{workbook_birthdate_norm}' (len={len(workbook_birthdate_norm)}), DB: '{athlete_birthdate_norm}' (len={len(athlete_birthdate_norm)})", flush=True)
                    # Check if birthdates are transposed (same year, month/day swapped)
                    if is_birthdate_transposed(workbook_birthdate_norm, athlete_birthdate_norm):
                        # Auto-update: use Excel birthdate (results data is authoritative)
                        if athlete_record:
                            collector.add_birthdate_update(athlete_record.id, workbook_birthdate_norm, athlete_birthdate_norm, sheet_name, excel_row, current_meet_name)
                        if is_mattioli_row:
                            print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - Birthdate transposed - will auto-update (Excel: {workbook_birthdate_norm}, DB: {athlete_birthdate_norm})", flush=True)
                    elif should_use_excel_day(workbook_birthdate_norm, athlete_birthdate_norm):
                        # Name, year, and month match - use Excel day (results data is authoritative)
                        if athlete_record:
                            collector.add_birthdate_update(athlete_record.id, workbook_birthdate_norm, athlete_birthdate_norm, sheet_name, excel_row, current_meet_name)
                        if is_mattioli_row:
                            print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - Birthdate day difference (year/month match) - will auto-update day (Excel: {workbook_birthdate_norm}, DB: {athlete_birthdate_norm})", flush=True)
                    elif should_use_excel_birthdate_when_year_matches(workbook_birthdate_norm, athlete_birthdate_norm):
                        # Year matches (name already matched) - use Excel birthdate (results data is authoritative)
                        # This handles cases where exact name match but month/day differ
                        if athlete_record:
                            collector.add_birthdate_update(athlete_record.id, workbook_birthdate_norm, athlete_birthdate_norm, sheet_name, excel_row, current_meet_name)
                        if is_mattioli_row:
                            print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - Birthdate difference (year matches, month/day differ) - will auto-update (Excel: {workbook_birthdate_norm}, DB: {athlete_birthdate_norm})", flush=True)
                    else:
                        # Not transposed and not just day difference - report as mismatch
                        if is_mattioli_row:
                            print(f"[MATTIOLI DEBUG] Row {excel_row} ({full_name}) - Birthdate mismatch WARNING (Excel: {workbook_birthdate_norm}, DB: {athlete_birthdate_norm}) - but continuing anyway since name matched", flush=True)
                        collector.add_birthdate_mismatch(
                            sheet_name, excel_row, full_name, workbook_birthdate_norm, athlete_birthdate_norm, current_meet_name, athlete_record.id if athlete_record else None
                        )
                # Don't continue - proceed to create the result anyway since name matched
                # Track nation update if needed (before creating result dict)
                nation_update_new = None
            if nation_value and athlete_record.nation and nation_value != athlete_record.nation:
                    # Nation mismatch: Trust Excel if it's non-MAS, update athlete's nation
                    if nation_value != "MAS" and athlete_record.nation == "MAS":
                        # Excel says non-MAS, DB says MAS - trust Excel and update athlete
                        nation_update_new = nation_value
                        print(f"    [NATION] Row {excel_row}: {full_name} - Will update nation from '{athlete_record.nation}' to '{nation_value}' (Excel non-MAS)", flush=True)
                        # Continue processing - don't skip the row
                    else:
                        # Other mismatch (Excel=MAS but DB=non-MAS, or both non-MAS but different)
                        # Track but don't update automatically - needs manual review
                        skip_reasons["nation_mismatch"] += 1
                        if len(skipped_rows_details["nation_mismatch"]) < 10:
                            skipped_rows_details["nation_mismatch"].append(f"Row {excel_row}: {full_name} - Excel: '{nation_value}', DB: '{athlete_record.nation}' (needs manual review)")
                    # Track the mismatch for all cases
                    collector.add_nation_mismatch(
                        sheet_name,
                        excel_row,
                        full_name,
                        nation_value,
                        athlete_record.nation,
                        athlete_record.id,
                    )
            if nation_value and not athlete_record.nation:
                collector.add_nation_mismatch(
                    sheet_name,
                    excel_row,
                    full_name,
                    nation_value,
                    "(blank in athlete table)",
                    athlete_record.id if athlete_record else None,
                )
                continue
            athlete_id = athlete_record.id
            birthdate_for_age = normalize_birthdate(athlete_record.birthdate) or normalize_birthdate(
                birthdate_value
            )
            if birthdate_for_age and meet_date_obj:
                day_age, year_age = compute_ages(birthdate_for_age, meet_date_obj)

            result = {
                "id": str(uuid.uuid4()),
                "athlete_id": athlete_id,
                "event_id": event_id,
                "time_seconds": time_numeric,
                "time_string": time_string,
                "place": place,
                "aqua_points": aqua_points,
                "rudolph_points": rudolph_points,
                "course": course,
                "result_meet_date": meet_date_str or meet_info.get("meet_date"),
                # MEETNAME is always populated per row by design - use it directly
                "meet_name": meet_name_cell or sheet_meet_name or meet_info.get("name"),
                # Debug flag for Mattioli
                "_is_mattioli_row": is_mattioli_row,
                "meet_city": meet_city_cell or sheet_meet_city or meet_info.get("city"),
                "day_age": day_age,
                "year_age": year_age,
                "team_name": club_record.club_name if club_record else None,
                "team_code": club_record.club_code if club_record else None,
                "team_state_code": club_record.state_code if club_record else None,
                "team_nation": club_record.nation if club_record else None,
                "is_relay": 1 if relay_meta else 0,
                # Tracking fields for skipped row reporting
                "sheet_name": sheet_name,
                "excel_row": excel_row,
                "full_name": full_name,
                "workbook_birthdate": workbook_birthdate_norm if not relay_meta else None,  # Store Excel birthdate for auditing
            }
            
            # Store nation update info in result if needed
            if nation_update_new:
                result['_nation_update'] = nation_update_new
                result['_nation_update_athlete_id'] = athlete_id
                result['_nation_update_old'] = athlete_record.nation
            
            results.append(result)
        except Exception as e:
            # Catch any exceptions during row processing and log them
            print(f"    [ERROR] Row {excel_row if 'excel_row' in locals() else row_idx+1}: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            continue  # Continue to next row even if this one fails
            
    return results, sheet_meet_name, sheet_meet_date, sheet_meet_city, skip_reasons, skipped_rows_details


# --------------------------------------------------------------------------- #
# Conversion entry point
# --------------------------------------------------------------------------- #


def process_meet_file_simple(file_path: Path, meet_info: Dict[str, Any], sheet_filter: Optional[List[str]] = None):
    """Read an Excel workbook and return (athlete_refs, results, event_refs).

    Args:
        file_path: Path to Excel file
        meet_info: Meet metadata dict
        sheet_filter: Optional list of sheet names to process (for debugging).
                     If None, processes all sheets.
                     TEMPORARY: Remove this constraint after debugging is complete.
    """
    # print(f"Processing: {file_path.name}")  # Removed to reduce noise

    collector = ValidationCollector()

    conn = get_database_connection()
    try:
        # print(f"\n[process_meet_file_simple] Loading indexes for {file_path.name}...")  # Removed to reduce noise
        athlete_index = AthleteIndex.from_connection(conn)
        # print(f"[process_meet_file_simple] AthleteIndex loaded, total keys in index: {len(athlete_index.by_name)}")  # Removed to reduce noise
        club_index = ClubIndex.from_connection(conn)
        event_index = EventIndex.from_connection(conn)
    finally:
        conn.close()

    excel_engine = "xlrd" if file_path.suffix.lower() == ".xls" else None
    excel = pd.ExcelFile(file_path, engine=excel_engine)

    all_results: List[Dict[str, Any]] = []
    used_athletes: Set[str] = set()
    used_events: Set[str] = set()
    meet_name_candidates: List[str] = []
    meet_date_candidates: List[str] = []
    meet_city_candidates: List[str] = []
    # Skip sheets: LAP (lap times), TOP (top results), 4X (relays), 5000 (open water)
    # Note: Relays skipped for now - no age group data available for proper results table entry
    skip_patterns = ["LAP", "TOP", "4X", "5000"]

    # Apply sheet filter if provided (TEMPORARY for debugging)
    sheets_to_process = excel.sheet_names
    if sheet_filter:
        sheets_to_process = [s for s in excel.sheet_names if s in sheet_filter]
        print(f"[PARSE] DEBUG MODE: Only processing sheets: {sheet_filter}", flush=True)

    total_sheets = len([s for s in sheets_to_process if s.strip() and not any(p in "".join(as_clean_str(s).upper().split()) for p in skip_patterns)])
    sheet_num = 0

    for sheet_name in sheets_to_process:
        normalized_name = "".join(as_clean_str(sheet_name).upper().split())
        if not sheet_name.strip():
            continue
        if any(p in normalized_name for p in skip_patterns):
            continue

        sheet_num += 1
        print(f"[PARSE] Processing sheet {sheet_num}/{total_sheets}: '{sheet_name}'...", flush=True)

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None,
            usecols=USECOLS,
            engine=excel_engine,
        )
        
        # Debug: Print first few rows to understand file structure
        if sheet_name == '50m Fr':  # Only for first sheet to avoid spam
            print(f"    [DEBUG] Sheet '{sheet_name}' shape: {df.shape}", flush=True)
            print(f"    [DEBUG] First 3 rows of data:", flush=True)
            for i in range(min(3, len(df))):
                print(f"    [DEBUG]   Row {i}: {df.iloc[i].tolist()}", flush=True)

        results, sheet_meet_name, sheet_meet_date, sheet_meet_city, skip_reasons, skipped_rows_details = process_sheet(
            sheet_name,
            df,
            meet_info,
            athlete_index,
            club_index,
            event_index,
            collector,
        )

        for result in results:
            if result.get("athlete_id"):
                used_athletes.add(result["athlete_id"])
            if result.get("event_id"):
                used_events.add(result["event_id"])

        all_results.extend(results)
        skipped_total = sum(skip_reasons.values())
        print(f"[PARSE]   ✓ Sheet '{sheet_name}': {len(results)} results found, {skipped_total} rows skipped", flush=True)
        if skipped_total > 0:
            skip_details = ", ".join([f"{k}: {v}" for k, v in skip_reasons.items() if v > 0])
            print(f"[PARSE]     Skip breakdown: {skip_details}", flush=True)
            
            # Show detailed examples of skipped rows
            for skip_type, details_list in skipped_rows_details.items():
                if details_list and skip_reasons.get(skip_type, 0) > 0:
                    print(f"[PARSE]     Examples of '{skip_type}' skips (showing {len(details_list)} of {skip_reasons[skip_type]}):", flush=True)
                    for detail in details_list:
                        print(f"[PARSE]       - {detail}", flush=True)

        if sheet_meet_name:
            meet_name_candidates.append(sheet_meet_name)
        if sheet_meet_date:
            meet_date_candidates.append(sheet_meet_date)
        if sheet_meet_city:
            meet_city_candidates.append(sheet_meet_city)

    # Don't raise on validation errors - continue processing and report issues in summary
    # collector.raise_if_errors()  # Commented out to allow processing to continue

    if meet_name_candidates:
        meet_info["name"] = meet_name_candidates[0]
    if meet_date_candidates:
        meet_date_candidates.sort()
        meet_info["meet_date"] = meet_date_candidates[0]
    if meet_city_candidates and not meet_info.get("city"):
        meet_info["city"] = meet_city_candidates[0]

    athlete_refs = [{"id": aid, "existing": True} for aid in sorted(used_athletes)]
    event_refs = [{"id": eid, "existing": True} for eid in sorted(used_events)]

    # Return validation collector so issues can be reported (but don't raise)
    return athlete_refs, all_results, event_refs, collector


# --------------------------------------------------------------------------- #
# Database interaction helpers
# --------------------------------------------------------------------------- #


def get_database_connection():
    """
    Get database connection with WAL mode enabled and timeout.
    WAL mode allows concurrent reads while writes are happening.
    
    IMPORTANT: Always use this in a try/finally block or context manager
    to ensure connections are closed:
    
        conn = get_database_connection()
        try:
            # use conn
        finally:
            conn.close()
    """
    project_root = Path(__file__).parent.parent
    db_path = project_root / "malaysia_swimming.db"
    
    # Try to connect with WAL mode - this allows concurrent access
    conn = sqlite3.connect(
        str(db_path), 
        timeout=30.0,  # Wait up to 30 seconds for lock to clear
        check_same_thread=False  # Allow connections from different threads
    )
    
    # Enable WAL mode for better concurrency (allows readers while writer is active)
    conn.execute("PRAGMA journal_mode=WAL")
    # Set busy timeout (how long to wait if database is locked)
    conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds
    # Set synchronous mode to NORMAL for better performance with WAL
    conn.execute("PRAGMA synchronous=NORMAL")
    
    return conn


def insert_data_simple(conn, athletes, results, events, meet_info, collector=None):
    """Insert the prepared results into SQLite (athletes/events lists mark existing rows).
    
    Args:
        conn: Database connection
        athletes: List of athlete references
        results: List of result dictionaries (each should have sheet_name, excel_row, full_name for tracking)
        events: List of event references
        meet_info: Meet information dictionary
        collector: Optional ValidationCollector to track skipped rows
    """
    cursor = conn.cursor()
    
    columns_to_add = [
        ("day_age", "INTEGER"),
        ("year_age", "INTEGER"),
        ("result_meet_date", "TEXT"),
        ("aqua_points", "INTEGER"),
        ("rudolph_points", "REAL"),
        ("team_name", "TEXT"),
        ("team_code", "TEXT"),
        ("team_state_code", "TEXT"),
        ("team_nation", "TEXT"),
        ("is_relay", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE results ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_unique ON results(meet_id, event_id, athlete_id)"
        )
    except sqlite3.OperationalError:
        pass

    cursor.execute(
        """
        INSERT OR IGNORE INTO meets (id, name, meet_type, meet_date, location, city)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            meet_info["id"],
            meet_info.get("name", ""),
            meet_info.get("meet_type"),
            meet_info.get("meet_date"),
            meet_info.get("location"),
            meet_info.get("city"),
        ),
    )

    athlete_id_map: Dict[str, str] = {}
    event_id_map: Dict[str, str] = {}

    for athlete in athletes:
        old_id = athlete.get("id")
        if not old_id:
            continue
        athlete_id_map[old_id] = old_id

    for event in events:
        old_id = event.get("id")
        if not old_id:
            continue
        event_id_map[old_id] = old_id

    existing_athlete_ids = {r.get("athlete_id") for r in results if r.get("athlete_id")}
    for athlete_id in existing_athlete_ids:
        if not athlete_id or athlete_id in athlete_id_map:
            continue
        cursor.execute("SELECT 1 FROM athletes WHERE id = ? LIMIT 1", (athlete_id,))
        if cursor.fetchone():
            athlete_id_map[athlete_id] = athlete_id

    existing_event_ids = {r.get("event_id") for r in results if r.get("event_id")}
    for event_id in existing_event_ids:
        if not event_id or event_id in event_id_map:
            continue
        cursor.execute("SELECT 1 FROM events WHERE id = ? LIMIT 1", (event_id,))
        if cursor.fetchone():
            event_id_map[event_id] = event_id

    inserted = 0
    skipped = 0
    total_results = len(results)
    
    # OPTIMIZATION: Load all existing results for this meet in ONE query instead of checking each row
    # This dramatically speeds up duplicate checking for large batches
    # Get meet_id from meet_info (all results should have the same meet_id)
    meet_id = meet_info.get("id")
    meet_name = meet_info.get("name", "Unknown")
    existing_results_set = set()
    if meet_id and results:
        print(f"    [DB] Loading existing results for meet {meet_id} ('{meet_name}')...", flush=True)
        cursor.execute("""
            SELECT event_id, athlete_id 
            FROM results 
            WHERE meet_id = ?
        """, (meet_id,))
        for row in cursor.fetchall():
            event_id = row[0]
            athlete_id = row[1]
            # Use tuple (event_id, athlete_id) as key, handling NULL athlete_id
            key = (event_id, athlete_id if athlete_id else None)
            existing_results_set.add(key)
        print(f"    [DB] Found {len(existing_results_set)} existing results to check against for meet '{meet_name}' (ID: {meet_id})", flush=True)
        if len(existing_results_set) > 0:
            print(f"    [DB] WARNING: Meet '{meet_name}' already has {len(existing_results_set)} results in database. New results with same (event_id, athlete_id) will be skipped as duplicates.", flush=True)
    
    # Progress tracking
    progress_interval = max(1, total_results // 10) if total_results > 0 else 1  # Print every 10%
    
    # Prepare batch insert data
    batch_inserts = []
    
    for idx, result in enumerate(results, 1):
        # Print progress for large batches
        if total_results > 50 and idx % progress_interval == 0:
            print(f"    [Progress] {idx}/{total_results} ({100*idx//total_results}%) - Inserted: {inserted}, Skipped: {skipped}", flush=True)
        sheet_name = result.get("sheet_name", "Unknown")
        excel_row = result.get("excel_row", 0)
        full_name = result.get("full_name", result.get("athlete_name", "Unknown"))
        
        original_athlete_id = result.get("athlete_id")
        original_event_id = result.get("event_id")
        if original_athlete_id:
            resolved_athlete_id = athlete_id_map.get(original_athlete_id)
            if not resolved_athlete_id:
                skipped += 1
                if collector:
                    collector.add_skipped_row(sheet_name, excel_row, full_name, "Athlete not in athlete table")
                continue
            result["athlete_id"] = resolved_athlete_id
        if original_event_id:
            resolved_event_id = event_id_map.get(original_event_id)
            if not resolved_event_id:
                skipped += 1
                if collector:
                    collector.add_skipped_row(sheet_name, excel_row, full_name, "Event not found")
                continue
            result["event_id"] = resolved_event_id

        numeric_time = result.get("time_seconds")
        time_string = result.get("time_string")
        result_meet_id = result.get("meet_id")
        if not result.get("event_id") or not result_meet_id:
            skipped += 1
            if collector:
                collector.add_skipped_row(sheet_name, excel_row, full_name, "Missing event_id or meet_id")
            continue

        athlete_id_for_query = result.get("athlete_id")
        # OPTIMIZED: Check for duplicate in memory set instead of database query
        duplicate_key = (result["event_id"], athlete_id_for_query if athlete_id_for_query else None)
        if duplicate_key in existing_results_set:
            skipped += 1
            if collector:
                collector.add_skipped_row(sheet_name, excel_row, full_name, "Duplicate result row")
            continue
        
        # Add to existing set to prevent duplicates within this batch
        existing_results_set.add(duplicate_key)
        
        # Collect data for batch insert
        batch_inserts.append((
            result["id"],
            result_meet_id,
            result.get("athlete_id"),
            result["event_id"],
            result.get("time_seconds"),
            time_string,
            numeric_time,
            result.get("place"),
            result.get("aqua_points"),
            result.get("rudolph_points"),
            result.get("course"),
            result.get("result_meet_date"),
            result.get("day_age"),
            result.get("year_age"),
            result.get("team_name"),
            result.get("team_code"),
            result.get("team_state_code"),
            result.get("team_nation"),
            result.get("is_relay", 0),
            result.get("workbook_birthdate"),  # Store Excel birthdate for auditing
        ))
        inserted += 1
    
    # OPTIMIZATION: Batch insert all results at once instead of one-by-one
    if batch_inserts:
        print(f"    [DB] Batch inserting {len(batch_inserts)} results...", flush=True)
        cursor.executemany(
            """
            INSERT INTO results (
                id,
                meet_id,
                athlete_id,
                event_id,
                time_seconds,
                time_string,
                place,
                aqua_points,
                rudolph_points,
                course,
                result_meet_date,
                day_age,
                year_age,
                team_name,
                team_code,
                team_state_code,
                team_nation,
                is_relay,
                workbook_birthdate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch_inserts,
        )
        print(f"    [DB] Batch insert complete", flush=True)
    
    # Apply FULLNAME updates (results FULLNAME overwrites registration FULLNAME)
    # IMPORTANT: Preserve old FULLNAME in alias field before updating
    fullname_updates_applied = 0
    if collector and hasattr(collector, 'fullname_updates') and collector.fullname_updates:
        # Deduplicate by athlete_id (only keep latest update per athlete, but preserve old_fullname)
        updates_by_athlete = {}
        old_names_by_athlete = {}
        for update in collector.fullname_updates:
            athlete_id = update.get("athlete_id")
            new_fullname = update.get("new_fullname")
            old_fullname = update.get("old_fullname")
            if athlete_id and new_fullname:
                updates_by_athlete[athlete_id] = new_fullname
                # Keep the first old_fullname we see (original registration name)
                if athlete_id not in old_names_by_athlete:
                    old_names_by_athlete[athlete_id] = old_fullname
        
        # Check which alias columns exist
        cursor.execute("PRAGMA table_info(athletes)")
        columns_info = cursor.fetchall()
        columns = {row[1].lower() for row in columns_info}
        has_alias_1 = "athlete_alias_1" in columns
        has_alias_2 = "athlete_alias_2" in columns
        
        for athlete_id, new_fullname in updates_by_athlete.items():
            try:
                old_fullname = old_names_by_athlete.get(athlete_id)
                
                # First, preserve old FULLNAME in alias field if it's not already there
                if old_fullname and old_fullname != new_fullname:
                    # Check current alias values (only if columns exist)
                    current_alias_1 = None
                    current_alias_2 = None
                    if has_alias_1 or has_alias_2:
                        select_cols = []
                        if has_alias_1:
                            select_cols.append("athlete_alias_1")
                        if has_alias_2:
                            select_cols.append("athlete_alias_2")
                        if select_cols:
                            cursor.execute(f"SELECT {', '.join(select_cols)} FROM athletes WHERE id = ?", (athlete_id,))
                            row = cursor.fetchone()
                            if row:
                                idx = 0
                                if has_alias_1:
                                    current_alias_1 = row[idx]
                                    idx += 1
                                if has_alias_2:
                                    current_alias_2 = row[idx] if len(row) > idx else None
                    
                    # Check if old_fullname is already in an alias field
                    old_in_alias = (current_alias_1 and normalize_name(current_alias_1) == normalize_name(old_fullname)) or \
                                   (current_alias_2 and normalize_name(current_alias_2) == normalize_name(old_fullname))
                    
                    if not old_in_alias:
                        # Store old name in an available alias field
                        if has_alias_1 and not current_alias_1:
                            # Use alias_1 if available
                            cursor.execute("UPDATE athletes SET athlete_alias_1 = ? WHERE id = ?", (old_fullname, athlete_id))
                            print(f"    [DB] Stored old FULLNAME '{old_fullname}' in athlete_alias_1 for athlete {athlete_id}", flush=True)
                        elif has_alias_2 and not current_alias_2:
                            # Use alias_2 if alias_1 is taken
                            cursor.execute("UPDATE athletes SET athlete_alias_2 = ? WHERE id = ?", (old_fullname, athlete_id))
                            print(f"    [DB] Stored old FULLNAME '{old_fullname}' in athlete_alias_2 for athlete {athlete_id}", flush=True)
                        elif has_alias_1:
                            # Both aliases are taken, but we'll still update FULLNAME
                            print(f"    [DB] WARNING: Both alias fields are full for athlete {athlete_id}, cannot preserve old name '{old_fullname}'", flush=True)
                
                # Now update FULLNAME to results format (only if different)
                if old_fullname != new_fullname:
                    cursor.execute("UPDATE athletes SET FULLNAME = ? WHERE id = ?", (new_fullname, athlete_id))
                    fullname_updates_applied += 1
                    print(f"    [DB] Updated athlete {athlete_id} FULLNAME from '{old_fullname}' to '{new_fullname}'", flush=True)
                else:
                    # Names are the same, no update needed
                    print(f"    [DB] Skipped FULLNAME update for athlete {athlete_id} (already '{new_fullname}')", flush=True)
            except Exception as e:
                if collector:
                    collector.add_general_error("FULLNAME Update", 0, f"Error updating {athlete_id}: {e}")
    
    # Apply birthdate updates (transposed birthdates - use results birthdate)
    birthdate_updates_applied = 0
    if collector and hasattr(collector, 'birthdate_updates') and collector.birthdate_updates:
        # Deduplicate by athlete_id (only keep latest update per athlete)
        updates_by_athlete = {}
        for update in collector.birthdate_updates:
            athlete_id = update.get("athlete_id")
            new_birthdate = update.get("new_birthdate")
            if athlete_id and new_birthdate:
                updates_by_athlete[athlete_id] = new_birthdate
        
        for athlete_id, new_birthdate in updates_by_athlete.items():
            try:
                # Update birthdate
                cursor.execute("UPDATE athletes SET BIRTHDATE = ? WHERE id = ?", (new_birthdate, athlete_id))
                birthdate_updates_applied += 1
                print(f"    [DB] Updated athlete {athlete_id} BIRTHDATE to '{new_birthdate}' (transposed date corrected)", flush=True)
            except Exception as e:
                conn.rollback()
                print(f"    [DB] ERROR updating BIRTHDATE for athlete {athlete_id}: {e}", flush=True)
    
    # Apply NATION updates (trust Excel if non-MAS, update athlete's nation)
    nation_updates_applied = 0
    nation_updates_by_athlete = {}
    for result in results:
        if result.get('_nation_update') and result.get('_nation_update_athlete_id'):
            athlete_id = result['_nation_update_athlete_id']
            new_nation = result['_nation_update']
            # Keep latest update per athlete
            nation_updates_by_athlete[athlete_id] = new_nation
    
    for athlete_id, new_nation in nation_updates_by_athlete.items():
        try:
            cursor.execute("UPDATE athletes SET NATION = ? WHERE id = ?", (new_nation, athlete_id))
            nation_updates_applied += 1
            print(f"    [DB] Updated athlete {athlete_id} nation to '{new_nation}'", flush=True)
        except Exception as e:
            if collector:
                collector.add_general_error("NATION Update", 0, f"Error updating athlete {athlete_id} nation to {new_nation}: {e}")
    
    conn.commit()
    
    # Final summary for this batch
    if total_results > 0:
        print(f"    [Complete] Inserted: {inserted}, Skipped: {skipped}, Total processed: {total_results}")
    
    return {
        "inserted_results": inserted, 
        "skipped_results": skipped,
        "fullname_updates_applied": fullname_updates_applied,
        "birthdate_updates_applied": birthdate_updates_applied
    }


# --------------------------------------------------------------------------- #
# Compatibility stubs (legacy callers expect these helpers)
# --------------------------------------------------------------------------- #


def load_club_mapping() -> Dict[str, str]:
    """Legacy helper – retained for compatibility, returns empty mapping."""
    return {}


def load_athleteinfo_lookup() -> Dict[str, Tuple[str, str, str]]:
    """Legacy helper – retained for compatibility, returns empty lookup."""
    return {}


# --------------------------------------------------------------------------- #
# CLI smoke test
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    test_file = Path("data/meets/SUKMA_2024_Men.xls")
    if test_file.exists():
        print(f"Testing with: {test_file}")
        result = process_meet_file_simple(test_file, {"id": "test_meet", "name": "Test Meet"})
        print(f"Result: {result}")
    else:
        print(f"Test file not found: {test_file}")

