from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import sqlite3
from typing import List, Dict, Any

router = APIRouter()

def get_db():
    # Simple SQLite connection for now
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'malaysia_swimming.db')
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
        m.name as meet_name
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
            "meet": row[8]
        })
    
    conn.close()
    return {"results": data, "count": len(data)}

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
