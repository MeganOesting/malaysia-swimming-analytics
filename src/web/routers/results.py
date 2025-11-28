from datetime import datetime
from typing import Optional

from fastapi import APIRouter
import sqlite3

# Import date validation utility
from ..utils.date_validator import parse_and_validate_date
# Import MAP points calculation
from ..utils.calculation_utils import calculate_map_points

router = APIRouter()


def _compute_age(
    year_age: Optional[int],
    day_age: Optional[int],
    birthdate: Optional[str],
    meet_date: Optional[str],
) -> Optional[int]:
    """
    Compute athlete age at time of meet.
    Priority: year_age → day_age → computed from birthdate + meet_date

    Note: Dates must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
    """
    if year_age is not None:
        return year_age

    if day_age is not None:
        return day_age

    if not birthdate or not meet_date:
        return None

    try:
        # Parse ISO 8601 dates
        birth_dt = datetime.strptime(birthdate.rstrip('Z'), "%Y-%m-%dT%H:%M:%S")
        meet_dt = datetime.strptime(meet_date.rstrip('Z'), "%Y-%m-%dT%H:%M:%S")

        years = meet_dt.year - birth_dt.year
        if (meet_dt.month, meet_dt.day) < (birth_dt.month, birth_dt.day):
            years -= 1
        return years
    except (ValueError, AttributeError):
        # Invalid date format - should be caught by validation earlier
        return None


def get_db():
    # Simple SQLite connection for now
    import os
    from pathlib import Path
    
    # Get database path - works for both Docker and local development
    # results.py is in src/web/routers/, so go up 4 levels to get to project root
    # __file__ = src/web/routers/results.py
    # parent = src/web/routers/
    # parent.parent = src/web/
    # parent.parent.parent = src/
    # parent.parent.parent.parent = project root
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Use authoritative database in root directory
    root_db = project_root / "malaysia_swimming.db"
    if root_db.exists():
        db_path = str(root_db)
    else:
        # Docker path (fallback)
        db_path = '/app/malaysia_swimming.db'
    
    # Ensure the directory exists
    db_dir = Path(db_path).parent
    if not db_dir.exists() and db_path.startswith('/app'):
        # Docker path - assume it exists
        pass
    elif not Path(db_path).exists() and not db_path.startswith('/app'):
        # File doesn't exist - raise an error
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/results/simple")
async def get_simple_results():
    """
    Get simple results with direct mapping columns only.
    This is for the first commit - simple data display.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if meet_date column exists
        cursor.execute("PRAGMA table_info(meets)")
        columns = [col[1] for col in cursor.fetchall()]
        has_meet_date = 'meet_date' in columns
        
        # Simple query with direct mapping columns
        # Use year_age with fallback to athlete age
        if has_meet_date:
            query = """
            SELECT
                COALESCE(a.FULLNAME, '') AS full_name,
                COALESCE(a.Gender, '') AS gender,
                r.year_age,
                r.day_age,
                a.BIRTHDATE AS birthdate,
                m.meet_date AS meet_date,
                e.event_distance AS distance,
                e.event_stroke AS stroke,
                r.time_string,
                r.comp_place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.meet_name AS meet_name,
                m.meet_type AS meet_code,
                r.result_status
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
            ORDER BY COALESCE(m.meet_date, '2099-12-31') DESC, e.event_distance, e.event_stroke, COALESCE(r.time_seconds, 999999)
            """
        else:
            query = """
            SELECT
                COALESCE(a.FULLNAME, '') AS full_name,
                COALESCE(a.Gender, '') AS gender,
                r.year_age,
                r.day_age,
                a.BIRTHDATE AS birthdate,
                m.meet_date AS meet_date,
                e.event_distance AS distance,
                e.event_stroke AS stroke,
                r.time_string,
                r.comp_place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.meet_name AS meet_name,
                m.meet_type AS meet_code,
                r.result_status
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
            ORDER BY e.event_distance, e.event_stroke, COALESCE(r.time_seconds, 999999)
            """
        
        cursor.execute(query)
        results = cursor.fetchall()

        # Convert to list of dicts
        data = []
        for row in results:
            # Show result_status (DQ, DNS, etc.) in place field if no comp_place and status isn't OK
            place_value = row["comp_place"]
            result_status = row["result_status"] or "OK"
            if place_value is None and result_status != "OK":
                place_value = result_status  # Show DQ, DNS, DNF, SCR

            # Sort key: numeric places first (by value), then statuses at end
            if row["comp_place"] is not None:
                sort_place = row["comp_place"]
            elif result_status == "DQ":
                sort_place = 9991
            elif result_status == "DNS":
                sort_place = 9992
            elif result_status == "DNF":
                sort_place = 9993
            elif result_status == "SCR":
                sort_place = 9994
            else:
                sort_place = 9999

            data.append({
                "name": row["full_name"] or "Unknown",
                "gender": row["gender"] or "U",
                "age": _compute_age(row["year_age"], row["day_age"], row["birthdate"], row["meet_date"]),
                "year_age": row["year_age"],
                "distance": row["distance"],
                "stroke": row["stroke"],
                "time": row["time_string"],
                "place": place_value,
                "aqua_points": row["aqua_points"],
                "meet_id": str(row["meet_id"]) if row["meet_id"] else None,
                "meet": row["meet_name"],
                "meet_code": row["meet_code"],
                "sort_place": sort_place
            })

        conn.close()

        # Sort by sort_place (1,2,3... then DQ, DNS, etc. at bottom)
        data.sort(key=lambda x: x["sort_place"])

        return {"results": data, "count": len(data)}
    except Exception as e:
        import traceback
        print(f"Error in get_simple_results: {e}")
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return {"results": [], "count": 0, "error": str(e)}

@router.get("/results/filtered")
async def get_filtered_results(
    meet_ids: str = None,
    genders: str = None,
    events: str = None,
    age_groups: str = None,
    include_foreign: bool = True
):
    """
    Get filtered results based on meet, gender, event, and age group filters.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if meet_date column exists
        cursor.execute("PRAGMA table_info(meets)")
        columns = [col[1] for col in cursor.fetchall()]
        has_meet_date = 'meet_date' in columns
        
        # Build base query
        # Use year_age with fallback to athlete age
        # Include club/team info for Team column display
        base_query = """
            SELECT
                COALESCE(a.fullname, fa.fullname, '') AS full_name,
                COALESCE(a.Gender, fa.gender, '') AS gender,
                r.year_age,
                r.day_age,
                COALESCE(a.BIRTHDATE, fa.birthdate) AS birthdate,
                m.meet_date AS meet_date,
                e.event_distance AS distance,
                e.event_stroke AS stroke,
                e.gender AS event_gender,
                r.time_string,
                r.time_seconds,
                r.comp_place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.meet_name AS meet_name,
                m.meet_alias AS meet_code,
                COALESCE(a.nation, fa.nation, '') AS nation,
                COALESCE(r.club_code, '') AS club_code,
                COALESCE(r.club_name, '') AS club_name,
                COALESCE(r.state_code, '') AS state_code,
                r.result_status
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN foreign_athletes fa ON r.foreign_athlete_id = fa.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
        """
        
        # Build WHERE clause
        where_conditions = []
        params = []
        meet_id_list = []  # Initialize for debug loop

        # Filter by meet IDs (UUIDs stored as strings)
        if meet_ids:
            meet_id_list = [m.strip() for m in meet_ids.split(',') if m.strip()]
            if meet_id_list:
                placeholders = ','.join(['?' for _ in meet_id_list])
                where_conditions.append(f"r.meet_id IN ({placeholders})")
                params.extend(meet_id_list)
                print(f"[DEBUG] Filtering by meet_ids: {meet_id_list}")

        # Debug: check what's in the database
        cursor.execute("SELECT COUNT(*) FROM results")
        total_results = cursor.fetchone()[0]
        print(f"[DEBUG] Total rows in results table: {total_results}")

        cursor.execute("SELECT DISTINCT meet_id FROM results LIMIT 5")
        sample_result_meet_ids = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Sample meet_ids in results table: {sample_result_meet_ids}")

        cursor.execute("SELECT id FROM meets LIMIT 5")
        sample_meets_ids = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Sample ids in meets table: {sample_meets_ids}")

        # Check if the requested meet_id exists and has results
        for mid in meet_id_list:
            cursor.execute("SELECT COUNT(*) FROM results WHERE meet_id = ?", (mid,))
            count = cursor.fetchone()[0]
            print(f"[DEBUG] Results with meet_id '{mid}': {count}")

            # Check event_ids for this meet
            cursor.execute("SELECT DISTINCT e.event_distance, e.event_stroke FROM results r LEFT JOIN events e ON r.event_id = e.id WHERE r.meet_id = ? ORDER BY e.event_distance LIMIT 10", (mid,))
            events_sample = [(row[0], row[1]) for row in cursor.fetchall()]
            print(f"[DEBUG] Events available for this meet: {events_sample}")

            # Check gender values for this meet
            cursor.execute("SELECT DISTINCT a.Gender FROM results r LEFT JOIN athletes a ON r.athlete_id = a.id WHERE r.meet_id = ? LIMIT 10", (mid,))
            genders_sample = [row[0] for row in cursor.fetchall()]
            print(f"[DEBUG] Gender values for this meet: {genders_sample}")

            # Check if 50m Free exists for this meet
            cursor.execute("""
                SELECT COUNT(*) FROM results r
                JOIN events e ON r.event_id = e.id
                WHERE r.meet_id = ? AND e.event_distance = 50 AND e.event_stroke = 'Free'
            """, (mid,))
            fr50_count = cursor.fetchone()[0]
            print(f"[DEBUG] 50m Free results for this meet: {fr50_count}")
        
        # Filter by genders (both athlete gender AND event gender since events are gender-specific)
        if genders:
            gender_list = [g.strip().upper() for g in genders.split(',') if g.strip()]
            if gender_list:
                placeholders = ','.join(['?' for _ in gender_list])
                # Filter on event gender (events are gender-specific in this schema)
                where_conditions.append(f"UPPER(COALESCE(e.gender, '')) IN ({placeholders})")
                params.extend(gender_list)
        
        # Filter by events
        if events:
            event_list = [e.strip() for e in events.split(',') if e.strip()]
            if event_list:
                # Parse event formats: "50m Free", "50m FR", "50 Free", "100 Free", etc.
                # Map user-facing stroke names to DATABASE format (Free/Back/Breast/Fly/Medley)
                event_conditions = []
                stroke_map = {
                    # Full names -> database format
                    "Free": "Free", "Freestyle": "Free",
                    "Back": "Back", "Backstroke": "Back",
                    "Breast": "Breast", "Breaststroke": "Breast",
                    "Fly": "Fly", "Butterfly": "Fly",
                    "IM": "Medley", "Medley": "Medley",
                    # Short codes -> database format (legacy support)
                    "Fr": "Free", "FR": "Free",
                    "Bk": "Back", "BK": "Back",
                    "Br": "Breast", "BR": "Breast",
                    "Fl": "Fly", "BU": "Fly",
                    "ME": "Medley"
                }
                for event in event_list:
                    # Try "50m Free" format first
                    if 'm ' in event:
                        parts = event.split('m ')
                        if len(parts) == 2:
                            try:
                                distance = int(parts[0])
                                stroke_name = parts[1]
                                stroke_code = stroke_map.get(stroke_name, stroke_name)
                                event_conditions.append("(e.event_distance = ? AND e.event_stroke = ?)")
                                params.append(distance)
                                params.append(stroke_code)
                            except ValueError:
                                pass
                    # Try "50 Free" format (no 'm')
                    elif ' ' in event:
                        parts = event.split(' ', 1)
                        if len(parts) == 2:
                            try:
                                distance = int(parts[0])
                                stroke_name = parts[1]
                                stroke_code = stroke_map.get(stroke_name, stroke_name)
                                event_conditions.append("(e.event_distance = ? AND e.event_stroke = ?)")
                                params.append(distance)
                                params.append(stroke_code)
                            except ValueError:
                                pass

                if event_conditions:
                    where_conditions.append(f"({' OR '.join(event_conditions)})")
        
        # Filter by age groups
        if age_groups:
            age_list = [a.strip().upper() for a in age_groups.split(',') if a.strip()]
            if age_list:
                age_conditions = []
                for age in age_list:
                    if age == 'OPEN':
                        # No age filtering for OPEN
                        continue
                    else:
                        # Parse age ranges like "13", "15", "17", "13-14", "16-18", etc.
                        if '-' in age:
                            # Range like "16-18"
                            parts = age.split('-')
                            if len(parts) == 2:
                                try:
                                    min_age = int(parts[0])
                                    max_age = int(parts[1])
                                    age_conditions.append("r.year_age BETWEEN ? AND ?")
                                    params.append(min_age)
                                    params.append(max_age)
                                except ValueError:
                                    pass
                        elif age == '13&UNDER' or age == '13 & UNDER':
                            # 13 and under
                            age_conditions.append("r.year_age <= 13")
                        else:
                            # Single age like "13"
                            try:
                                age_num = int(age)
                                age_conditions.append("r.year_age = ?")
                                params.append(age_num)
                            except ValueError:
                                pass

                if age_conditions:
                    where_conditions.append(f"({' OR '.join(age_conditions)})")
        
        # Filter out foreign athletes if needed
        if not include_foreign:
            where_conditions.append("UPPER(COALESCE(a.NATION, 'MAS')) = 'MAS'")
        
        # Combine WHERE conditions
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions)
        else:
            query = base_query
        
        # Add ORDER BY - fastest times first within each event
        query += " ORDER BY e.event_distance, e.event_stroke, COALESCE(r.time_seconds, 999999) ASC"
        
        print(f"[DEBUG] Final query: {query}")
        print(f"[DEBUG] Query params: {params}")

        cursor.execute(query, params)
        results = cursor.fetchall()
        print(f"[DEBUG] Query returned {len(results)} rows")

        # Convert to list of dicts
        data = []
        for row in results:
            # Calculate age for MAP points
            age = _compute_age(row["year_age"], row["day_age"], row["birthdate"], row["meet_date"])

            # Calculate MAP points using event gender, distance, stroke, time_seconds, and age
            map_points = None
            if age and row["time_seconds"] and row["distance"] and row["stroke"]:
                # Use event_gender for MAP lookup (M or F)
                event_gender = row["event_gender"] or row["gender"]
                map_points = calculate_map_points(
                    conn,
                    event_gender,
                    row["distance"],
                    row["stroke"],
                    row["time_seconds"],
                    age
                )

            # Show result_status (DQ, DNS, etc.) in place field if no comp_place and status isn't OK
            place_value = row["comp_place"]
            result_status = row["result_status"] or "OK"
            if place_value is None and result_status != "OK":
                place_value = result_status  # Show DQ, DNS, DNF, SCR

            # Sort key: numeric places first (by value), then statuses at end
            # Numeric places: use the number, Statuses: use 9999 + order
            if row["comp_place"] is not None:
                sort_place = row["comp_place"]
            elif result_status == "DQ":
                sort_place = 9991
            elif result_status == "DNS":
                sort_place = 9992
            elif result_status == "DNF":
                sort_place = 9993
            elif result_status == "SCR":
                sort_place = 9994
            else:
                sort_place = 9999  # OK with no place

            data.append({
                "name": row["full_name"] or "Unknown",
                "gender": row["gender"] or "U",
                "age": age,
                "year_age": row["year_age"],
                "distance": row["distance"],
                "stroke": row["stroke"],
                "time": row["time_string"],
                "place": place_value,
                "aqua_points": row["aqua_points"],
                "map_points": map_points,
                "meet_id": str(row["meet_id"]) if row["meet_id"] else None,
                "meet": row["meet_name"],
                "meet_code": row["meet_code"],
                "club_code": row["club_code"] or "",
                "club_name": row["club_name"] or "",
                "state_code": row["state_code"] or "",
                "nation": row["nation"] or "MAS",
                "sort_place": sort_place
            })

        conn.close()

        # Sort by sort_place (1,2,3... then DQ, DNS, etc. at bottom)
        data.sort(key=lambda x: x["sort_place"])

        return {"results": data, "count": len(data)}
    except Exception as e:
        import traceback
        print(f"Error in get_filtered_results: {e}")
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return {"results": [], "count": 0, "error": str(e)}

@router.get("/meets")
async def get_meets():
    """Get list of available meets."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all meets with dates in a single query
        cursor.execute("""
            SELECT id, meet_name, meet_alias, COALESCE(meet_date, '2099-12-31') as meet_date, meet_type
            FROM meets
            ORDER BY COALESCE(meet_date, '2099-12-31') DESC, meet_name
        """)
        meets = cursor.fetchall()

        # Process all meets - return all individual meets
        all_meets = []

        for meet in meets:
            meet_id = meet[0]
            db_name = meet[1]
            meet_code = meet[2]  # meet_alias is the code (W-PARA, MIAG25)
            meet_date = meet[3] if len(meet) > 3 else "2099-12-31"
            meet_type = meet[4] if len(meet) > 4 else ""  # meet_type is now OPEN-D, PARA-I

            all_meets.append({
                "id": str(meet_id),
                "name": db_name,
                "meet_code": meet_code,
                "meet_date": meet_date,
                "meet_type": meet_type or ""
            })

        # Sort by date descending (most recent first), then by name
        all_meets.sort(key=lambda x: (x.get("meet_date", "2099-12-31"), x.get("name", "")), reverse=True)

        data = all_meets
        
        conn.close()
        return {"meets": data}
    except Exception as e:
        import traceback
        print(f"Error in get_meets: {e}")
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return {"meets": [], "error": str(e)}

@router.get("/events")
async def get_events():
    """Get list of available events."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get distinct events from database
    cursor.execute("SELECT DISTINCT event_distance, event_stroke FROM events ORDER BY event_distance, event_stroke")
    events = cursor.fetchall()
    
    # Stroke mapping: DATABASE format -> user display
    # Database stores: Free, Back, Breast, Fly, Medley
    # User sees: Free, Back, Breast, Fly, IM
    STROKE_MAP = {
        "Free": "Free",
        "Back": "Back",
        "Breast": "Breast",
        "Fly": "Fly",
        "Medley": "IM",
    }
    
    data = []
    for event in events:
        distance = event[0]
        stroke = event[1]
        stroke_label = STROKE_MAP.get(stroke, stroke)
        event_name = f"{distance}m {stroke_label}"
        data.append({
            "id": event_name,
            "name": event_name
        })
    
    conn.close()
    return {"events": data}

@router.get("/results/stats")
async def get_results_stats():
    """
    Get basic statistics for the results.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute("SELECT COUNT(*) FROM results")
    total_results = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM athletes")
    total_athletes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM meets")
    total_meets = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_results": total_results,
        "total_athletes": total_athletes,
        "total_meets": total_meets
    }
