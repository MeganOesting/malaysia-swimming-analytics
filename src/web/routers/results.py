from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import sqlite3
from typing import List, Dict, Any

router = APIRouter()

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
    
    # Try root directory first (local development)
    root_db = project_root / "malaysia_swimming.db"
    if root_db.exists():
        db_path = str(root_db)
    else:
        # Try database folder
        db_folder_db = project_root / "database" / "malaysia_swimming.db"
        if db_folder_db.exists():
            db_path = str(db_folder_db)
        else:
            # Docker path (fallback)
            db_path = '/app/database/malaysia_swimming.db'
    
    # Ensure the directory exists
    db_dir = Path(db_path).parent
    if not db_dir.exists() and db_path.startswith('/app'):
        # Docker path - assume it exists
        pass
    elif not Path(db_path).exists() and not db_path.startswith('/app'):
        # File doesn't exist - raise an error
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
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
                a.name,
                a.gender,
                COALESCE(r.year_age, a.age) as age,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                m.id as meet_id,
                m.name as meet_name,
                m.meet_type as meet_code
            FROM results r
            JOIN athletes a ON r.athlete_id = a.id
            JOIN events e ON r.event_id = e.id
            JOIN meets m ON r.meet_id = m.id
            ORDER BY m.meet_date DESC, e.distance, e.stroke, COALESCE(r.time_seconds, 999999)
            """
        else:
            query = """
            SELECT 
                a.name,
                a.gender,
                COALESCE(r.year_age, a.age) as age,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                m.id as meet_id,
                m.name as meet_name,
                m.meet_type as meet_code
            FROM results r
            JOIN athletes a ON r.athlete_id = a.id
            JOIN events e ON r.event_id = e.id
            JOIN meets m ON r.meet_id = m.id
            ORDER BY e.distance, e.stroke, COALESCE(r.time_seconds, 999999)
            """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in results:
            data.append({
                "name": row[0],
                "gender": row[1],
                "age": row[2],
                "distance": row[3],
                "stroke": row[4],
                "time": row[5],
                "place": row[6],
                "aqua_points": row[7],
                "meet_id": row[8],  # meet_id
                "meet": row[9],  # meet_name
                "meet_code": row[10]  # meet_code
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
                a.name,
                a.gender,
                COALESCE(r.year_age, a.age) as age,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.aqua_points,
                m.id as meet_id,
                m.name as meet_name,
                m.meet_type as meet_code
            FROM results r
            JOIN athletes a ON r.athlete_id = a.id
            JOIN events e ON r.event_id = e.id
            JOIN meets m ON r.meet_id = m.id
        """
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        # Filter by meet IDs
        if meet_ids:
            meet_id_list = [m.strip() for m in meet_ids.split(',') if m.strip()]
            if meet_id_list:
                # Check if STATE25 is in the list
                if 'STATE25' in meet_id_list:
                    # Remove STATE25 and add individual state meet IDs
                    meet_id_list.remove('STATE25')
                    # Get state meet IDs from the meets endpoint logic
                    cursor.execute("""
                        SELECT id FROM meets WHERE meet_type LIKE '%State%'
                    """)
                    state_meets = cursor.fetchall()
                    for sm in state_meets:
                        if sm[0] not in meet_id_list:
                            meet_id_list.append(sm[0])
                
                if meet_id_list:
                    placeholders = ','.join(['?' for _ in meet_id_list])
                    where_conditions.append(f"m.id IN ({placeholders})")
                    params.extend(meet_id_list)
        
        # Filter by genders
        if genders:
            gender_list = [g.strip().upper() for g in genders.split(',') if g.strip()]
            if gender_list:
                placeholders = ','.join(['?' for _ in gender_list])
                where_conditions.append(f"a.gender IN ({placeholders})")
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
            where_conditions.append("a.is_foreign = 0")
        
        # Combine WHERE conditions
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions)
        else:
            query = base_query
        
        # Add ORDER BY
        if has_meet_date:
            query += " ORDER BY m.meet_date DESC, e.distance, e.stroke, COALESCE(r.time_seconds, 999999)"
        else:
            query += " ORDER BY e.distance, e.stroke, COALESCE(r.time_seconds, 999999)"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in results:
            data.append({
                "name": row[0],
                "gender": row[1],
                "age": row[2],
                "distance": row[3],
                "stroke": row[4],
                "time": row[5],
                "place": row[6],
                "aqua_points": row[7],
                "meet_id": row[8],
                "meet": row[9],
                "meet_code": row[10]
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
        
        # Get all meets with dates in a single query - much faster!
        cursor.execute("""
            SELECT id, name, meet_type, COALESCE(meet_date, '2099-12-31') as meet_date
            FROM meets 
            ORDER BY COALESCE(meet_date, '2099-12-31') DESC, name
        """)
        meets = cursor.fetchall()
        
        # Identify state meets by name patterns (excluding national meets)
        state_meet_patterns = [
            "Selangor", "Sarawak", "Sabah", "Pasa", "Perak", "Johor", 
            "Milo/Akl", "Kedah", "Pahang", "Kelantan", "Melaka", "Negeri",
            "Terengganu", "Penang"
        ]
        
        # Exclude these national meets (they should NOT be treated as state meets)
        national_meet_patterns = [
            "Malaysia Age Group", "MIAG", "Southeast Asian", "SEA Age"
        ]
        
        # Map specific meet names to their codes
        meet_name_to_code = {
            "47th Southeast Asian Age Group Aquatics Championships": "SEAG25",
            "67th Malaysian Open Championships": "MO25",
            "60th Malaysia Age Group Championships": "MIAG25",
            "Sukan Malaysia XXI Msn": "SUK24",
            # Other non-state meets
            "Mattioli Victorian Open": "VIC25",
            "Open Championships": "OPEN25",
            "Asian Open Schools Invitational Championships": "AIS25",
        }
        
        # Separate state meets from other meets - process in memory
        state_meet_ids = []
        other_meets = []
        
        for meet in meets:
            meet_id = meet[0]
            db_name = meet[1]
            db_type = meet[2] if len(meet) > 2 and meet[2] else None
            meet_date = meet[3] if len(meet) > 3 else "2099-12-31"
            
            # Check if this is a national meet (exclude from state meets)
            is_national_meet = any(pattern.lower() in db_name.lower() for pattern in national_meet_patterns)
            
            # Check if this is a state meet (must match state pattern AND not be a national meet)
            is_state_meet = (not is_national_meet) and (
                any(pattern.lower() in db_name.lower() for pattern in state_meet_patterns) or 
                (db_type and "State" in db_type and "Malaysia" not in db_name)
            )
            
            if is_state_meet:
                state_meet_ids.append(meet_id)
            else:
                # Get code for non-state meets
                display_code = meet_name_to_code.get(db_name)
                if not display_code:
                    # Fallback codes
                    if "Southeast Asian" in db_name or "SEA" in db_name:
                        display_code = "SEAG25"
                    elif "Malaysia Open" in db_name or "Malaysian Open" in db_name:
                        display_code = "MO25"
                    elif "Malaysia Age Group" in db_name or "MIAG" in db_name:
                        display_code = "MIAG25"
                    elif "Sukan Malaysia" in db_name or "SUKMA" in db_name:
                        display_code = "SUK24"
                    else:
                        display_code = db_name[:6].upper() if db_name else ""
                
                other_meets.append({
                    "id": meet_id,
                    "name": db_name,
                    "meet_code": display_code,
                    "meet_date": meet_date
                })
        
        # Build final data list
        data = []
        
        # Combine state meets group and other meets, then sort by date
        all_meets_with_dates = []
        
        # Add state meets as a single grouped entry
        if state_meet_ids:
            # Find earliest date from state meets - calculate from already fetched data
            state_dates = []
            for meet in meets:
                if meet[0] in state_meet_ids:
                    state_date = meet[3] if len(meet) > 3 else "2099-12-31"
                    if state_date != "2099-12-31":
                        state_dates.append(state_date)
            
            state_min_date = min(state_dates) if state_dates else "2099-12-31"
            
            all_meets_with_dates.append({
                "id": "STATE25",
                "name": "State Meets",
                "meet_code": "STATE25",
                "meet_date": state_min_date,
                "state_meet_ids": state_meet_ids
            })
        
        # Add other meets (already have dates from initial query)
        all_meets_with_dates.extend(other_meets)
        
        # Sort by date descending (most recent first), then by name
        all_meets_with_dates.sort(key=lambda x: (x.get("meet_date", "2099-12-31"), x.get("name", "")), reverse=True)
        
        # Remove meet_date from output (only used for sorting)
        for meet in all_meets_with_dates:
            if "meet_date" in meet:
                del meet["meet_date"]
        
        data = all_meets_with_dates
        
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
