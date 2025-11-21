from datetime import datetime
from typing import Optional

from fastapi import APIRouter
import sqlite3

# Import date validation utility
from ..utils.date_validator import parse_and_validate_date

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
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.name AS meet_name,
                m.meet_type AS meet_code
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
            ORDER BY COALESCE(m.meet_date, '2099-12-31') DESC, e.distance, e.stroke, COALESCE(r.time_seconds, r.time_seconds_numeric, 999999)
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
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.name AS meet_name,
                m.meet_type AS meet_code
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
            ORDER BY e.distance, e.stroke, COALESCE(r.time_seconds, r.time_seconds_numeric, 999999)
            """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in results:
            data.append({
                "name": row["full_name"] or "Unknown",
                "gender": row["gender"] or "U",
                "age": _compute_age(row["year_age"], row["day_age"], row["birthdate"], row["meet_date"]),
                "distance": row["distance"],
                "stroke": row["stroke"],
                "time": row["time_string"],
                "place": row["place"],
                "aqua_points": row["aqua_points"],
                "meet_id": row["meet_id"],
                "meet": row["meet_name"],
                "meet_code": row["meet_code"]
            })
        
        conn.close()
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
        base_query = """
            SELECT 
                COALESCE(a.FULLNAME, '') AS full_name,
                COALESCE(a.Gender, '') AS gender,
                r.year_age,
                r.day_age,
                a.BIRTHDATE AS birthdate,
                m.meet_date AS meet_date,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                COALESCE(r.meet_id, m.id) AS meet_id,
                m.name AS meet_name,
                m.meet_type AS meet_code,
                COALESCE(a.NATION, '') AS nation
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
        """
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        # Filter by meet IDs
        if meet_ids:
            meet_id_list = [m.strip() for m in meet_ids.split(',') if m.strip()]
            if meet_id_list:
                placeholders = ','.join(['?' for _ in meet_id_list])
                where_conditions.append(f"m.id IN ({placeholders})")
                params.extend(meet_id_list)
        
        # Filter by genders
        if genders:
            gender_list = [g.strip().upper() for g in genders.split(',') if g.strip()]
            if gender_list:
                placeholders = ','.join(['?' for _ in gender_list])
                where_conditions.append(f"UPPER(COALESCE(a.Gender, '')) IN ({placeholders})")
                params.extend(gender_list)
        
        # Filter by events
        if events:
            event_list = [e.strip() for e in events.split(',') if e.strip()]
            if event_list:
                # Parse event format "50m Free", "100m Back", etc.
                event_conditions = []
                for event in event_list:
                    # Parse "50m Free" -> distance=50, stroke="Free"
                    parts = event.split('m ')
                    if len(parts) == 2:
                        try:
                            distance = int(parts[0])
                            stroke_name = parts[1]
                            # Map stroke names to codes
                            stroke_map = {
                                "Free": "FR",
                                "Back": "BK",
                                "Breast": "BR",
                                "Fly": "BU",
                                "IM": "ME"
                            }
                            stroke_code = stroke_map.get(stroke_name, stroke_name)
                            event_conditions.append("(e.distance = ? AND e.stroke = ?)")
                            params.append(distance)
                            params.append(stroke_code)
                        except ValueError:
                            pass  # Invalid distance, skip
                
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
                        # Parse age ranges like "13", "15", "17", "13-14", etc.
                        if '-' in age:
                            # Range like "13-14"
                            parts = age.split('-')
                            if len(parts) == 2:
                                try:
                                    min_age = int(parts[0])
                                    max_age = int(parts[1])
                                    age_conditions.append("COALESCE(r.year_age, a.age) BETWEEN ? AND ?")
                                    params.append(min_age)
                                    params.append(max_age)
                                except ValueError:
                                    pass
                        else:
                            # Single age like "13"
                            try:
                                age_num = int(age)
                                age_conditions.append("COALESCE(r.year_age, a.age) = ?")
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
        
        # Add ORDER BY
        if has_meet_date:
            query += " ORDER BY COALESCE(m.meet_date, '2099-12-31') DESC, e.distance, e.stroke, COALESCE(r.time_seconds, r.time_seconds_numeric, 999999)"
        else:
            query += " ORDER BY e.distance, e.stroke, COALESCE(r.time_seconds, r.time_seconds_numeric, 999999)"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in results:
            data.append({
                "name": row["full_name"] or "Unknown",
                "gender": row["gender"] or "U",
                "age": _compute_age(row["year_age"], row["day_age"], row["birthdate"], row["meet_date"]),
                "distance": row["distance"],
                "stroke": row["stroke"],
                "time": row["time_string"],
                "place": row["place"],
                "aqua_points": row["aqua_points"],
                "meet_id": row["meet_id"],
                "meet": row["meet_name"],
                "meet_code": row["meet_code"]
            })
        
        conn.close()
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
            SELECT id, name, meet_type, COALESCE(meet_date, '2099-12-31') as meet_date
            FROM meets
            ORDER BY COALESCE(meet_date, '2099-12-31') DESC, name
        """)
        meets = cursor.fetchall()

        # Process all meets - return all individual meets
        all_meets = []

        for meet in meets:
            meet_id = meet[0]
            db_name = meet[1]
            meet_code = meet[2]  # Use meet_type directly from database
            meet_date = meet[3] if len(meet) > 3 else "2099-12-31"

            all_meets.append({
                "id": meet_id,
                "name": db_name,
                "meet_code": meet_code,
                "meet_date": meet_date
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
    cursor.execute("SELECT DISTINCT distance, stroke FROM events ORDER BY distance, stroke")
    events = cursor.fetchall()
    
    # Stroke mapping
    STROKE_MAP = {
        "FR": "Free",
        "BK": "Back", 
        "BR": "Breast",
        "BU": "Fly",
        "ME": "IM",
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
