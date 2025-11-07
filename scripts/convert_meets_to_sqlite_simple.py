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


@dataclass
class ClubRecord:
    club_name: str
    club_code: Optional[str]
    state_code: Optional[str]
    nation: Optional[str]


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
        self.nation_mismatches: List[Dict[str, str]] = []
        self.gender_mismatches: List[Dict[str, str]] = []
        self.club_misses: List[Dict[str, str]] = []
        self.event_misses: List[Dict[str, str]] = []
        self.time_errors: List[Dict[str, str]] = []
        self.course_errors: List[Dict[str, str]] = []
        self.general_errors: List[Dict[str, str]] = []

    # ---- collection helpers ------------------------------------------------ #

    def add_missing_athlete(
        self, sheet: str, row: int, full_name: str, birthdate: str, gender: str
    ) -> None:
        self.missing_athletes.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "birthdate": birthdate or "(blank)",
                "gender": gender or "(blank)",
            }
        )

    def add_birthdate_mismatch(
        self,
        sheet: str,
        row: int,
        full_name: str,
        workbook_birthdate: str,
        database_birthdate: str,
    ) -> None:
        self.birthdate_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "workbook_birthdate": workbook_birthdate or "(blank)",
                "database_birthdate": database_birthdate or "(blank)",
            }
        )

    def add_nation_mismatch(
        self, sheet: str, row: int, full_name: str, workbook_nation: str, database_nation: str
    ) -> None:
        self.nation_mismatches.append(
            {
                "sheet": sheet,
                "row": str(row),
                "full_name": full_name,
                "workbook_nation": workbook_nation or "(blank)",
                "database_nation": database_nation or "(blank)",
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

    def add_club_missing(self, sheet: str, row: int, club_name: str) -> None:
        self.club_misses.append(
            {
                "sheet": sheet,
                "row": str(row),
                "club_name": club_name or "(blank)",
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

    # ---- aggregation ------------------------------------------------------- #

    def has_errors(self) -> bool:
        return any(
            (
                self.missing_athletes,
                self.birthdate_mismatches,
                self.nation_mismatches,
                self.gender_mismatches,
                self.club_misses,
                self.event_misses,
                self.time_errors,
                self.course_errors,
                self.general_errors,
            )
        )

    def summary(self) -> str:
        if not self.has_errors():
            return ""

        def _line(label: str, items: List[Any]) -> str:
            return f"- {label}: {len(items)} issue(s)"

        lines = ["Conversion halted due to data validation issues."]
        if self.missing_athletes:
            lines.append(_line("Missing athletes", self.missing_athletes))
        if self.birthdate_mismatches:
            lines.append(_line("Birthdate mismatches", self.birthdate_mismatches))
        if self.nation_mismatches:
            lines.append(_line("Nation mismatches", self.nation_mismatches))
        if self.gender_mismatches:
            lines.append(_line("Gender mismatches", self.gender_mismatches))
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
        lines.append("Review the detailed payload, correct the data, and retry the upload.")
        return "\n".join(lines)

    def payload(self) -> Dict[str, List[Dict[str, str]]]:
        return {
            "missing_athletes": self.missing_athletes,
            "birthdate_mismatches": self.birthdate_mismatches,
            "nation_mismatches": self.nation_mismatches,
            "gender_mismatches": self.gender_mismatches,
            "club_misses": self.club_misses,
            "event_misses": self.event_misses,
            "time_errors": self.time_errors,
            "course_errors": self.course_errors,
            "general_errors": self.general_errors,
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


def normalize_birthdate(value: Any) -> str:
    dt = parse_excel_date(value)
    if not dt:
        text = "".join(ch for ch in as_clean_str(value) if ch.isdigit())
        if len(text) == 8:
            return f"{text[:4]}.{text[4:6]}.{text[6:]}"
        return ""
    return dt.strftime("%Y.%m.%d")


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


class AthleteIndex:
    def __init__(self, records: List[AthleteRecord]):
        self.by_name: Dict[str, List[AthleteRecord]] = {}
        for record in records:
            key = normalize_name(record.full_name)
            if key:
                self.by_name.setdefault(key, []).append(record)

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "AthleteIndex":
        columns = {row[1].lower() for row in conn.execute("PRAGMA table_info(athletes)")}
        select_cols = ["id", "FULLNAME", "BIRTHDATE", "NATION"]
        gender_present = "gender" in columns
        if gender_present:
            select_cols.append("GENDER")
        query = f"SELECT {', '.join(select_cols)} FROM athletes"
        df = pd.read_sql_query(query, conn)
        records: List[AthleteRecord] = []
        for _, row in df.iterrows():
            gender_value = row.get("GENDER") if gender_present else None
            records.append(
                AthleteRecord(
                    id=str(row["id"]),
                    full_name=str(row["FULLNAME"] or ""),
                    birthdate=normalize_birthdate(row["BIRTHDATE"]),
                    nation=as_clean_str(row["NATION"]).upper(),
                    gender=as_clean_str(gender_value).upper() or None,
                )
            )
        return cls(records)

    def find(
        self,
        full_name: str,
        birthdate: str,
        gender: Optional[str],
        sheet: str,
        row: int,
        collector: ValidationCollector,
    ) -> Optional[AthleteRecord]:
        norm_name = normalize_name(full_name)
        if not norm_name:
            collector.add_general_error(sheet, row, "Blank FULLNAME encountered.")
            return None
        candidates = self.by_name.get(norm_name, [])
        normalized_birthdate = normalize_birthdate(birthdate)
        if not candidates:
            collector.add_missing_athlete(sheet, row, full_name, normalized_birthdate, gender or "")
            return None

        selected: Optional[AthleteRecord] = None
        if normalized_birthdate:
            matches = [
                c for c in candidates if normalize_birthdate(c.birthdate) == normalized_birthdate
            ]
            if len(matches) == 1:
                selected = matches[0]
            elif not matches:
                options = ", ".join(
                    sorted({normalize_birthdate(c.birthdate) or "(blank)" for c in candidates})
                )
                collector.add_birthdate_mismatch(sheet, row, full_name, normalized_birthdate, options)
                return None
            else:
                collector.add_general_error(
                    sheet,
                    row,
                    f"Multiple athlete records for '{full_name}' with birthdate {normalized_birthdate}.",
                )
                return None
        else:
            distinct_birthdates = {normalize_birthdate(c.birthdate) for c in candidates}
            if len(candidates) == 1 or len(distinct_birthdates) == 1:
                selected = candidates[0]
            else:
                collector.add_general_error(
                    sheet,
                    row,
                    f"No birthdate provided for '{full_name}' and multiple athlete records exist.",
                )
                return None

        if selected:
            db_birthdate = normalize_birthdate(selected.birthdate)
            if normalized_birthdate and db_birthdate and db_birthdate != normalized_birthdate:
                collector.add_birthdate_mismatch(
                    sheet, row, full_name, normalized_birthdate, db_birthdate
                )
                return None
            if gender and selected.gender and gender != selected.gender:
                collector.add_gender_mismatch(sheet, row, full_name, gender, selected.gender)
                return None
        return selected


class ClubIndex:
    def __init__(self, mapping: Dict[str, ClubRecord]):
        self.mapping = mapping

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "ClubIndex":
        df = pd.read_sql_query(
            "SELECT club_name, club_code, state_code, nation FROM clubs", conn
        )
        mapping: Dict[str, ClubRecord] = {}
        for _, row in df.iterrows():
            club_name = as_clean_str(row["club_name"])
            if not club_name:
                    continue
            record = ClubRecord(
                club_name=club_name,
                club_code=as_clean_str(row.get("club_code")) or None,
                state_code=as_clean_str(row.get("state_code")) or None,
                nation=as_clean_str(row.get("nation")).upper() or None,
            )
            mapping[normalize_name(club_name)] = record
        return cls(mapping)

    def resolve(
        self,
        club_name: str,
        sheet: str,
        row: int,
        collector: ValidationCollector,
    ) -> Optional[ClubRecord]:
        norm = normalize_name(club_name)
        if not norm:
            collector.add_club_missing(sheet, row, club_name)
            return None
        record = self.mapping.get(norm)
        if not record:
            collector.add_club_missing(sheet, row, club_name)
            return None
        return record


class EventIndex:
    def __init__(self, mapping: Dict[Tuple[str, int, str, str], str]):
        self.mapping = mapping

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> "EventIndex":
        df = pd.read_sql_query("SELECT id, course, distance, stroke, gender FROM events", conn)
        mapping: Dict[Tuple[str, int, str, str], str] = {}
        for _, row in df.iterrows():
            course = as_clean_str(row["course"]).upper()
            distance = int(row["distance"])
            stroke = as_clean_str(row["stroke"])
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
) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str], Optional[str]]:
    results: List[Dict[str, Any]] = []
    sheet_meet_name: Optional[str] = None
    sheet_meet_date: Optional[str] = None
    sheet_meet_city: Optional[str] = None

    if df.shape[0] < 3:
        return results, sheet_meet_name, sheet_meet_date, sheet_meet_city

    for row_idx in range(2, len(df)):
        row = df.iloc[row_idx]
        excel_row = row_idx + 1

        full_name = as_clean_str(get_value(row, "FULLNAME"))
        if not full_name:
            continue

        course = parse_course(get_value(row, "COURSE"))
        if not course:
            collector.add_course_error(sheet_name, excel_row, full_name, as_clean_str(get_value(row, "COURSE")))
            continue

        gender = parse_gender(get_value(row, "GENDER"))
        if not gender:
            collector.add_general_error(sheet_name, excel_row, f"Unable to parse gender for '{full_name}'.")
            continue

        distance_value = get_value(row, "DISTANCE")
        stroke_value = get_value(row, "STROKE")
        relay_meta = detect_relay(distance_value, stroke_value, sheet_name)

        event_id: Optional[str] = None
        distance_int: Optional[int] = None
        stroke_name: Optional[str] = None

        if relay_meta:
            event_id = event_index.resolve_relay(course, relay_meta.leg_distance, relay_meta.stroke_kind, gender)
            if not event_id:
                collector.add_event_missing(
                    sheet_name,
                    excel_row,
                    relay_description(relay_meta, course, gender),
                )
                continue
        else:
            distance_text = as_clean_str(distance_value)
            if not distance_text:
                collector.add_event_missing(sheet_name, excel_row, f"{course} event missing distance for {full_name}.")
                continue
            try:
                distance_int = int(float(distance_text))
            except ValueError:
                collector.add_event_missing(sheet_name, excel_row, f"Invalid distance '{distance_text}' for {full_name}.")
                continue
            stroke_symbol = as_clean_str(stroke_value).upper()
            stroke_name = STROKE_MAP.get(stroke_symbol)
            if not stroke_name:
                collector.add_event_missing(sheet_name, excel_row, f"Unknown stroke '{stroke_symbol}' for {full_name}.")
                continue
            if stroke_name == "IM" and distance_int == 100 and course != "SCM":
                collector.add_event_missing(
                    sheet_name,
                    excel_row,
                    f"100 IM only accepted for SCM (row shows {course}).",
                )
                continue
            event_id = event_index.resolve_individual(course, distance_int, stroke_name, gender)
            if not event_id:
                collector.add_event_missing(
                    sheet_name,
                    excel_row,
                    f"No event found for {course} {distance_int}m {stroke_name} {gender}.",
                )
                continue

        meet_name_cell = as_clean_str(get_value(row, "MEETNAME"))
        if meet_name_cell and not sheet_meet_name:
            sheet_meet_name = meet_name_cell

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
            collector.add_time_error(
                sheet_name,
                excel_row,
                full_name,
                time_string,
                as_clean_str(get_value(row, "SWIMTIME_N")),
            )
            continue

        place = parse_optional_int(get_value(row, "PLACE"))
        aqua_points = parse_optional_int(get_value(row, "PTS_FINA"))
        rudolph_points = parse_optional_float(get_value(row, "PTS_RUDOLPH"))

        club_name_value = as_clean_str(get_value(row, "CLUBNAME"))
        nation_value = as_clean_str(get_value(row, "NATION")).upper()
        birthdate_value = as_clean_str(get_value(row, "BIRTHDATE"))

        club_lookup_value = club_name_value
        if relay_meta and not club_lookup_value:
            club_lookup_value = full_name

        club_record = club_index.resolve(club_lookup_value, sheet_name, excel_row, collector)
        if not club_record:
            continue

        athlete_id: Optional[str] = None
        day_age: Optional[int] = None
        year_age: Optional[int] = None

        if not relay_meta:
            athlete_record = athlete_index.find(full_name, birthdate_value, gender, sheet_name, excel_row, collector)
            if not athlete_record:
                continue
            workbook_birthdate_norm = normalize_birthdate(birthdate_value)
            athlete_birthdate_norm = normalize_birthdate(athlete_record.birthdate)
            if (
                workbook_birthdate_norm
                and athlete_birthdate_norm
                and workbook_birthdate_norm != athlete_birthdate_norm
            ):
                collector.add_birthdate_mismatch(
                    sheet_name, excel_row, full_name, workbook_birthdate_norm, athlete_birthdate_norm
                )
                continue
            if nation_value and athlete_record.nation and nation_value != athlete_record.nation:
                collector.add_nation_mismatch(
                    sheet_name,
                    excel_row,
                    full_name,
                    nation_value,
                    athlete_record.nation,
                )
                continue
            if nation_value and not athlete_record.nation:
                collector.add_nation_mismatch(
                    sheet_name,
                    excel_row,
                    full_name,
                    nation_value,
                    "(blank in athlete table)",
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
            "time_seconds_numeric": time_numeric,
            "time_string": time_string,
            "place": place,
            "aqua_points": aqua_points,
            "rudolph_points": rudolph_points,
            "course": course,
            "result_meet_date": meet_date_str or meet_info.get("meet_date"),
            "meet_name": meet_name_cell or sheet_meet_name or meet_info.get("name"),
            "meet_city": meet_city_cell or sheet_meet_city or meet_info.get("city"),
            "day_age": day_age,
            "year_age": year_age,
            "team_name": club_record.club_name,
            "team_code": club_record.club_code,
            "team_state_code": club_record.state_code,
            "team_nation": club_record.nation,
            "is_relay": 1 if relay_meta else 0,
            }
            
            results.append(result)
            
    return results, sheet_meet_name, sheet_meet_date, sheet_meet_city


# --------------------------------------------------------------------------- #
# Conversion entry point
# --------------------------------------------------------------------------- #


def process_meet_file_simple(file_path: Path, meet_info: Dict[str, Any]):
    """Read an Excel workbook and return (athlete_refs, results, event_refs)."""
    print(f"Processing: {file_path.name}")

    collector = ValidationCollector()

    conn = get_database_connection()
    try:
        athlete_index = AthleteIndex.from_connection(conn)
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

    for sheet_name in excel.sheet_names:
        normalized_name = "".join(as_clean_str(sheet_name).upper().split())
        if not sheet_name.strip():
            continue
        if "LAP" in normalized_name or "TOP" in normalized_name:
            continue

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=None,
            usecols=USECOLS,
            engine=excel_engine,
        )

        results, sheet_meet_name, sheet_meet_date, sheet_meet_city = process_sheet(
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

        if sheet_meet_name:
            meet_name_candidates.append(sheet_meet_name)
        if sheet_meet_date:
            meet_date_candidates.append(sheet_meet_date)
        if sheet_meet_city:
            meet_city_candidates.append(sheet_meet_city)

    collector.raise_if_errors()

    if meet_name_candidates:
        meet_info["name"] = meet_name_candidates[0]
    if meet_date_candidates:
        meet_date_candidates.sort()
        meet_info["meet_date"] = meet_date_candidates[0]
    if meet_city_candidates and not meet_info.get("city"):
        meet_info["city"] = meet_city_candidates[0]

    athlete_refs = [{"id": aid, "existing": True} for aid in sorted(used_athletes)]
    event_refs = [{"id": eid, "existing": True} for eid in sorted(used_events)]

    print(f"  Prepared {len(all_results)} results from {file_path.name}")
    return athlete_refs, all_results, event_refs


# --------------------------------------------------------------------------- #
# Database interaction helpers
# --------------------------------------------------------------------------- #


def get_database_connection():
    project_root = Path(__file__).parent.parent
    db_path = project_root / "malaysia_swimming.db"
    return sqlite3.connect(str(db_path))


def insert_data_simple(conn, athletes, results, events, meet_info):
    """Insert the prepared results into SQLite (athletes/events lists mark existing rows)."""
    cursor = conn.cursor()
    
    columns_to_add = [
        ("day_age", "INTEGER"),
        ("year_age", "INTEGER"),
        ("result_meet_date", "TEXT"),
        ("aqua_points", "INTEGER"),
        ("time_seconds_numeric", "REAL"),
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
            "CREATE INDEX IF NOT EXISTS idx_results_unique ON results(meet_id, event_id, athlete_id, time_seconds_numeric)"
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
    
    for result in results:
        original_athlete_id = result.get("athlete_id")
        original_event_id = result.get("event_id")
        if original_athlete_id:
            resolved_athlete_id = athlete_id_map.get(original_athlete_id)
            if not resolved_athlete_id:
                print(f"  WARNING: Missing athlete {original_athlete_id} for result {result.get('id')}")
            skipped += 1
            continue
            result["athlete_id"] = resolved_athlete_id
        if original_event_id:
            resolved_event_id = event_id_map.get(original_event_id)
            if not resolved_event_id:
                print(f"  WARNING: Missing event {original_event_id} for result {result.get('id')}")
                skipped += 1
                continue
            result["event_id"] = resolved_event_id

        numeric_time = result.get("time_seconds_numeric")
        time_string = result.get("time_string")
        meet_id = result.get("meet_id")
        if not result.get("event_id") or not meet_id:
            skipped += 1
            continue

        athlete_id_for_query = result.get("athlete_id")
        cursor.execute(
            """
            SELECT 1 FROM results 
            WHERE meet_id = ? 
              AND event_id = ? 
              AND (
                    (? IS NULL AND athlete_id IS NULL)
                 OR (? IS NOT NULL AND athlete_id = ?)
              )
              AND (
                    (? IS NOT NULL AND time_seconds_numeric IS NOT NULL AND ABS(time_seconds_numeric - ?) < 1e-6)
                 OR (? IS NULL AND time_seconds_numeric IS NULL AND IFNULL(time_string, '') = IFNULL(?, ''))
              )
            LIMIT 1
            """,
            (
                meet_id,
                result["event_id"],
                athlete_id_for_query,
                athlete_id_for_query,
                athlete_id_for_query,
                numeric_time,
                numeric_time,
                numeric_time,
                numeric_time,
                time_string,
                time_string,
            ),
        )
        if cursor.fetchone():
            skipped += 1
            continue
        
        cursor.execute(
            """
            INSERT INTO results (
                id,
                meet_id,
                athlete_id,
                event_id,
                time_seconds,
                time_string,
                time_seconds_numeric,
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
                is_relay
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["id"],
                meet_id,
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
            ),
        )
        inserted += 1
    
    conn.commit()
    return {"inserted_results": inserted, "skipped_results": skipped}


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
        meet_info = {
            "id": str(uuid.uuid4()),
            "name": "Test Meet",
            "meet_date": "2024-08-20",
            "location": "Unknown",
        }
        try:
            athletes, results, events = process_meet_file_simple(test_file, meet_info)
            print(f"\n✅ Prepared {len(results)} results across {len(events)} event references.")
        except ConversionValidationError as exc:
            print("\n❌ Validation failed:")
            print(exc)
            print(json.dumps(exc.details, indent=2))
    else:
        print(f"Test file not found: {test_file}")

