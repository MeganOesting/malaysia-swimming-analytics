"""
Admin API endpoints for Excel file upload and conversion
Using convert_meets_to_sqlite_simple.py for data conversion
"""

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import sqlite3
import sys
import logging

# Date validation
from ..utils.date_validator import parse_and_validate_date

logger = logging.getLogger(__name__)

# Add project root to path
# __file__ = src/web/routers/admin.py
# parent = src/web/routers/
# parent.parent = src/web/
# parent.parent.parent = src/
# parent.parent.parent.parent = project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Import conversion logic - using simple converter
from scripts.convert_meets_to_sqlite_simple import (
    process_meet_file_simple,
    get_database_connection,
    insert_data_simple,
    ConversionValidationError,
)
from scripts.convert_clubs_to_sqlite import process_clubs_file, insert_club_data

router = APIRouter()

# Simple password authentication
ADMIN_PASSWORD = "MAS2025"

class AuthRequest(BaseModel):
    password: str

class ConversionResult(BaseModel):
    success: bool
    message: str
    athletes: int = 0
    results: int = 0
    events: int = 0
    meets: int = 0
    unmatched_clubs: List[Dict[str, Any]] = []  # List of unmatched club names from upload (unique names only)
    club_misses: List[Dict[str, Any]] = []  # Full list of club misses with context (meet_name, meet_city, etc.)
    name_format_mismatches: List[Dict[str, Any]] = []  # List of name format mismatches with athlete_id
    missing_athletes: List[Dict[str, Any]] = []  # List of missing athletes that need to be added to database

class ClubConversionResult(BaseModel):
    success: bool
    message: str
    states: int = 0
    clubs: int = 0
    inserted_states: int = 0
    skipped_states: int = 0
    inserted_clubs: int = 0
    skipped_clubs: int = 0

class SEAGUploadResult(BaseModel):
    success: bool
    message: str
    meet_id: Optional[str] = None
    meet_name: str = "SEA AGE Group Aquatics Championships"
    results_inserted: int = 0
    unmatched_athletes: List[Dict[str, Any]] = []  # Athletes not found in database
    errors: List[str] = []  # Any parsing errors

class AliasUpdate(BaseModel):
    alias: str


class AthleteSearchResponse(BaseModel):
    id: str
    name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    club_name: Optional[str] = None
    state_code: Optional[str] = None
    nation: Optional[str] = None


class AthleteUpdateRequest(BaseModel):
    name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    club_name: Optional[str] = None
    state_code: Optional[str] = None
    nation: Optional[str] = None

class ClubCreateRequest(BaseModel):
    club_name: str
    club_code: Optional[str] = None
    state_code: Optional[str] = None
    nation: Optional[str] = "MAS"
    alias: Optional[str] = None

class CoachCreateRequest(BaseModel):
    club_name: str
    name: str
    role: str  # 'head_coach', 'assistant_coach', 'manager'
    email: Optional[str] = None
    whatsapp: Optional[str] = None
    passport_photo: Optional[str] = None
    passport_number: Optional[str] = None
    ic: Optional[str] = None
    shoe_size: Optional[str] = None
    tshirt_size: Optional[str] = None
    tracksuit_size: Optional[str] = None
    course_level_1_sport_specific: bool = False
    course_level_2: bool = False
    course_level_3: bool = False
    course_level_1_isn: bool = False
    course_level_2_isn: bool = False
    course_level_3_isn: bool = False
    seminar_oct_2024: bool = False
    other_courses: Optional[str] = None
    state_coach: bool = False
    logbook_file: Optional[str] = None


class ManualResult(BaseModel):
    athlete_id: str
    distance: int
    stroke: str
    event_gender: str
    time_string: str
    place: Optional[int] = None


class ManualResultsSubmission(BaseModel):
    meet_name: str
    meet_date: str
    meet_city: str
    meet_course: str
    meet_alias: str
    results: List[ManualResult]


@router.get("/admin/test")
async def test_admin():
    """Test admin endpoint"""
    return {"message": "Admin router is working"}

@router.options("/admin/authenticate")
async def options_authenticate():
    """Handle CORS preflight for authenticate endpoint"""
    return {"ok": True}

@router.post("/admin/authenticate")
async def authenticate(request: AuthRequest):
    """Authenticate admin user"""
    if request.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Authentication successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

@router.post("/admin/convert-excel", response_model=ConversionResult)
async def convert_excel(
    file: UploadFile = File(...),
    meet_name: str = Form(None),
    meet_code: str = Form(None),
    existing_meet_id: str = Form(None)
):
    """Convert uploaded Excel file to database entries using fixed conversion script"""
    print(f"\n[UPLOAD REQUEST] Received: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Save uploaded file temporarily (stream in chunks to reduce startup delay and memory)
    print(f"[UPLOAD] Saving file to temporary location...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        temp_file_path = temp_file.name
        # Stream read in 1MB chunks
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            temp_file.write(chunk)
    print(f"[UPLOAD] File saved, starting processing...")
    
    try:
        # Process the file
        result = await process_uploaded_file(temp_file_path, file.filename, meet_name, meet_code, existing_meet_id)
        # Ensure a concrete JSON body is returned (avoid empty preview)
        try:
            body = result.dict() if hasattr(result, 'dict') else dict(result)
        except Exception:
            body = {
                "success": getattr(result, 'success', True),
                "message": getattr(result, 'message', "Conversion complete"),
                "athletes": getattr(result, 'athletes', 0),
                "results": getattr(result, 'results', 0),
                "events": getattr(result, 'events', 0),
                "meets": getattr(result, 'meets', 1),
            }
        return JSONResponse(content=body)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

@router.post("/admin/upload-seag", response_model=SEAGUploadResult)
async def upload_seag(file: UploadFile = File(...), year: str = Form("2025")):
    """Upload SEAG results from Excel file - matches athletes by name"""
    print(f"\n[SEAG UPLOAD] Received: {file.filename}")

    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    # Save uploaded file temporarily
    print(f"[SEAG UPLOAD] Saving file to temporary location...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        temp_file_path = temp_file.name
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            temp_file.write(chunk)

    print(f"[SEAG UPLOAD] File saved, starting processing...")

    try:
        import pandas as pd

        # Read Excel file
        try:
            df = pd.read_excel(temp_file_path, sheet_name="Sheet", skiprows=[0], header=0)
        except Exception as e:
            return SEAGUploadResult(
                success=False,
                message=f"Failed to read Excel file: {str(e)}",
                results_inserted=0,
                unmatched_athletes=[],
                errors=[str(e)]
            )

        print(f"[SEAG UPLOAD] Loaded {len(df)} rows from Excel")

        # Get database connection
        conn = get_database_connection()
        cursor = conn.cursor()

        # Create or get SEAG meet
        meet_name = f"SEA AGE Group Aquatics Championships {year}"
        meet_id = f"seag_{year.lower()}"
        meet_date = None

        # Try to extract meet date from first row if available
        if len(df) > 0 and 'MEETDATE' in df.columns:
            try:
                meet_date_raw = df.iloc[0].get('MEETDATE')
                if pd.notna(meet_date_raw):
                    meet_date = parse_and_validate_date(str(meet_date_raw), field_name="MEETDATE")
            except:
                pass

        # Ensure meet exists
        cursor.execute("SELECT id FROM meets WHERE id = ?", (meet_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO meets (id, name, meet_type, meet_date, location, city)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (meet_id, meet_name, "International", meet_date, "Singapore", "Singapore"))
            conn.commit()
            print(f"[SEAG UPLOAD] Created meet: {meet_id}")
        else:
            print(f"[SEAG UPLOAD] Meet already exists: {meet_id}")

        # Process results
        results_inserted = 0
        unmatched_athletes = []
        errors = []

        for idx, row in df.iterrows():
            try:
                # Extract data
                gender = str(row.get('GENDER', '')).strip().upper()[0] if pd.notna(row.get('GENDER')) else None
                distance = int(row.get('DISTANCE', 0)) if pd.notna(row.get('DISTANCE')) else None
                stroke = str(row.get('STROKE', '')).strip().upper() if pd.notna(row.get('STROKE')) else None
                fullname = str(row.get('FULLNAME', '')).strip() if pd.notna(row.get('FULLNAME')) else None
                time_str = str(row.get('SWIMTIME', '')).strip() if pd.notna(row.get('SWIMTIME')) else None
                year_age = int(row.get('AGE', 0)) if pd.notna(row.get('AGE')) else None

                # Validate required fields
                if not all([gender, distance, stroke, fullname, time_str]):
                    continue

                # Look up athlete
                cursor.execute("""
                    SELECT id FROM athletes
                    WHERE UPPER(TRIM(FULLNAME)) = ?
                    AND GENDER = ?
                    LIMIT 1
                """, (fullname.upper(), gender))
                athlete_row = cursor.fetchone()

                if not athlete_row:
                    unmatched_athletes.append({
                        'fullname': fullname,
                        'gender': gender,
                        'distance': distance,
                        'stroke': stroke,
                        'time': time_str
                    })
                    continue

                athlete_id = athlete_row[0]

                # Convert time to seconds
                try:
                    if ':' in time_str:
                        parts = time_str.split(':')
                        if len(parts) == 2:
                            minutes, seconds = parts
                            time_seconds = float(minutes) * 60 + float(seconds)
                        else:
                            continue
                    else:
                        time_seconds = float(time_str)
                except:
                    continue

                # Get or create event
                stroke_map = {"FR": "Free", "BK": "Back", "BR": "Breast", "FLY": "Fly", "IM": "IM"}
                stroke_name = stroke_map.get(stroke, stroke)

                cursor.execute("""
                    SELECT id FROM events
                    WHERE distance = ? AND stroke = ? AND gender = ?
                    LIMIT 1
                """, (distance, stroke_name, gender))
                event_row = cursor.fetchone()

                if event_row:
                    event_id = event_row[0]
                else:
                    event_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO events (id, distance, stroke, gender)
                        VALUES (?, ?, ?, ?)
                    """, (event_id, distance, stroke_name, gender))

                # Insert result
                result_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO results (
                        id, meet_id, athlete_id, event_id, time_seconds, place, course, year_age
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (result_id, meet_id, athlete_id, event_id, time_seconds, None, 'LCM', year_age))

                results_inserted += 1

            except Exception as e:
                errors.append(f"Row {idx+2}: {str(e)}")
                continue

        conn.commit()
        conn.close()

        return SEAGUploadResult(
            success=True,
            message=f"SEAG upload complete: {results_inserted} results inserted",
            meet_id=meet_id,
            meet_name=meet_name,
            results_inserted=results_inserted,
            unmatched_athletes=unmatched_athletes,
            errors=errors
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"SEAG upload failed: {str(e)}")

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

@router.get("/admin/meets")
async def get_meets():
    """Get list of all meets"""
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                m.id, 
                m.name, 
                m.meet_type as alias, 
                m.meet_date as date, 
                m.city,
                COUNT(r.id) as result_count
            FROM meets m
            LEFT JOIN results r ON m.id = r.meet_id
            GROUP BY m.id, m.name, m.meet_type, m.meet_date, m.city
            ORDER BY m.meet_date DESC
        """)
        meets_data = cursor.fetchall()
        
        meets = []
        for row in meets_data:
            meets.append({
                "id": row[0],
                "name": row[1],
                "alias": row[2] or "",
                "date": row[3] or "",
                "city": row[4] or "",
                "result_count": row[5] or 0
            })
        
        return {"meets": meets}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/admin/meets/{meet_id}/alias")
async def update_meet_alias(meet_id: str, alias_data: AliasUpdate):
    """
    Update the alias/meet_type for a specific meet.
    
    Args:
        meet_id: UUID of the meet to update
        alias_data: AliasUpdate model with 'alias' field containing the new alias/meet_type value
    
    Returns:
        JSON response with success message
    
    Raises:
        HTTPException 404: If meet not found
        HTTPException 500: If database error occurs
    """
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        # Verify meet exists
        cursor.execute("SELECT id, name FROM meets WHERE id = ?", (meet_id,))
        meet = cursor.fetchone()
        if not meet:
            raise HTTPException(status_code=404, detail="Meet not found")
        
        new_alias = alias_data.alias.strip() if alias_data.alias else ''
        
        # Update meet_type (alias) in database
        cursor.execute("UPDATE meets SET meet_type = ? WHERE id = ?", (new_alias, meet_id))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Successfully updated alias for meet '{meet[1]}' to '{new_alias}'."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating alias: {str(e)}")
    finally:
        conn.close()

@router.delete("/admin/meets/{meet_id}")
async def delete_meet(meet_id: str):
    """
    Delete a meet and all associated results.
    
    This function:
    1. Deletes all results associated with the meet
    2. Deletes the meet record itself
    3. Note: Athletes and events are NOT deleted (they may be used by other meets)
    
    Args:
        meet_id: UUID of the meet to delete
    
    Returns:
        JSON response with success message
    """
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        # Verify meet exists
        cursor.execute("SELECT id, name FROM meets WHERE id = ?", (meet_id,))
        meet = cursor.fetchone()
        if not meet:
            raise HTTPException(status_code=404, detail="Meet not found")
        
        meet_name = meet[1]
        
        # Delete all results for this meet
        cursor.execute("DELETE FROM results WHERE meet_id = ?", (meet_id,))
        results_deleted = cursor.rowcount
        
        # Delete the meet
        cursor.execute("DELETE FROM meets WHERE id = ?", (meet_id,))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Successfully deleted meet '{meet_name}' and {results_deleted} associated results."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting meet: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/meets/{meet_id}/pdf")
async def get_meet_pdf(meet_id: str):
    """
    Generate HTML report for a specific meet (printable PDF-like format).
    
    This endpoint:
    1. Retrieves all results for the specified meet from the database
    2. Groups results by event (distance + stroke + gender)
    3. Generates formatted HTML with meet information and results tables
    4. Returns HTML that can be viewed in browser or printed to PDF
    
    The HTML report includes:
    - Meet details (name, type, date, location, city)
    - Results grouped by event
    - For each result: Place, Athlete Name, Time, Age, Course
    
    Args:
        meet_id: UUID of the meet to generate report for
    
    Returns:
        HTMLResponse with formatted meet results report
    
    Raises:
        HTTPException 404: If meet not found
        HTTPException 500: If database error occurs
    """
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        # Get meet info
        cursor.execute("SELECT id, name, meet_type, meet_date, location, city FROM meets WHERE id = ?", (meet_id,))
        meet = cursor.fetchone()
        if not meet:
            raise HTTPException(status_code=404, detail="Meet not found")
        
        meet_name = meet[1]
        meet_type = meet[2] or ""
        meet_date = meet[3] or ""
        location = meet[4] or ""
        city = meet[5] or ""
        
        # Get all results for this meet
        # First, detect actual column names in the database
        cursor.execute("PRAGMA table_info(athletes)")
        athlete_columns = {row[1]: row[1] for row in cursor.fetchall()}
        athlete_gender_col = next((col for col in athlete_columns.values() if col.lower() == "gender"), "Gender")
        
        # Build query with detected column names
        # Note: Gender should come from events table (e.gender) as it represents the event's gender category
        query = f"""
            SELECT 
                a.FULLNAME as athlete_name,
                COALESCE(e.gender, a."{athlete_gender_col}") as gender,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.day_age,
                CASE 
                    WHEN r.year_age IS NOT NULL THEN r.year_age
                    WHEN a.BIRTHDATE IS NOT NULL AND r.result_meet_date IS NOT NULL THEN 
                        CAST(substr(r.result_meet_date,1,4) AS INTEGER) - CAST(substr(a.BIRTHDATE,1,4) AS INTEGER)
                    ELSE NULL
                END as year_age,
                r.course
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            WHERE r.meet_id = ?
              AND r.athlete_id IS NOT NULL
              AND r.event_id IS NOT NULL
            ORDER BY e.distance, e.stroke, e.gender, r.time_seconds_numeric ASC
        """
        cursor.execute(query, (meet_id,))
        results = cursor.fetchall()
        print(f"\n[PDF GENERATION] Meet ID: {meet_id}")
        print(f"[PDF GENERATION] Found {len(results)} results from database query")
        
        # Group results by event
        events_dict = {}
        for row in results:
            # row structure: (athlete_name, gender, distance, stroke, time_string, place, day_age, year_age, course)
            # Handle None values for event grouping
            distance = row[2] if row[2] is not None else 0
            stroke = row[3] if row[3] is not None else ''
            gender = row[1] if row[1] is not None else ''
            
            event_key = f"{distance}{stroke}{gender}"  # distance + stroke + gender
            if event_key not in events_dict:
                events_dict[event_key] = {
                    'distance': distance,
                    'stroke': stroke,
                    'gender': gender,
                    'results': [],
                    'seen': {}  # normalized_key -> index in results
                }
            athlete_name = row[0] or ''
            time_string = row[4] or ''
            
            # Skip only if athlete_name is truly empty - otherwise include all results
            if not athlete_name or not athlete_name.strip():
                continue
            
            # Simply append all results - no duplicate filtering
            # All results from the database query should be displayed
            events_dict[event_key]['results'].append({
                'athlete_name': athlete_name,
                'time_string': time_string,
                'place': row[5],
                'day_age': row[6],
                'year_age': row[7],
                'course': row[8]
            })
        
        # Generate fixed-width text format HTML
        # Format: Place (4 chars) + space + Name (30 chars) + space + Time (8 chars) + newline
        html = f"""
 <!DOCTYPE html>
 <html>
 <head>
     <meta charset="UTF-8">
     <title>{meet_name} - Results</title>
     <style>
        body {{ 
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 20px; 
            font-size: 12pt;
            line-height: 1.4;
        }}
        h1 {{ 
            color: #2c3e50; 
            margin-bottom: 20px; 
            font-size: 14pt;
        }}
        .columns {{
            column-count: 2;
            column-gap: 24px;
        }}
        .event-section {{ 
            margin-bottom: 16px; 
            page-break-inside: avoid;
            break-inside: avoid;
            -webkit-column-break-inside: avoid;
        }}
        .event-title {{ 
            font-size: 14pt; 
            font-weight: bold; 
            margin-bottom: 0;
            padding-bottom: 0;
            color: #34495e;
        }}
        .results-text {{
            font-family: 'Courier New', monospace;
            white-space: pre;
            font-size: 11pt;
            line-height: 1.0;
            margin-top: 0;
            padding-top: 0;
        }}
        @media print {{ 
            body {{ margin: 0; }}
            .event-section {{ page-break-inside: avoid; }}
        }}
     </style>
 </head>
 <body>
     <h1>{meet_name} {meet_date}</h1>
     <div class="columns">
"""
        
        # Stroke abbreviation mapping (matching frontend display)
        stroke_map = {
            'Fr': 'Free',
            'FR': 'Free',
            'FRE': 'Free',
            'Freestyle': 'Free',
            'Bk': 'Back',
            'BK': 'Back',
            'BAC': 'Back',
            'Backstroke': 'Back',
            'Br': 'Breast',
            'BR': 'Breast',
            'BRE': 'Breast',
            'Breaststroke': 'Breast',
            'Bu': 'Fly',
            'BU': 'Fly',
            'FLY': 'Fly',
            'Butterfly': 'Fly',
            'Me': 'IM',
            'ME': 'IM',
            'IM': 'IM',
            'Medley': 'IM'
        }
        
        # Gender mapping - handle various formats
        gender_map = {
            'M': "Men's",
            'F': "Women's",
            'MALE': "Men's",
            'FEMALE': "Women's",
            'MEN': "Men's",
            'WOMEN': "Women's"
        }
        
        # Custom sorting function for events
        def event_sort_key(event_key):
            """Sort by: 1) Gender (M before F), 2) Stroke (Free, Back, Breast, Fly, IM), 3) Distance (short to long)"""
            event_data = events_dict[event_key]
            stroke = event_data.get('stroke')
            distance = event_data.get('distance')
            gender = event_data.get('gender')
            
            # Handle None values
            stroke_str = (stroke or '').upper() if stroke is not None else ''
            gender_str = (gender or '').upper() if gender is not None else ''
            
            # Convert distance to int for proper numeric sorting (short to long)
            try:
                distance_int = int(distance) if distance is not None else 0
            except (ValueError, TypeError):
                distance_int = 0
            
            # Stroke order: Free=0, Back=1, Breast=2, Fly=3, IM=4
            # Events table uses full stroke names: "Free", "Back", "Breast", "Fly", "IM"
            stroke_lower = stroke_str.lower()
            
            # Determine stroke priority based on common patterns
            if stroke_lower.startswith('free') or stroke_lower in ('fr', 'fre', 'freestyle'):
                stroke_priority = 0  # Free
            elif stroke_lower.startswith('back') or stroke_lower in ('bk', 'bac', 'backstroke'):
                stroke_priority = 1  # Back
            elif stroke_lower.startswith('breast') or stroke_lower in ('br', 'bre', 'breaststroke'):
                stroke_priority = 2  # Breast
            elif stroke_lower.startswith('fly') or stroke_lower.startswith('butter') or stroke_lower in ('bu', 'fly', 'butterfly'):
                stroke_priority = 3  # Fly
            elif stroke_lower.startswith('im') or stroke_lower.startswith('medley') or stroke_lower in ('me', 'im', 'med', 'medley'):
                stroke_priority = 4  # IM
            else:
                stroke_priority = 5  # Unknown strokes go last
            
            # Gender priority: M=0 (Men's first), F=1 (Women's second)
            gender_priority = 0 if gender_str == 'M' else 1
            
            # Return sort tuple: (gender, stroke, distance)
            # This sorts: Men's before Women's, then Free/Back/Breast/Fly/IM, then short to long distance
            return (gender_priority, stroke_priority, distance_int)
        
        # Sort only the keys using the key function
        sorted_event_keys = sorted(events_dict.keys(), key=event_sort_key)
        for event_key in sorted_event_keys:
            event_data = events_dict[event_key]
            # Get course from first result (all results in same event have same course)
            course = event_data['results'][0]['course'] if event_data['results'] else 'LCM'
            course_str = course if course else 'LCM'
            
            # Format: "Men's 50m Freestyle LCM"
            stroke_val = event_data.get('stroke') or ''
            # Get gender and normalize - handle None, empty strings, and whitespace
            raw_gender = event_data.get('gender')
            if raw_gender:
                gender_val = str(raw_gender).strip().upper()
            else:
                gender_val = ''
            
            distance_val = event_data.get('distance') or 0
            
            stroke_full = stroke_map.get(stroke_val, stroke_val) if stroke_val else 'Unknown'
            
            # Map gender - check mappings with normalized value
            if gender_val:
                # Try exact match first
                gender_full = gender_map.get(gender_val)
                # If no match, try first character
                if not gender_full and len(gender_val) > 0:
                    gender_full = gender_map.get(gender_val[0])
            else:
                gender_full = None
            
            # Default to 'Unknown' if no mapping found
            if not gender_full:
                gender_full = 'Unknown'
            
            event_title = f"{gender_full} {distance_val}m {stroke_full} {course_str}"
            
            html += f"""    <div class="event-section">
        <div class="event-title">{event_title}</div>
        <div class="results-text">"""
            for idx, result in enumerate(event_data['results'], start=1):
                # Compute meet-specific place within this event (1..N), ignoring stored place from source
                place_str = str(idx).rjust(4)
                name_str = (result['athlete_name'] or '').ljust(30)[:30]  # Truncate or pad to 30 chars
                time_str = (result['time_string'] or '').rjust(8)[:8]  # Right-align to 8 chars
                age_val = result.get('year_age')
                age_str = (str(age_val).rjust(2) if age_val is not None else '  ')
                
                html += f"{place_str} {name_str} {age_str}  {time_str}\n"
            
            html += """</div>
    </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

async def process_uploaded_file(file_path: str, filename: str, meet_name: str, meet_code: str, existing_meet_id: str = None) -> ConversionResult:
    """Process uploaded Excel file and add to database"""
    
    print(f"\n{'='*60}", flush=True)
    print(f"[UPLOAD] Starting processing: {filename}", flush=True)
    print(f"[UPLOAD] Meet: {meet_name or 'N/A'}, Code: {meet_code or 'N/A'}", flush=True)
    print(f"{'='*60}", flush=True)
    
    # Determine if we're creating a new meet or adding to existing
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        
        if existing_meet_id:
            # Add to existing meet
            cursor.execute("SELECT * FROM meets WHERE id = ?", (existing_meet_id,))
            existing_meet = cursor.fetchone()
            if not existing_meet:
                raise HTTPException(status_code=404, detail="Existing meet not found")
            
            meet_info = {
                'id': existing_meet_id,
                'name': existing_meet[1],  # name
                'meet_type': existing_meet[2],  # meet_type
                'meet_date': existing_meet[3],  # meet_date
                'location': existing_meet[4],  # location
                'city': existing_meet[5] if len(existing_meet) > 5 else None,  # city
            }
        else:
            # Create new meet (will be updated with extracted info during processing)
            # Note: Do NOT set meet_type (alias) automatically - aliases must be set manually
            meet_info = {
                'id': str(uuid.uuid4()),
                'name': meet_name or 'Uploaded Meet',
                'meet_type': None,  # Don't auto-assign aliases - must be set manually
                'meet_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # ISO 8601 with UTC timezone
                'location': 'Uploaded Meet',
            }
    finally:
        conn.close()
    
    # Process the file using the conversion script with full validation
    # Note: We now continue processing even with validation errors and report issues in summary
    print(f"[PARSE] Reading Excel file...", flush=True)
    file_path_obj = Path(file_path)
    validation_issues = None
    try:
        athletes, results, events, collector = process_meet_file_simple(file_path_obj, meet_info)
        validation_issues = collector
        print(f"[PARSE] ✓ Parsed: {len(athletes)} athletes, {len(results)} results, {len(events)} events", flush=True)
        if validation_issues and hasattr(validation_issues, 'has_errors') and validation_issues.has_errors():
            error_count = (
                len(validation_issues.missing_athletes) +
                len(getattr(validation_issues, 'name_format_mismatches', [])) +
                len(validation_issues.birthdate_mismatches) +
                len(validation_issues.nation_mismatches) +
                len(validation_issues.club_misses) +
                len(validation_issues.event_misses)
            )
            print(f"[PARSE] ⚠ Found {error_count} validation issues (will be reported in summary)")
    except Exception as e:
        # If there's a different error, still raise it
        print(f"[PARSE] ✗ Error parsing file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    # After processing, check if meet with extracted name already exists (deduplication)
    if not existing_meet_id and meet_info.get('name'):
        conn = get_database_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, meet_date, city, meet_type FROM meets WHERE name = ?", (meet_info['name'],))
            existing_meet = cursor.fetchone()
            
            if existing_meet:
                # Use existing meet ID instead of creating duplicate
                meet_info['id'] = existing_meet[0]
                # Update meet_info with existing meet data
                if existing_meet[4]:  # meet_type
                    meet_info['meet_type'] = existing_meet[4]
                if existing_meet[2]:  # meet_date
                    meet_info['meet_date'] = existing_meet[2]
                if existing_meet[3]:  # city
                    meet_info['city'] = existing_meet[3]
        finally:
            conn.close()
    
    
    if not results:
        print(f"[UPLOAD] ✗ No results found in file")
        return ConversionResult(
            success=False,
            message="No valid swimming results found in the Excel file. Please check the file format."
        )
    
    # Insert into database: split results by meet_name to create separate meets
    print(f"[DB] Starting database insertion...")
    conn = get_database_connection()
    try:
        def norm_text(s: str) -> str:
            if s is None:
                return ''
            s = str(s).strip()
            return ' '.join(s.split())
        results_by_meet = {}
        mattioli_debug = []  # Track Mattioli results specifically
        for r in results:
            raw_name = r.get('meet_name') or meet_info.get('name') or 'Uploaded Meet'
            name_key = norm_text(raw_name)
            results_by_meet.setdefault(name_key, []).append(r)
            # Debug: track any result that might be Mattioli
            if 'mattioli' in raw_name.lower() or 'victorian' in raw_name.lower():
                mattioli_debug.append({
                    'raw_name': raw_name,
                    'normalized': name_key,
                    'sheet': r.get('sheet_name', '?'),
                    'row': r.get('excel_row', '?'),
                    'athlete': r.get('full_name', '?')
                })


        total_meets_created = 0
        per_meet_summaries = []
        print(f"[DB] Processing {len(results_by_meet)} meet group(s)...")
        for idx, (name, group) in enumerate(results_by_meet.items(), 1):
            print(f"[DB] [{idx}/{len(results_by_meet)}] Processing meet: '{name}' ({len(group)} results)")
            # Determine earliest date and city from group
            # Earliest date
            raw_dates = [r.get('result_meet_date') for r in group if r.get('result_meet_date')]
            parsed = []
            for d in raw_dates:
                for fmt in ('%Y-%m-%d','%d/%m/%Y','%d.%m.%Y','%Y/%m/%d','%d-%m-%Y'):
                    try:
                        parsed.append(datetime.strptime(str(d), fmt).strftime('%Y-%m-%d'))
                        break
                    except Exception:
                        pass
            earliest_date = min(parsed) if parsed else meet_info.get('meet_date')
            cities = [norm_text(r.get('meet_city')) for r in group if r.get('meet_city')]
            city = cities[0] if cities else norm_text(meet_info.get('city'))

            # Reuse existing meet if same name, city, and year exists
            # Note: Use year only (not full date) since meets span multiple days
            # Matching by full date causes men's and women's files for the same meet to not match
            # But we need the year to distinguish same meet name in different years
            cursor = conn.cursor()
            year = None
            if earliest_date:
                try:
                    # Extract year from earliest_date (format: YYYY-MM-DD or YYYY)
                    year = earliest_date[:4] if len(earliest_date) >= 4 else None
                except Exception:
                    pass
            
            # Match by name + city + year (extract year from meet_date in database)
            existing = None
            if city and year:
                # Extract year from meet_date column for comparison
                cursor.execute("""
                    SELECT id, meet_date, city, meet_type FROM meets 
                    WHERE name = ? AND city = ? 
                    AND substr(meet_date, 1, 4) = ?
                """, (name, city, year))
                existing = cursor.fetchone()
            # Fallback: name + city only (if year missing)
            if not existing and city:
                cursor.execute("SELECT id, meet_date, city, meet_type FROM meets WHERE name = ? AND city = ?", 
                             (name, city))
                existing = cursor.fetchone()
            # Last resort: name only (if city is missing)
            if not existing:
                cursor.execute("SELECT id, meet_date, city, meet_type FROM meets WHERE name = ?", (name,))
                existing = cursor.fetchone()
            
            if existing:
                # Use existing meet - preserve existing alias (meet_type), don't overwrite it
                existing_alias = existing[3]  # meet_type
                child_meet_info = {
                    'id': existing[0],
                    'name': name,
                    'meet_type': existing_alias,  # Preserve existing alias, don't overwrite
                    'meet_date': existing[1] or earliest_date,  # Use existing date if available
                    'location': meet_info.get('location'),
                    'city': existing[2] or city,  # Use existing city if available
                }
            else:
                # Create new meet - don't set alias automatically
                new_meet_id = str(uuid.uuid4())
                child_meet_info = {
                    'id': new_meet_id,
                    'name': name,
                    'meet_type': None,  # Don't auto-assign aliases
                    'meet_date': earliest_date,
                    'location': meet_info.get('location'),
                    'city': city,
                }

            # Update meet_id on group results to the child meet id
            meet_id_assigned = child_meet_info['id']
            for r in group:
                r['meet_id'] = meet_id_assigned

            # Insert and collect summary (pass collector to track skipped rows)
            print(f"[DB]   → Inserting {len(group)} results into database...")
            summary = insert_data_simple(conn, athletes, group, events, child_meet_info, collector=validation_issues)
            inserted = summary.get('inserted_results', 0)
            skipped = summary.get('skipped_results', 0)
            print(f"[DB]   ✓ Inserted: {inserted} new, {skipped} duplicates skipped")
            per_meet_summaries.append((name, child_meet_info['meet_date'], child_meet_info.get('city'), summary))
            total_meets_created += 0 if existing else 1

        # Build summary message with clear statistics
        lines = [f"Upload complete: {filename}\n"]
        total_inserted = 0
        total_skipped = 0
        for name, d, city, s in per_meet_summaries:
            ins = s.get('inserted_results', 0); sk = s.get('skipped_results', 0)
            total_inserted += ins
            total_skipped += sk
            city_str = f", {city}" if city else ""
            if ins > 0 or sk > 0:
                lines.append(f"  • {name} ({d}{city_str}): {ins} results added, {sk} duplicate results skipped (already in database)")
        
        # Add totals summary - emphasize duplicates and skipped rows
        if total_skipped > 0:
            lines.append(f"\n✓ Summary: {total_inserted} new results inserted, {total_skipped} duplicate results skipped (already in database)")
        else:
            lines.append(f"\n✓ Summary: {total_inserted} results inserted, no duplicates found")
        
        # Report validation issues as informational (not errors)
        # Group by meet for better readability
        if validation_issues and hasattr(validation_issues, 'has_errors') and validation_issues.has_errors():
            lines.append("\n" + "="*60)
            lines.append("VALIDATION ISSUES BY MEET")
            lines.append("="*60)
            
            # Create a mapping of meet names to their validation issues
            meets_with_issues = {}
            
            # Helper to get meet name from an issue
            def get_meet_name(issue, default="Unknown Meet"):
                # Try to get from meet_name field first
                meet = issue.get("meet_name", "")
                if meet and meet != "(unknown)":
                    return meet
                # Fallback to sheet name
                sheet = issue.get("sheet", "")
                if sheet:
                    # Try to match sheet name to a meet in per_meet_summaries
                    for name, _, _, _ in per_meet_summaries:
                        if name.lower() in sheet.lower() or sheet.lower() in name.lower():
                            return name
                return default
            
            # Group missing athletes by meet
            if validation_issues.missing_athletes:
                for athlete in validation_issues.missing_athletes:
                    meet_name = get_meet_name(athlete)
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["missing_athletes"].append(athlete)
            
            # Group name format mismatches by meet
            if hasattr(validation_issues, 'name_format_mismatches') and validation_issues.name_format_mismatches:
                for mismatch in validation_issues.name_format_mismatches:
                    meet_name = get_meet_name(mismatch)
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["name_format_mismatches"].append(mismatch)
            
            # Group birthdate mismatches by meet
            if validation_issues.birthdate_mismatches:
                for mismatch in validation_issues.birthdate_mismatches:
                    meet_name = get_meet_name(mismatch)
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["birthdate_mismatches"].append(mismatch)
            
            # Group nation mismatches by meet
            if validation_issues.nation_mismatches:
                for mismatch in validation_issues.nation_mismatches:
                    meet_name = get_meet_name(mismatch, "Other Issues")
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["nation_mismatches"].append(mismatch)
            
            # Group club misses by meet
            if validation_issues.club_misses:
                for miss in validation_issues.club_misses:
                    meet_name = get_meet_name(miss)
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["club_misses"].append(miss)
            
            # Group event misses by meet
            if validation_issues.event_misses:
                for miss in validation_issues.event_misses:
                    meet_name = get_meet_name(miss)
                    if meet_name not in meets_with_issues:
                        meets_with_issues[meet_name] = {"missing_athletes": [], "birthdate_mismatches": [], "nation_mismatches": [], "name_format_mismatches": [], "club_misses": [], "event_misses": []}
                    meets_with_issues[meet_name]["event_misses"].append(miss)
            
            # Display issues grouped by meet
            for meet_name in sorted(meets_with_issues.keys()):
                issues = meets_with_issues[meet_name]
                has_any = any(issues.values())
                if not has_any:
                    continue
                
                lines.append(f"\n{meet_name}:")
                lines.append("-" * 60)
                
                # Missing athletes - NEED TO BE ADDED
                if issues["missing_athletes"]:
                    lines.append(f"  ⚠️ MISSING ATHLETES - NEED TO BE ADDED TO DATABASE ({len(issues['missing_athletes'])} rows):")
                    for athlete in issues["missing_athletes"][:20]:  # First 20
                        sheet = athlete.get("sheet", "Unknown")
                        row = athlete.get("row", "?")
                        full_name = athlete.get("full_name", "Unknown")
                        birthdate = athlete.get("birthdate", "(blank)")
                        gender = athlete.get("gender", "(blank)")
                        lines.append(f"    • {sheet} row {row}: {full_name} (Birthdate: {birthdate}, Gender: {gender}) - ADD TO DATABASE")
                    if len(issues["missing_athletes"]) > 20:
                        lines.append(f"    ... and {len(issues['missing_athletes']) - 20} more missing athletes that need to be added")
                    lines.append("")
                    lines.append("  ⚠️ ACTION REQUIRED: These athletes are not in the database.")
                    lines.append("     Add them to the athlete table before uploading results.")
                
                # Birthdate mismatches
                if issues["birthdate_mismatches"]:
                    lines.append(f"  Birthdate Mismatches ({len(issues['birthdate_mismatches'])} rows):")
                    for mismatch in issues["birthdate_mismatches"][:20]:  # First 20
                        sheet = mismatch.get("sheet", "Unknown")
                        row = mismatch.get("row", "?")
                        full_name = mismatch.get("full_name", "Unknown")
                        excel_bday = mismatch.get("workbook_birthdate", "(blank)")
                        db_bday = mismatch.get("database_birthdate", "(blank)")
                        athlete_id = mismatch.get("athlete_id", "(unknown)")
                        lines.append(f"    • {sheet} row {row}: {full_name} (athlete_id: {athlete_id}) - Excel: {excel_bday} ≠ Database: {db_bday}")
                    if len(issues["birthdate_mismatches"]) > 20:
                        lines.append(f"    ... and {len(issues['birthdate_mismatches']) - 20} more birthdate mismatches")
                
                # Nation mismatches
                if issues["nation_mismatches"]:
                    lines.append(f"  Nation Mismatches ({len(issues['nation_mismatches'])} rows):")
                    for mismatch in issues["nation_mismatches"][:20]:  # First 20
                        sheet = mismatch.get("sheet", "Unknown")
                        row = mismatch.get("row", "?")
                        full_name = mismatch.get("full_name", "Unknown")
                        excel_nation = mismatch.get("workbook_nation", "(blank)")
                        db_nation = mismatch.get("database_nation", "(blank)")
                        athlete_id = mismatch.get("athlete_id", "(unknown)")
                        lines.append(f"    • {sheet} row {row}: {full_name} (athlete_id: {athlete_id}) - Excel: {excel_nation} ≠ Database: {db_nation}")
                    if len(issues["nation_mismatches"]) > 20:
                        lines.append(f"    ... and {len(issues['nation_mismatches']) - 20} more nation mismatches")
                
                # Name format mismatches (exact FULLNAME doesn't match but normalized does)
                if issues.get("name_format_mismatches"):
                    lines.append(f"  Name Format Mismatches ({len(issues['name_format_mismatches'])} rows - case/format differences):")
                    for mismatch in issues["name_format_mismatches"][:20]:  # First 20
                        sheet = mismatch.get("sheet", "Unknown")
                        row = mismatch.get("row", "?")
                        upload_name = mismatch.get("upload_fullname", "Unknown")
                        db_name = mismatch.get("database_fullname", "Unknown")
                        lines.append(f"    • {sheet} row {row}: Upload='{upload_name}' ≠ Database='{db_name}'")
                    if len(issues["name_format_mismatches"]) > 20:
                        lines.append(f"    ... and {len(issues['name_format_mismatches']) - 20} more name format mismatches")
                
                # Club misses
                if issues["club_misses"]:
                    lines.append(f"  Unknown Clubs/Teams ({len(issues['club_misses'])} rows - results created with null club fields):")
                    for miss in issues["club_misses"][:20]:  # First 20
                        sheet = miss.get("sheet", "Unknown")
                        row = miss.get("row", "?")
                        full_name = miss.get("full_name", "Unknown")
                        club_name = miss.get("club_name", "(blank)")
                        athlete_id = miss.get("athlete_id", "(unknown)")
                        lines.append(f"    • {sheet} row {row}: {full_name} (athlete_id: {athlete_id}) - Club not found: {club_name}")
                    if len(issues["club_misses"]) > 20:
                        lines.append(f"    ... and {len(issues['club_misses']) - 20} more unknown clubs")
                
                # Event misses
                if issues["event_misses"]:
                    lines.append(f"  Unknown Events ({len(issues['event_misses'])} rows):")
                    for miss in issues["event_misses"][:20]:  # First 20
                        sheet = miss.get("sheet", "Unknown")
                        row = miss.get("row", "?")
                        description = miss.get("description", "Unknown event")
                        lines.append(f"    • {sheet} row {row}: {description}")
                    if len(issues["event_misses"]) > 20:
                        lines.append(f"    ... and {len(issues['event_misses']) - 20} more unknown events")
                
                # Skipped rows (duplicates and other reasons) - only show if there are any
                if hasattr(validation_issues, 'skipped_rows') and validation_issues.skipped_rows:
                    # Group skipped rows by reason for this meet
                    skipped_by_reason = {}
                    for skipped in validation_issues.skipped_rows:
                        reason = skipped.get("reason", "Unknown reason")
                        if reason not in skipped_by_reason:
                            skipped_by_reason[reason] = []
                        # Only include if it's for this meet (check sheet name matches meet name pattern)
                        skipped_sheet = skipped.get("sheet", "")
                        if not meet_name or meet_name == "Unknown Meet" or meet_name.lower() in skipped_sheet.lower() or skipped_sheet.lower() in meet_name.lower():
                            skipped_by_reason[reason].append(skipped)
                    
                    if skipped_by_reason:
                        total_skipped_for_meet = sum(len(rows) for rows in skipped_by_reason.values())
                        lines.append(f"\n  Skipped Rows ({total_skipped_for_meet} rows - not uploaded):")
                        for reason, rows in skipped_by_reason.items():
                            lines.append(f"    • {reason}: {len(rows)} row(s)")
                            # Show first 5 examples of each reason
                            for skipped in rows[:5]:
                                sheet = skipped.get("sheet", "Unknown")
                                row = skipped.get("row", "?")
                                full_name = skipped.get("full_name", "Unknown")
                                lines.append(f"      - {sheet} row {row}: {full_name}")
                            if len(rows) > 5:
                                lines.append(f"      ... and {len(rows) - 5} more rows with this reason")
            
            lines.append("\n" + "="*60)
        
        message = "\n".join(lines)
        
        # Final summary
        total_inserted = sum(s.get('inserted_results', 0) for _, _, _, s in per_meet_summaries)
        total_skipped = sum(s.get('skipped_results', 0) for _, _, _, s in per_meet_summaries)
        print(f"\n{'='*60}")
        print(f"[UPLOAD] ✓ Complete!")
        print(f"[UPLOAD]   Total inserted: {total_inserted} results")
        print(f"[UPLOAD]   Total skipped (duplicates): {total_skipped} results")
        print(f"[UPLOAD]   Meets processed: {len(results_by_meet)}")
        print(f"{'='*60}\n")
        
        # Extract unmatched clubs and name format mismatches from validation collector
        unmatched_clubs_list = []
        club_misses_list = []
        name_format_mismatches_list = []
        if validation_issues:
            if hasattr(validation_issues, 'club_misses'):
                # Get unique unmatched club names (for backward compatibility)
                seen_clubs = set()
                for club_miss in validation_issues.club_misses:
                    club_name = club_miss.get('club_name', '').strip()
                    if club_name and club_name not in seen_clubs and club_name != '(blank)':
                        seen_clubs.add(club_name)
                        unmatched_clubs_list.append({
                            'club_name': club_name,
                            'state_code': None  # Could extract from club name if needed
                        })
                    # Also include full club miss data with context
                    if club_name and club_name != '(blank)':
                        club_misses_list.append(club_miss)
            if hasattr(validation_issues, 'name_format_mismatches'):
                # Get name format mismatches with athlete_id
                for mismatch in validation_issues.name_format_mismatches:
                    if mismatch.get('athlete_id'):
                        name_format_mismatches_list.append(mismatch)
        
        # Extract missing athletes from validation collector
        missing_athletes_list = []
        if validation_issues and hasattr(validation_issues, 'missing_athletes'):
            missing_athletes_list = validation_issues.missing_athletes
            
            # Automatically save missing athletes to JSON file for easy access
            if missing_athletes_list:
                import json
                output_file = project_root / "missing_athletes_latest.json"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "timestamp": datetime.now().isoformat(),
                            "filename": filename,
                            "missing_athletes": missing_athletes_list
                        }, f, indent=2, ensure_ascii=False)
                    print(f"[SAVE] Saved {len(missing_athletes_list)} missing athletes to: {output_file}", flush=True)
                except Exception as e:
                    print(f"[WARN] Failed to save missing athletes to file: {e}", flush=True)
        
        return ConversionResult(
            success=True,
            message=message,
            athletes=len(athletes),
            results=len(results),
            events=len(events),
            meets=max(1, len(results_by_meet)),
            unmatched_clubs=unmatched_clubs_list,
            club_misses=club_misses_list,
            name_format_mismatches=name_format_mismatches_list,
            missing_athletes=missing_athletes_list,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    finally:
        conn.close()

@router.post("/admin/convert-clubs", response_model=ClubConversionResult)
async def convert_clubs_excel(file: UploadFile = File(...)):
    """Convert uploaded Clubs_By_State.xlsx file to database entries"""
    
    print(f"[club upload] Received request for file: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Save uploaded file temporarily by streaming
    temp_file_path = None
    try:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            print(f"[club upload] Received file '{file.filename}', starting save to '{temp_file_path}'")
            # Stream file in chunks
            chunk_size = 1024 * 1024  # 1MB
            total_saved = 0
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)
                total_saved += len(chunk)
            print(f"[club upload] Saved {total_saved} bytes for '{file.filename}'")
        
        # Process the file
        print(f"[club upload] Processing '{file.filename}'...")
        try:
            # Quick validation before processing - check file structure
            import pandas as pd
            quick_check = pd.ExcelFile(temp_file_path, engine='xlrd' if suffix == '.xls' else None)
            sheet_names_check = quick_check.sheet_names[:5]  # Check first 5 sheets
            
            # Check if this looks like a meet results file
            meet_indicators = ['50M', '100M', '200M', '400M', '800M', '1500M', 'FR', 'BK', 'BR', 'BU', 'ME', 'IM']
            has_meet_indicators = any(any(ind in str(s).upper() for ind in meet_indicators) for s in sheet_names_check)
            state_code_sheets = [s for s in sheet_names_check if len(str(s).strip().upper()) >= 2 and len(str(s).strip().upper()) <= 3]
            
            if has_meet_indicators and len(state_code_sheets) == 0:
                raise HTTPException(status_code=400, detail="This appears to be a meet results file (has event sheets like '50m Fr', '100m Fr'), not a Clubs_By_State file. Please upload this to the 'Upload & Convert Meet' tab instead. Clubs_By_State files should have sheets named with state codes (e.g., 'KL', 'SGR', 'JHR').")
            
            data = process_clubs_file(temp_file_path)
            print(f"[club upload] Processed: {len(data.get('states', []))} states, {len(data.get('clubs', []))} clubs")
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except ValueError as ve:
            # This is a file structure validation error
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
        
        # Insert into database
        conn = get_database_connection()
        try:
            result = insert_club_data(conn, data['states'], data['clubs'])
            print(f"[club upload] Inserted: {result['inserted_states']} states, {result['inserted_clubs']} clubs")
            print(f"[club upload] Skipped: {result['skipped_states']} states, {result['skipped_clubs']} clubs")
            
            message = (f"Successfully converted {file.filename}.\n"
                      f"{result['inserted_states']} states added, {result['skipped_states']} states skipped\n"
                      f"{result['inserted_clubs']} clubs added, {result['skipped_clubs']} clubs skipped")
            
            return ClubConversionResult(
                success=True,
                message=message,
                states=len(data['states']),
                clubs=len(data['clubs']),
                inserted_states=result['inserted_states'],
                skipped_states=result['skipped_states'],
                inserted_clubs=result['inserted_clubs'],
                skipped_clubs=result['skipped_clubs']
            )
        finally:
            conn.close()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"[club upload] Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"[club upload] Error cleaning up temporary file {temp_file_path}: {e}")


@router.get("/admin/athletes/search")
async def search_athletes(q: str = ""):
    """Search athletes by name (case-insensitive)."""
    query = (q or "").strip()
    if not query:
        return {"athletes": []}

    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        pattern = f"%{query.upper()}%"
        cursor.execute(
            """
            SELECT id, FULLNAME, Gender, BIRTHDATE, ClubName, ClubCode, NATION
            FROM athletes
            WHERE UPPER(FULLNAME) LIKE ?
            ORDER BY FULLNAME
            LIMIT 50
            """,
            (pattern,)
        )
        rows = cursor.fetchall()
        athletes = []
        for row in rows:
            athletes.append({
                "id": row[0],
                "name": row[1] or "",
                "gender": row[2] or "",
                "birth_date": row[3] or None,
                "club_name": row[4] or None,
                "state_code": row[5] or None,
                "nation": row[6] or None,
            })
        return {"athletes": athletes}
    finally:
        conn.close()


@router.get("/admin/athletes/{athlete_id}")
async def get_athlete_detail(athlete_id: str):
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, gender, birth_date, club_name, state_code, nation
            FROM athletes
            WHERE id = ?
            """,
            (athlete_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Athlete not found")
        athlete = {
            "id": row[0],
            "name": row[1] or "",
            "gender": row[2] or "",
            "birth_date": row[3] or None,
            "club_name": row[4] or None,
            "state_code": row[5] or None,
            "nation": row[6] or None,
        }
        return {"athlete": athlete}
    finally:
        conn.close()


@router.patch("/admin/athletes/{athlete_id}")
async def update_athlete(athlete_id: str, payload: AthleteUpdateRequest):
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM athletes WHERE id = ?", (athlete_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Athlete not found")

        cursor.execute(
            """
            UPDATE athletes
            SET name = ?,
                gender = ?,
                birth_date = ?,
                club_name = ?,
                state_code = ?,
                nation = ?
            WHERE id = ?
            """,
            (
                payload.name.strip(),
                (payload.gender or "").strip() or None,
                payload.birth_date.strip() if payload.birth_date else None,
                payload.club_name.strip() if payload.club_name else None,
                payload.state_code.strip().upper() if payload.state_code else None,
                payload.nation.strip().upper() if payload.nation else None,
                athlete_id,
            ),
        )
        conn.commit()
        return {"success": True, "message": "Athlete updated"}
    except HTTPException:
        raise
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update athlete: {exc}")
    finally:
        conn.close()

@router.get("/admin/clubs/unmatched")
async def get_unmatched_clubs():
    """Get list of unmatched clubs from the last upload (stored in validation collector)"""
    # For now, we'll query results table for clubs that weren't matched
    # In the future, we could store unmatched clubs in a separate table
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Get unique club names from results where team_name is NULL (unmatched)
        # But we need to track what the original club name was
        # For now, let's get clubs that appear in results but not in clubs table
        cursor.execute("""
            SELECT DISTINCT r.team_name as unmatched_name, r.team_state_code
            FROM results r
            LEFT JOIN clubs c ON UPPER(TRIM(r.team_name)) = UPPER(TRIM(c.club_name))
            WHERE r.team_name IS NOT NULL 
            AND r.team_name != ''
            AND c.club_name IS NULL
            ORDER BY r.team_name
        """)
        
        unmatched = []
        for row in cursor.fetchall():
            unmatched.append({
                "club_name": row[0],
                "state_code": row[1] if row[1] else None
            })
        
        return {"unmatched_clubs": unmatched, "count": len(unmatched)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unmatched clubs: {str(e)}")
    finally:
        conn.close()

@router.post("/admin/clubs")
async def create_club(club: ClubCreateRequest):
    """Create a new club in the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if club already exists (case-insensitive)
        cursor.execute(
            "SELECT club_name FROM clubs WHERE UPPER(TRIM(club_name)) = ?",
            (club.club_name.upper().strip(),)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"Club '{club.club_name}' already exists")
        
        # Check if alias column exists
        cursor.execute("PRAGMA table_info(clubs)")
        columns = {row[1].lower() for row in cursor.fetchall()}
        has_alias = 'alias' in columns
        
        # Insert new club
        if has_alias:
            cursor.execute("""
                INSERT INTO clubs (club_name, club_code, state_code, nation, alias)
                VALUES (?, ?, ?, ?, ?)
            """, (
                club.club_name.strip(),
                club.club_code.strip() if club.club_code else None,
                club.state_code.strip().upper() if club.state_code else None,
                club.nation.strip().upper() if club.nation else "MAS",
                club.alias.strip() if club.alias else None
            ))
        else:
            cursor.execute("""
                INSERT INTO clubs (club_name, club_code, state_code, nation)
                VALUES (?, ?, ?, ?)
            """, (
                club.club_name.strip(),
                club.club_code.strip() if club.club_code else None,
                club.state_code.strip().upper() if club.state_code else None,
                club.nation.strip().upper() if club.nation else "MAS"
            ))
        
        conn.commit()
        return {"success": True, "message": f"Club '{club.club_name}' created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create club: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/clubs")
async def list_clubs(state_code: Optional[str] = None):
    """List all clubs in the database, optionally filtered by state_code"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if alias column exists
        cursor.execute("PRAGMA table_info(clubs)")
        columns = {row[1].lower() for row in cursor.fetchall()}
        has_alias = 'alias' in columns
        
        # Build query with optional state filter
        if state_code:
            if has_alias:
                cursor.execute(
                    "SELECT club_name, club_code, state_code, nation, alias FROM clubs WHERE state_code = ? ORDER BY club_name",
                    (state_code.upper(),)
                )
            else:
                cursor.execute(
                    "SELECT club_name, club_code, state_code, nation FROM clubs WHERE state_code = ? ORDER BY club_name",
                    (state_code.upper(),)
                )
        else:
            if has_alias:
                cursor.execute("SELECT club_name, club_code, state_code, nation, alias FROM clubs ORDER BY club_name")
            else:
                cursor.execute("SELECT club_name, club_code, state_code, nation FROM clubs ORDER BY club_name")
        
        clubs = []
        for row in cursor.fetchall():
            club = {
                "club_name": row[0],
                "club_code": row[1],
                "state_code": row[2],
                "nation": row[3]
            }
            if has_alias and len(row) > 4:
                club["alias"] = row[4]
            clubs.append(club)
        
        return {"clubs": clubs, "count": len(clubs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list clubs: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/clubs/states")
async def list_states():
    """Get list of unique state codes from clubs"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT state_code FROM clubs WHERE state_code IS NOT NULL AND state_code != '' ORDER BY state_code")
        states = [row[0] for row in cursor.fetchall()]
        return {"states": states}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list states: {str(e)}")
    finally:
        conn.close()

@router.put("/admin/clubs/{club_name}")
async def update_club(club_name: str, club: ClubCreateRequest):
    """Update an existing club in the database"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if club exists
        cursor.execute(
            "SELECT club_name FROM clubs WHERE club_name = ?",
            (club_name,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Club '{club_name}' not found")
        
        # Check if alias column exists
        cursor.execute("PRAGMA table_info(clubs)")
        columns = {row[1].lower() for row in cursor.fetchall()}
        has_alias = 'alias' in columns
        
        # Update club
        if has_alias:
            cursor.execute("""
                UPDATE clubs 
                SET club_name = ?, club_code = ?, state_code = ?, nation = ?, alias = ?
                WHERE club_name = ?
            """, (
                club.club_name.strip(),
                club.club_code.strip() if club.club_code else None,
                club.state_code.strip().upper() if club.state_code else None,
                club.nation.strip().upper() if club.nation else "MAS",
                club.alias.strip() if club.alias else None,
                club_name  # WHERE clause uses original name
            ))
        else:
            cursor.execute("""
                UPDATE clubs 
                SET club_name = ?, club_code = ?, state_code = ?, nation = ?
                WHERE club_name = ?
            """, (
                club.club_name.strip(),
                club.club_code.strip() if club.club_code else None,
                club.state_code.strip().upper() if club.state_code else None,
                club.nation.strip().upper() if club.nation else "MAS",
                club_name  # WHERE clause uses original name
            ))
        
        conn.commit()
        return {"success": True, "message": f"Club '{club.club_name}' updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update club: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/coaches")
async def list_coaches(club_name: Optional[str] = None, name: Optional[str] = None):
    """List coaches, optionally filtered by club_name or name"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT id, club_name, name, role, email, whatsapp,
                   passport_photo, passport_number, ic, shoe_size, tshirt_size, tracksuit_size,
                   course_level_1_sport_specific, course_level_2, course_level_3,
                   course_level_1_isn, course_level_2_isn, course_level_3_isn,
                   seminar_oct_2024, other_courses, state_coach, logbook_file,
                   created_at, updated_at
            FROM coaches
            WHERE 1=1
        """
        params = []
        
        if club_name:
            query += " AND club_name = ?"
            params.append(club_name)
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        query += " ORDER BY club_name, name"
        
        cursor.execute(query, params)
        coaches = []
        for row in cursor.fetchall():
            coaches.append({
                "id": row[0],
                "club_name": row[1],
                "name": row[2],
                "role": row[3],
                "email": row[4],
                "whatsapp": row[5],
                "passport_photo": row[6],
                "passport_number": row[7],
                "ic": row[8],
                "shoe_size": row[9],
                "tshirt_size": row[10],
                "tracksuit_size": row[11],
                "course_level_1_sport_specific": bool(row[12]),
                "course_level_2": bool(row[13]),
                "course_level_3": bool(row[14]),
                "course_level_1_isn": bool(row[15]),
                "course_level_2_isn": bool(row[16]),
                "course_level_3_isn": bool(row[17]),
                "seminar_oct_2024": bool(row[18]),
                "other_courses": row[19],
                "state_coach": bool(row[20]),
                "logbook_file": row[21],
                "created_at": row[22],
                "updated_at": row[23]
            })
        
        return {"coaches": coaches, "count": len(coaches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list coaches: {str(e)}")
    finally:
        conn.close()

@router.post("/admin/coaches")
async def create_coach(coach: CoachCreateRequest):
    """Create a new coach"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO coaches (
                club_name, name, role, email, whatsapp,
                passport_photo, passport_number, ic, shoe_size, tshirt_size, tracksuit_size,
                course_level_1_sport_specific, course_level_2, course_level_3,
                course_level_1_isn, course_level_2_isn, course_level_3_isn,
                seminar_oct_2024, other_courses, state_coach, logbook_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            coach.club_name.strip(),
            coach.name.strip(),
            coach.role.strip(),
            coach.email.strip() if coach.email else None,
            coach.whatsapp.strip() if coach.whatsapp else None,
            coach.passport_photo.strip() if coach.passport_photo else None,
            coach.passport_number.strip() if coach.passport_number else None,
            coach.ic.strip() if coach.ic else None,
            coach.shoe_size.strip() if coach.shoe_size else None,
            coach.tshirt_size.strip() if coach.tshirt_size else None,
            coach.tracksuit_size.strip() if coach.tracksuit_size else None,
            1 if coach.course_level_1_sport_specific else 0,
            1 if coach.course_level_2 else 0,
            1 if coach.course_level_3 else 0,
            1 if coach.course_level_1_isn else 0,
            1 if coach.course_level_2_isn else 0,
            1 if coach.course_level_3_isn else 0,
            1 if coach.seminar_oct_2024 else 0,
            coach.other_courses.strip() if coach.other_courses else None,
            1 if coach.state_coach else 0,
            coach.logbook_file.strip() if coach.logbook_file else None
        ))
        
        conn.commit()
        return {"success": True, "message": f"Coach '{coach.name}' created successfully", "id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create coach: {str(e)}")
    finally:
        conn.close()

@router.put("/admin/coaches/{coach_id}")
async def update_coach(coach_id: int, coach: CoachCreateRequest):
    """Update an existing coach"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if coach exists
        cursor.execute("SELECT id FROM coaches WHERE id = ?", (coach_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Coach with id {coach_id} not found")
        
        cursor.execute("""
            UPDATE coaches SET
                club_name = ?, name = ?, role = ?, email = ?, whatsapp = ?,
                passport_photo = ?, passport_number = ?, ic = ?, shoe_size = ?, tshirt_size = ?, tracksuit_size = ?,
                course_level_1_sport_specific = ?, course_level_2 = ?, course_level_3 = ?,
                course_level_1_isn = ?, course_level_2_isn = ?, course_level_3_isn = ?,
                seminar_oct_2024 = ?, other_courses = ?, state_coach = ?, logbook_file = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            coach.club_name.strip(),
            coach.name.strip(),
            coach.role.strip(),
            coach.email.strip() if coach.email else None,
            coach.whatsapp.strip() if coach.whatsapp else None,
            coach.passport_photo.strip() if coach.passport_photo else None,
            coach.passport_number.strip() if coach.passport_number else None,
            coach.ic.strip() if coach.ic else None,
            coach.shoe_size.strip() if coach.shoe_size else None,
            coach.tshirt_size.strip() if coach.tshirt_size else None,
            coach.tracksuit_size.strip() if coach.tracksuit_size else None,
            1 if coach.course_level_1_sport_specific else 0,
            1 if coach.course_level_2 else 0,
            1 if coach.course_level_3 else 0,
            1 if coach.course_level_1_isn else 0,
            1 if coach.course_level_2_isn else 0,
            1 if coach.course_level_3_isn else 0,
            1 if coach.seminar_oct_2024 else 0,
            coach.other_courses.strip() if coach.other_courses else None,
            1 if coach.state_coach else 0,
            coach.logbook_file.strip() if coach.logbook_file else None,
            coach_id
        ))
        
        conn.commit()
        return {"success": True, "message": f"Coach '{coach.name}' updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update coach: {str(e)}")
    finally:
        conn.close()

@router.delete("/admin/coaches/{coach_id}")
async def delete_coach(coach_id: int):
    """Delete a coach"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM coaches WHERE id = ?", (coach_id,))
        coach = cursor.fetchone()
        if not coach:
            raise HTTPException(status_code=404, detail=f"Coach with id {coach_id} not found")
        
        cursor.execute("DELETE FROM coaches WHERE id = ?", (coach_id,))
        conn.commit()
        return {"success": True, "message": f"Coach '{coach[0]}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete coach: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/clubs/search")
async def search_clubs(query: str = Query(..., min_length=2)):
    """Search for clubs by name (case-insensitive partial match)"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT club_name, club_code, state_code, nation, alias
            FROM clubs
            WHERE LOWER(club_name) LIKE LOWER(?) OR LOWER(club_code) LIKE LOWER(?)
            ORDER BY club_name
            LIMIT 20
        """, (f"%{query}%", f"%{query}%"))
        
        results = cursor.fetchall()
        clubs = []
        for row in results:
            clubs.append({
                "club_name": row[0],
                "club_code": row[1],
                "state_code": row[2],
                "nation": row[3],
                "alias": row[4]
            })
        
        return {"clubs": clubs, "count": len(clubs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search clubs: {str(e)}")
    finally:
        conn.close()

class ClubResolutionRequest(BaseModel):
    club_miss_id: Optional[str] = None  # Identifier for the club miss (e.g., index or hash)
    action: str  # "add_alias", "swap_names", or "create_new"
    existing_club_name: Optional[str] = None  # Required for add_alias and swap_names
    new_club_name: Optional[str] = None  # Required for create_new
    club_code: Optional[str] = None
    state_code: Optional[str] = None
    nation: str = "MAS"

@router.post("/admin/clubs/resolve-miss")
async def resolve_club_miss(resolution: ClubResolutionRequest):
    """Resolve a club miss by adding alias, swapping names, or creating new club"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if alias column exists
        cursor.execute("PRAGMA table_info(clubs)")
        columns = [row[1].lower() for row in cursor.fetchall()]
        has_alias = "alias" in columns
        
        if not has_alias:
            cursor.execute("ALTER TABLE clubs ADD COLUMN alias TEXT")
        
        if resolution.action == "add_alias":
            # Add the read-in name as an alias to existing club
            if not resolution.existing_club_name:
                raise HTTPException(status_code=400, detail="existing_club_name required for add_alias action")
            
            # Get current alias
            cursor.execute("SELECT alias FROM clubs WHERE club_name = ?", (resolution.existing_club_name,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Club '{resolution.existing_club_name}' not found")
            
            current_alias = row[0] or ""
            # The "read-in name" should be passed as new_club_name (the name from Excel)
            new_alias = resolution.new_club_name or ""
            
            if new_alias:
                if current_alias:
                    updated_alias = f"{current_alias}, {new_alias}"
                else:
                    updated_alias = new_alias
                
                cursor.execute("UPDATE clubs SET alias = ? WHERE club_name = ?", (updated_alias, resolution.existing_club_name))
                conn.commit()
                return {"success": True, "message": f"Added '{new_alias}' as alias to '{resolution.existing_club_name}'"}
        
        elif resolution.action == "swap_names":
            # Make read-in name the club_name and existing club_name the alias
            if not resolution.existing_club_name or not resolution.new_club_name:
                raise HTTPException(status_code=400, detail="Both existing_club_name and new_club_name required for swap_names action")
            
            # Check if new name already exists
            cursor.execute("SELECT club_name FROM clubs WHERE club_name = ?", (resolution.new_club_name,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Club '{resolution.new_club_name}' already exists")
            
            # Get current alias
            cursor.execute("SELECT alias FROM clubs WHERE club_name = ?", (resolution.existing_club_name,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Club '{resolution.existing_club_name}' not found")
            
            current_alias = row[0] or ""
            # Add old club_name to alias
            if current_alias:
                updated_alias = f"{current_alias}, {resolution.existing_club_name}"
            else:
                updated_alias = resolution.existing_club_name
            
            # Update club_name and alias
            cursor.execute("""
                UPDATE clubs 
                SET club_name = ?, alias = ?
                WHERE club_name = ?
            """, (resolution.new_club_name, updated_alias, resolution.existing_club_name))
            conn.commit()
            return {"success": True, "message": f"Swapped names: '{resolution.existing_club_name}' -> '{resolution.new_club_name}' (old name added as alias)"}
        
        elif resolution.action == "create_new":
            # Create a new club
            if not resolution.new_club_name:
                raise HTTPException(status_code=400, detail="new_club_name required for create_new action")
            
            # Check if club already exists
            cursor.execute("SELECT club_name FROM clubs WHERE LOWER(club_name) = LOWER(?)", (resolution.new_club_name,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Club '{resolution.new_club_name}' already exists")
            
            cursor.execute("""
                INSERT INTO clubs (club_name, club_code, state_code, nation, alias)
                VALUES (?, ?, ?, ?, ?)
            """, (
                resolution.new_club_name,
                resolution.club_code,
                resolution.state_code,
                resolution.nation,
                None  # No alias for new club
            ))
            conn.commit()
            return {"success": True, "message": f"Created new club '{resolution.new_club_name}'"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {resolution.action}. Must be 'add_alias', 'swap_names', or 'create_new'")
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resolve club miss: {str(e)}")
    finally:
        conn.close()

@router.post("/admin/athletes/{athlete_id}/add-alias")
async def add_athlete_alias(athlete_id: str, alias: str = Query(...)):
    """Add an alias to an athlete's alias field"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Check if athlete exists
        cursor.execute("SELECT id, FULLNAME FROM athletes WHERE id = ?", (athlete_id,))
        athlete = cursor.fetchone()
        if not athlete:
            raise HTTPException(status_code=404, detail=f"Athlete with id {athlete_id} not found")
        
        # Check which alias columns exist
        cursor.execute("PRAGMA table_info(athletes)")
        columns_info = cursor.fetchall()
        columns = {row[1].lower() for row in columns_info}
        has_alias_1 = "athlete_alias_1" in columns
        has_alias_2 = "athlete_alias_2" in columns
        
        if not has_alias_1 and not has_alias_2:
            raise HTTPException(status_code=400, detail="Alias columns not found in athletes table")
        
        # Check current alias values
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
                    if has_alias_2 and len(row) > idx:
                        current_alias_2 = row[idx]
        
        # Normalize alias for comparison
        def normalize_name(name):
            if not name:
                return ""
            return str(name).strip().upper()
        
        # Check if alias already exists
        alias_normalized = normalize_name(alias)
        if (current_alias_1 and normalize_name(current_alias_1) == alias_normalized) or \
           (current_alias_2 and normalize_name(current_alias_2) == alias_normalized):
            return {"success": True, "message": f"Alias '{alias}' already exists for this athlete"}
        
        # Add alias to first available field
        if has_alias_1 and not current_alias_1:
            cursor.execute("UPDATE athletes SET athlete_alias_1 = ? WHERE id = ?", (alias.strip(), athlete_id))
            conn.commit()
            return {"success": True, "message": f"Alias '{alias}' added to athlete_alias_1"}
        elif has_alias_2 and not current_alias_2:
            cursor.execute("UPDATE athletes SET athlete_alias_2 = ? WHERE id = ?", (alias.strip(), athlete_id))
            conn.commit()
            return {"success": True, "message": f"Alias '{alias}' added to athlete_alias_2"}
        else:
            # Both aliases are full - overwrite alias_2
            cursor.execute("UPDATE athletes SET athlete_alias_2 = ? WHERE id = ?", (alias.strip(), athlete_id))
            conn.commit()
            return {"success": True, "message": f"Alias '{alias}' added to athlete_alias_2 (overwrote existing value)"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add alias: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/athletes/{athlete_id}/results")
async def get_athlete_results(athlete_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, best_only: bool = False):
    """Get results for a specific athlete with club and state information"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Build query with date filtering and best times option
        base_query = """
            SELECT 
                r.id,
                r.time_string,
                r.place,
                r.aqua_points,
                r.year_age,
                r.day_age,
                e.distance,
                e.stroke,
                e.gender as event_gender,
                m.id as meet_id,
                m.name as meet_name,
                m.meet_type as meet_code,
                m.meet_date,
                r.team_name as club_name,
                r.team_state_code as state_code,
                a.FULLNAME as athlete_name,
                a.BIRTHDATE as birthdate
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN events e ON r.event_id = e.id
            LEFT JOIN meets m ON r.meet_id = m.id
            WHERE r.athlete_id = ?
        """
        params = [athlete_id]
        
        # Add date filtering
        if start_date:
            base_query += " AND (m.meet_date IS NULL OR m.meet_date >= ?)"
            params.append(start_date)
        
        if end_date:
            base_query += " AND (m.meet_date IS NULL OR m.meet_date <= ?)"
            params.append(end_date)
        
        # For best times, we need to group by event and get the best time
        if best_only:
            base_query += """
                ORDER BY e.distance, e.stroke, e.gender, 
                         COALESCE(r.time_seconds, r.time_seconds_numeric, 999999)
            """
            cursor.execute(base_query, params)
            all_results = cursor.fetchall()
            
            # Group by event and keep only best time
            best_results = {}
            for row in all_results:
                event_key = f"{row[6]}_{row[7]}_{row[8]}"  # distance_stroke_gender
                if event_key not in best_results:
                    best_results[event_key] = row
                else:
                    # Compare times (lower is better)
                    current_time = row[1] or "99:99.99"
                    best_time = best_results[event_key][1] or "99:99.99"
                    # Simple string comparison for times (works for most formats)
                    if current_time < best_time:
                        best_results[event_key] = row
            
            results = list(best_results.values())
        else:
            base_query += " ORDER BY m.meet_date DESC, e.distance, e.stroke"
            cursor.execute(base_query, params)
            results = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in results:
            data.append({
                "result_id": row[0],
                "time": row[1],
                "place": row[2],
                "aqua_points": row[3],
                "year_age": row[4],
                "day_age": row[5],
                "distance": row[6],
                "stroke": row[7],
                "event_gender": row[8],
                "meet_id": row[9],
                "meet_name": row[10],
                "meet_code": row[11],
                "meet_date": row[12],
                "club_name": row[13],
                "state_code": row[14],
                "athlete_name": row[15],
                "birthdate": row[16]
            })
        
        return {"results": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get athlete results: {str(e)}")
    finally:
        conn.close()

@router.get("/admin/clubs/{club_name}/roster")
async def get_club_roster(club_name: str, meet_id: Optional[str] = None):
    """Get athlete roster for a club, optionally filtered by meet"""
    conn = get_database_connection()
    cursor = conn.cursor()
    
    try:
        # Build query to get unique athletes from results for this club
        base_query = """
            SELECT DISTINCT
                a.id as athlete_id,
                a.FULLNAME as fullname,
                a.Gender as gender,
                r.year_age,
                r.day_age,
                m.meet_date,
                a.BIRTHDATE as birthdate
            FROM results r
            LEFT JOIN athletes a ON r.athlete_id = a.id
            LEFT JOIN meets m ON r.meet_id = m.id
            WHERE r.team_name = ?
        """
        params = [club_name]
        
        if meet_id:
            base_query += " AND r.meet_id = ?"
            params.append(meet_id)
        
        base_query += " ORDER BY a.FULLNAME"
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        # Convert to list of dicts and compute age
        roster = []
        for row in results:
            # Compute age at meet date
            age = None
            if row[6] and row[7]:  # meet_date and birthdate
                try:
                    from datetime import datetime
                    meet_date = datetime.strptime(row[6], '%Y-%m-%d') if isinstance(row[6], str) else row[6]
                    birthdate = datetime.strptime(row[7], '%Y.%m.%d') if isinstance(row[7], str) else row[7]
                    age = (meet_date.year - birthdate.year) - ((meet_date.month, meet_date.day) < (birthdate.month, birthdate.day))
                except:
                    age = row[3]  # fallback to year_age
            elif row[3]:  # year_age
                age = row[3]
            
            roster.append({
                "athlete_id": row[0],
                "fullname": row[1] or "Unknown",
                "gender": row[2] or "U",
                "age": age,
                "year_age": row[3],
                "day_age": row[4]
            })
        
        return {"roster": roster, "count": len(roster), "club_name": club_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get club roster: {str(e)}")
    finally:
        conn.close()

@router.post("/admin/analyze-athlete-info")
async def analyze_athlete_info(file: UploadFile = File(...)):
    """Analyze uploaded athlete info workbook structure - returns headers, sample data, and sheet info"""
    
    print(f"[athlete info analysis] Received request for file: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    import pandas as pd
    
    # Basic validation: check if this looks like a meet results file
    # (We'll do a quick check after reading the file)
    
    # Save uploaded file temporarily
    temp_file_path = None
    try:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            print(f"[athlete info analysis] Received file '{file.filename}', saving to '{temp_file_path}'")
            # Stream file in chunks
            chunk_size = 1024 * 1024  # 1MB
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                temp_file.write(chunk)
        
        # Analyze the file
        print(f"[athlete info analysis] Analyzing '{file.filename}'...")
        excel_file = pd.ExcelFile(temp_file_path, engine='xlrd' if suffix == '.xls' else None)
        sheet_names = excel_file.sheet_names
        
        print(f"[athlete info analysis] Found {len(sheet_names)} sheet(s): {', '.join(sheet_names[:5])}")
        
        # Basic validation: check if this looks like a meet results file instead
        meet_indicators = ['50M', '100M', '200M', '400M', '800M', '1500M', 'FR', 'BK', 'BR', 'BU', 'ME', 'IM']
        has_meet_indicators = any(any(ind in str(s).upper() for ind in meet_indicators) for s in sheet_names[:3])
        has_state_codes = any(len(str(s).strip().upper()) >= 2 and len(str(s).strip().upper()) <= 3 for s in sheet_names[:3])
        
        if has_meet_indicators and not has_state_codes:
            raise HTTPException(status_code=400, detail="This appears to be a meet results file (has event sheets like '50m Fr', '100m Fr'). Please upload this to the 'Upload & Convert Meet' tab instead. Athlete Info files should contain athlete personal information.")
        
        sheets_info = []
        for sheet_name in sheet_names:
            try:
                # Read first few rows to get headers and sample data
                df = pd.read_excel(temp_file_path, sheet_name=sheet_name, nrows=5, engine='xlrd' if suffix == '.xls' else None)
                
                # Get headers (first row)
                headers = [str(col).strip() if pd.notna(col) else f'Column_{i}' for i, col in enumerate(df.columns)]
                
                # Get sample rows (first 3 data rows)
                sample_rows = []
                for idx in range(min(3, len(df))):
                    row = df.iloc[idx]
                    sample_rows.append([str(val).strip() if pd.notna(val) else '' for val in row.values])
                
                sheets_info.append({
                    'name': sheet_name,
                    'row_count': len(pd.read_excel(temp_file_path, sheet_name=sheet_name, engine='xlrd' if suffix == '.xls' else None)),
                    'column_count': len(df.columns),
                    'headers': headers,
                    'sample_rows': sample_rows
                })
            except Exception as e:
                print(f"Error analyzing sheet '{sheet_name}': {e}")
                sheets_info.append({
                    'name': sheet_name,
                    'error': str(e)
                })
        
        return {
            'filename': file.filename,
            'sheet_count': len(sheet_names),
            'sheets': sheets_info
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"[athlete info analysis] Error cleaning up temporary file: {e}")


@router.get("/admin/athletes/export-excel")
async def export_athletes_excel():
    """Export all athletes from database as Excel file"""
    from fastapi.responses import FileResponse
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from io import BytesIO
    import sys
    import os

    try:
        print("DEBUG: Starting export", flush=True)
        sys.stdout.flush()

        conn = get_database_connection()
        cursor = conn.cursor()

        # Fetch all athletes with FULLNAME, BIRTHDATE, and id
        cursor.execute("""
            SELECT
                id,
                FULLNAME,
                BIRTHDATE
            FROM athletes
            ORDER BY FULLNAME ASC
        """)

        athletes = cursor.fetchall()
        conn.close()
        print(f"DEBUG: Fetched {len(athletes)} athletes", flush=True)
        sys.stdout.flush()

        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Athletes"

        # Add headers
        headers = ["Athlete ID", "Full Name", "Birthdate"]
        ws.append(headers)

        # Style header row
        header_fill = PatternFill(start_color="CC0000", end_color="CC0000", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font

        # Add data rows
        for athlete in athletes:
            athlete_id, fullname, birthdate = athlete
            ws.append([athlete_id, fullname, birthdate])

        # Adjust column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 15

        # Write to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        print("DEBUG: Workbook created successfully", flush=True)
        sys.stdout.flush()

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"athletes_export_{timestamp}.xlsx"

        # Write to temp file using tempfile module (Windows compatible)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"athletes_export_{timestamp}.xlsx")

        with open(temp_path, 'wb') as f:
            f.write(output.getvalue())
        print(f"DEBUG: Temp file created at {temp_path}", flush=True)
        sys.stdout.flush()

        # Return as FileResponse
        return FileResponse(
            temp_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )

    except Exception as e:
        import traceback
        print(f"DEBUG: Exception occurred: {str(e)}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/admin/manual-results")
async def submit_manual_results(submission: ManualResultsSubmission):
    """
    Submit manual meet results
    - Creates meet if it doesn't exist
    - Validates athletes exist
    - Inserts results into database
    """
    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        # 1. Create or get meet
        cursor.execute(
            "SELECT id FROM meets WHERE name = ?",
            (submission.meet_name,)
        )
        meet_row = cursor.fetchone()

        if not meet_row:
            # Create new meet
            meet_id = f"manual_{datetime.now().timestamp()}"

            # Validate and convert meet_date to ISO 8601 format
            try:
                validated_meet_date = parse_and_validate_date(
                    submission.meet_date.strip(),
                    field_name="meet_date"
                )
            except ValueError as e:
                logger.error(f"Date validation failed for manual entry: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid meet date format: {str(e)}")

            cursor.execute("""
                INSERT INTO meets (id, name, meet_type, meet_date, city, course)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meet_id,
                submission.meet_name.strip(),
                submission.meet_alias.strip() or "Manual Entry",
                validated_meet_date,
                submission.meet_city.strip(),
                submission.meet_course.strip()
            ))
            conn.commit()
        else:
            meet_id = meet_row[0]

        # 2. Validate and insert results
        inserted_count = 0
        errors = []

        for result in submission.results:
            try:
                # Check athlete exists
                cursor.execute(
                    "SELECT id FROM athletes WHERE id = ?",
                    (result.athlete_id,)
                )
                if not cursor.fetchone():
                    errors.append(f"Athlete {result.athlete_id} not found")
                    continue

                # Find or create event
                cursor.execute("""
                    SELECT id FROM events
                    WHERE distance = ? AND stroke = ? AND gender = ?
                """, (result.distance, result.stroke.upper(), result.event_gender.upper()))

                event_row = cursor.fetchone()
                if not event_row:
                    errors.append(f"Event {result.distance}{result.stroke} {result.event_gender} not found")
                    continue

                event_id = event_row[0]

                # Insert result
                cursor.execute("""
                    INSERT INTO results (
                        athlete_id, event_id, meet_id, time_string, place,
                        team_name, team_state_code
                    ) VALUES (?, ?, ?, ?, ?, NULL, NULL)
                """, (
                    result.athlete_id,
                    event_id,
                    meet_id,
                    result.time_string.strip(),
                    result.place
                ))
                inserted_count += 1

            except Exception as e:
                errors.append(f"Error inserting result for athlete {result.athlete_id}: {str(e)}")

        conn.commit()

        response = {
            "success": True,
            "meet_id": meet_id,
            "results_inserted": inserted_count,
            "total_results_submitted": len(submission.results),
            "message": f"Inserted {inserted_count}/{len(submission.results)} results for meet '{submission.meet_name}'"
        }

        if errors:
            response["errors"] = errors

        return response

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit results: {str(e)}")

    finally:
        conn.close()
