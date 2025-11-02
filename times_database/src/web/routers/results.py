from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import sqlite3
from typing import List, Dict, Any

router = APIRouter()

def get_db():
    # Simple SQLite connection for now
    import os
    # Use absolute path for Docker container
    db_path = '/app/database/malaysia_swimming.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/results/simple")
async def get_simple_results():
    """
    Get simple results with direct mapping columns only.
    This is for the first commit - simple data display.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Simple query with direct mapping columns
    query = """
    SELECT 
        a.name,
        a.gender,
        r.age,
        e.distance,
        e.stroke,
        r.time_string,
        r.place,
        r.aqua_points,
        m.name as meet_name,
        m.meet_type as meet_code
    FROM results r
    JOIN athletes a ON r.athlete_id = a.id
    JOIN events e ON r.event_id = e.id
    JOIN meets m ON r.meet_id = m.id
    ORDER BY r.created_at DESC
    LIMIT 100
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
            "meet": row[8],  # meet_name
            "meet_code": row[9]  # meet_code
        })
    
    conn.close()
    return {"results": data, "count": len(data)}

@router.get("/meets")
async def get_meets():
    """Get list of available meets."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get distinct meets from database (avoid duplicates)
    cursor.execute("""
        SELECT MIN(id) as id, name, meet_type 
        FROM meets 
        GROUP BY name, meet_type 
        ORDER BY MIN(created_at) DESC
    """)
    meets = cursor.fetchall()
    
    # Map database names to old build display names
    name_mapping = {
        "SUKMA 2024": "SUKMA 2024",
        "SEA Age 2025": "SEA Age 2025", 
        "Malaysia Open 2025": "MO 2025",
        "MIAG 2025": "MIAG 2025",
        "State Championships 2024": "States 2025"
    }
    
    # Map meet codes to old build abbreviations
    code_mapping = {
        "National Games": "SUK24",
        "Regional Age Group": "SEAG25",
        "National Open": "MO25", 
        "International Age Group": "MIA25",
        "State Championships": "STATE24"
    }
    
    data = []
    for meet in meets:
        db_name = meet[1]
        db_code = meet[2]
        
        # Use mapped names and codes
        display_name = name_mapping.get(db_name, db_name)
        display_code = code_mapping.get(db_code, db_code)
        
        data.append({
            "id": meet[0],
            "name": display_name,
            "meet_code": display_code
        })
    
    conn.close()
    return {"meets": data}

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
