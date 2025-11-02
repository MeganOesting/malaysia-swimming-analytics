#!/usr/bin/env python3
"""
Malaysia Swimming Analytics - FastAPI Main Application
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import List, Optional
import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Database path - works for both Docker and local development
def get_db_path():
    """Get database path, checking multiple possible locations"""
    # Try root directory first (local development)
    root_db = project_root / "malaysia_swimming.db"
    if root_db.exists():
        return str(root_db)
    # Try database folder
    db_folder_db = project_root / "database" / "malaysia_swimming.db"
    if db_folder_db.exists():
        return str(db_folder_db)
    # Docker path (fallback)
    return "/app/database/malaysia_swimming.db"

# Import routers
from src.web.routers import results, admin

app = FastAPI(
    title="Malaysia Swimming Analytics API",
    description="Modern swimming analytics platform for Malaysian swimming competitions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(results.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

# Security
security = HTTPBearer()

# TODO: Implement proper JWT authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    # TODO: Implement proper JWT authentication
    return {"user_id": "demo_user", "role": "admin"}

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Malaysia Swimming Analytics API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "malaysia-swimming-analytics"}

# TODO: Implement athlete management endpoints
@app.post("/api/admin/athletes")
async def create_athlete(athlete_data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new athlete"""
    # TODO: Implement athlete creation
    return {"message": "Athlete creation not yet implemented"}

@app.get("/api/athletes")
async def get_athletes(skip: int = 0, limit: int = 100):
    """Get list of athletes"""
    # TODO: Implement athlete retrieval
    return {"athletes": [], "total": 0, "skip": skip, "limit": limit}

# TODO: Implement meet management endpoints
@app.post("/api/admin/meets")
async def create_meet(meet_data: dict, current_user: dict = Depends(get_current_user)):
    """Create a new meet"""
    # TODO: Implement meet creation
    return {"message": "Meet creation not yet implemented"}


# Simple results endpoints for first commit
@app.get("/api/results/simple")
async def get_simple_results():
    """Get simple results with direct mapping columns only."""
    try:
        # Simple SQLite connection
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simple query with direct mapping columns - concatenate distance + stroke for event
        query = """
        SELECT 
            COALESCE(a.name, 'Unknown') as name,
            COALESCE(a.gender, 'U') as gender,
            r.age,
            COALESCE(e.distance, 0) as distance,
            COALESCE(e.stroke, 'Unknown') as stroke,
            r.time_string,
            r.place,
            r.aqua_points,
            COALESCE(m.name, 'Unknown Meet') as meet_name
        FROM results r
        LEFT JOIN athletes a ON r.athlete_id = a.id
        LEFT JOIN events e ON r.event_id = e.id
        LEFT JOIN meets m ON r.meet_id = m.id
        ORDER BY r.created_at DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Meet name to abbreviation mapping
        meet_abbreviations = {
            "SUKMA 2024": "SUK24",
            "MIAG 2025": "MIA25", 
            "Malaysia Open 2025": "MO25",
            "SEA Age 2025": "SEAG25",
            "State Championships 2024": "ST24"
        }
        
        # Convert to list of dicts - concatenate distance + stroke for event
        # Stroke mapping from original code
        STROKE_MAP = {
            "FR": "Free",
            "BK": "Back", 
            "BR": "Breast",
            "BU": "Fly",
            "ME": "IM",
        }
        
        data = []
        for row in results:
            meet_name = row[8]
            meet_abbr = meet_abbreviations.get(meet_name, meet_name)
            distance = row[3]
            stroke = row[4]
            stroke_label = STROKE_MAP.get(stroke, stroke) if stroke != 'Unknown' else 'Unknown'
            event = f"{distance} {stroke_label}" if distance > 0 and stroke != 'Unknown' else "Unknown Event"
            
            data.append({
                "name": row[0],
                "gender": row[1],
                "age": row[2],
                "distance": distance,
                "stroke": stroke,
                "event": event,
                "time": row[5],
                "place": row[6],
                "aqua_points": row[7],
                "meet": meet_abbr,
                "meet_code": meet_abbr
            })
        
        conn.close()
        return {"results": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/stats")
async def get_results_stats():
    """Get basic statistics for the results."""
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Meets and events endpoints moved to routers/results.py

# TODO: Implement results endpoints
@app.get("/api/results")
async def get_results(
    meet_id: Optional[str] = None,
    athlete_id: Optional[str] = None,
    event: Optional[str] = None,
    gender: Optional[str] = None
):
    """Get swimming results with optional filters"""
    # TODO: Implement results retrieval with filtering
    return {"results": []}

# TODO: Implement performance analysis endpoints
@app.get("/api/analytics/performance")
async def get_performance_analysis(athlete_id: str):
    """Get performance analysis for an athlete"""
    # TODO: Implement performance analysis
    return {"message": "Performance analysis not yet implemented"}

@app.get("/api/analytics/age-points")
async def get_age_points(athlete_id: str, event: str):
    """Get age points calculation for an athlete and event"""
    # TODO: Implement age points calculation
    return {"message": "Age points calculation not yet implemented"}

# TODO: Implement data migration endpoints
@app.post("/api/admin/migrate/excel")
async def migrate_excel_data(current_user: dict = Depends(get_current_user)):
    """Migrate Excel data to PostgreSQL"""
    # TODO: Implement Excel to PostgreSQL migration
    return {"message": "Excel migration not yet implemented"}

@app.post("/api/admin/migrate/clean-seag")
async def clean_seag_file(current_user: dict = Depends(get_current_user)):
    """Clean and reformat SEAG_2025_ALL.xlsx file"""
    # TODO: Implement SEAG file cleaning
    return {"message": "SEAG file cleaning not yet implemented"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )



