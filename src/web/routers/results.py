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
        # Use day_age or year_age instead of r.age (which no longer exists)
        if has_meet_date:
            query = """
            SELECT 
                a.name,
                a.gender,
                COALESCE(r.day_age, r.year_age, a.age) as age,
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
                COALESCE(r.day_age, r.year_age, a.age) as age,
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

@router.get("/meets")
async def get_meets():
    """Get list of available meets."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get all meets from database
        # Check if meet_date column exists
        cursor.execute("PRAGMA table_info(meets)")
        columns = [col[1] for col in cursor.fetchall()]
        has_date = 'meet_date' in columns
        
        if has_date:
            cursor.execute("""
                SELECT id, name, meet_type, meet_date
                FROM meets 
            """)
        else:
            cursor.execute("""
                SELECT id, name, meet_type 
                FROM meets 
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
        
        # Separate state meets from other meets
        state_meet_ids = []
        other_meets = []
        
        for meet in meets:
            meet_id = meet[0]
            db_name = meet[1]
            db_type = meet[2] if len(meet) > 2 and meet[2] else None
            
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
                    "meet_code": display_code
                })
        
        # Build final data list
        data = []
        
        # Combine state meets group and other meets, then sort by date
        all_meets_with_dates = []
        
        # Add state meets as a single grouped entry
        if state_meet_ids:
            # Get the earliest meet_date from state meets for sorting
            placeholders = ','.join(['?' for _ in state_meet_ids])
            cursor.execute(f"""
                SELECT MIN(meet_date) as min_date
                FROM meets 
                WHERE id IN ({placeholders})
            """, state_meet_ids)
            state_date_result = cursor.fetchone()
            state_min_date = state_date_result[0] if state_date_result and state_date_result[0] else "2099-12-31"
            
            all_meets_with_dates.append({
                "id": "STATE25",
                "name": "State Meets",
                "meet_code": "STATE25",
                "meet_date": state_min_date,
                "state_meet_ids": state_meet_ids
            })
        
        # Add other meets with their dates
        for meet in other_meets:
            # Get meet date for this meet
            cursor.execute("SELECT meet_date FROM meets WHERE id = ?", (meet["id"],))
            date_result = cursor.fetchone()
            meet_date = date_result[0] if date_result and date_result[0] else "2099-12-31"
            meet["meet_date"] = meet_date
            all_meets_with_dates.append(meet)
        
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
