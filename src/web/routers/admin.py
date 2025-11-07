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
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import sqlite3
import sys

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

class ClubConversionResult(BaseModel):
    success: bool
    message: str
    states: int = 0
    clubs: int = 0
    inserted_states: int = 0
    skipped_states: int = 0
    inserted_clubs: int = 0
    skipped_clubs: int = 0

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

@router.get("/admin/test")
async def test_admin():
    """Test admin endpoint"""
    return {"message": "Admin router is working"}

@router.post("/admin/authenticate")
async def authenticate(request: AuthRequest):
    """Authenticate admin user"""
    print(f"Received password: '{request.password}'")
    print(f"Expected password: '{ADMIN_PASSWORD}'")
    print(f"Passwords match: {request.password == ADMIN_PASSWORD}")
    
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
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Save uploaded file temporarily (stream in chunks to reduce startup delay and memory)
    print(f"[upload] Received file: {file.filename} - starting save to temp file...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        temp_file_path = temp_file.name
        # Stream read in 1MB chunks
        total_bytes = 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            temp_file.write(chunk)
            total_bytes += len(chunk)
        print(f"[upload] Saved to {temp_file_path} ({total_bytes} bytes)")
    
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
        print(f"[upload] Returning JSON response (bytes ~{len(str(body))})")
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

@router.get("/admin/meets")
async def get_meets():
    """Get list of all meets"""
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, meet_type as alias, meet_date as date, city
            FROM meets
            ORDER BY meet_date DESC
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
                "result_count": 0  # Could be added later
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
        cursor.execute("""
            SELECT 
                a.name as athlete_name,
                a.gender,
                e.distance,
                e.stroke,
                r.time_string,
                r.place,
                r.day_age,
                CASE 
                    WHEN r.year_age IS NOT NULL THEN r.year_age
                    WHEN a.age IS NOT NULL THEN a.age
                    WHEN a.birth_date IS NOT NULL AND r.result_meet_date IS NOT NULL THEN 
                        CAST(substr(r.result_meet_date,1,4) AS INTEGER) - CAST(substr(a.birth_date,1,4) AS INTEGER)
                    ELSE NULL
                END as year_age,
                r.course
            FROM results r
            JOIN athletes a ON r.athlete_id = a.id
            JOIN events e ON r.event_id = e.id
            WHERE r.meet_id = ?
            ORDER BY e.distance, e.stroke, e.gender, r.time_seconds ASC
        """, (meet_id,))
        results = cursor.fetchall()
        
        # Group results by event
        events_dict = {}
        for row in results:
            event_key = f"{row[2]}{row[3]}{row[1]}"  # distance + stroke + gender
            if event_key not in events_dict:
                events_dict[event_key] = {
                    'distance': row[2],
                    'stroke': row[3],
                    'gender': row[1],
                    'results': [],
                    'seen': {}  # normalized_key -> index in results
                }
            athlete_name = row[0] or ''
            time_string = row[4] or ''
            # Normalize: collapse spaces, uppercase name; strip time
            name_norm = ' '.join(str(athlete_name).split()).upper()
            time_norm = str(time_string).strip()
            norm_key = (name_norm, time_norm)
            existing_idx = events_dict[event_key]['seen'].get(norm_key)
            if existing_idx is not None:
                # Duplicate name+time within event; keep the better (smaller) place if available
                existing = events_dict[event_key]['results'][existing_idx]
                new_place = row[5]
                old_place = existing.get('place')
                try:
                    if new_place is not None and (old_place is None or int(new_place) < int(old_place)):
                        existing['place'] = new_place
                except Exception:
                    pass
                continue
            # First time seeing this name+time
            events_dict[event_key]['seen'][norm_key] = len(events_dict[event_key]['results'])
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
        
        # Gender mapping
        gender_map = {
            'M': "Men's",
            'F': "Women's"
        }
        
        # Custom sorting function for events
        def event_sort_key(event_key):
            """Sort by: 1) Gender (M before F), 2) Stroke (Fr, Bk, Br, Bu, Me), 3) Distance"""
            stroke = events_dict[event_key]['stroke']
            distance = events_dict[event_key]['distance']
            gender = events_dict[event_key]['gender']
            
            # Stroke order: Freestyle, Backstroke, Breaststroke, Butterfly, Medley
            stroke_order = {'FR': 0, 'FRE': 0, 'Fr': 0, 'Fre': 0, 'Freestyle': 0,
                           'BK': 1, 'BAC': 1, 'Bk': 1, 'Bac': 1, 'Backstroke': 1,
                           'BR': 2, 'BRE': 2, 'Br': 2, 'Bre': 2, 'Breaststroke': 2,
                           'BU': 3, 'FLY': 3, 'Bu': 3, 'Fly': 3, 'Butterfly': 3, 'Butter': 3,
                           'ME': 4, 'IM': 4, 'Me': 4, 'Med': 4, 'Medley': 4}
            
            stroke_priority = stroke_order.get(stroke.upper(), 5)  # Unknown strokes go last
            
            # Gender priority: M=0, F=1
            gender_priority = 0 if gender.upper() == 'M' else 1
            
            return (gender_priority, stroke_priority, distance)
        
        # Sort only the keys using the key function
        sorted_event_keys = sorted(events_dict.keys(), key=event_sort_key)
        for event_key in sorted_event_keys:
            event_data = events_dict[event_key]
            # Get course from first result (all results in same event have same course)
            course = event_data['results'][0]['course'] if event_data['results'] else 'LCM'
            course_str = course if course else 'LCM'
            
            # Format: "Men's 50m Freestyle LCM"
            stroke_full = stroke_map.get(event_data['stroke'], event_data['stroke'])
            gender_full = gender_map.get(event_data['gender'], event_data['gender'])
            
            event_title = f"{gender_full} {event_data['distance']}m {stroke_full} {course_str}"
            
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
    
    print(f"Processing uploaded file: {filename}")
    print(f"Meet Name: {meet_name}")
    print(f"Meet Code: {meet_code}")
    print(f"Existing Meet ID: {existing_meet_id}")
    
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
            meet_info = {
                'id': str(uuid.uuid4()),
                'name': meet_name or 'Uploaded Meet',
                'meet_type': meet_code,
                'meet_date': datetime.now().strftime('%Y-%m-%d'),
                'location': 'Uploaded Meet',
            }
    finally:
        conn.close()
    
    # Process the file using the conversion script with full validation
    file_path_obj = Path(file_path)
    try:
        athletes, results, events = process_meet_file_simple(file_path_obj, meet_info)
    except ConversionValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": str(exc),
                "issues": exc.details,
            },
        )
    
    # After processing, check if meet with extracted name already exists (deduplication)
    if not existing_meet_id and meet_info.get('name'):
        conn = get_database_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, meet_date, city, meet_type FROM meets WHERE name = ?", (meet_info['name'],))
            existing_meet = cursor.fetchone()
            
            if existing_meet:
                # Use existing meet ID instead of creating duplicate
                print(f"Found existing meet with same name: {meet_info['name']}, using existing ID: {existing_meet[0]}")
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
    
    print(f"Processed: {len(athletes)} athletes, {len(results)} results, {len(events)} events")
    
    if not results:
        return ConversionResult(
            success=False,
            message="No valid swimming results found in the Excel file. Please check the file format."
        )
    
    # Insert into database: split results by meet_name to create separate meets
    conn = get_database_connection()
    try:
        def norm_text(s: str) -> str:
            if s is None:
                return ''
            s = str(s).strip()
            return ' '.join(s.split())
        results_by_meet = {}
        for r in results:
            raw_name = r.get('meet_name') or meet_info.get('name') or 'Uploaded Meet'
            name_key = norm_text(raw_name)
            results_by_meet.setdefault(name_key, []).append(r)

        total_meets_created = 0
        per_meet_summaries = []
        for name, group in results_by_meet.items():
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

            # Reuse existing meet if same name exists
            cursor = conn.cursor()
            cursor.execute("SELECT id, meet_date, city, meet_type FROM meets WHERE name = ?", (name,))
            existing = cursor.fetchone()
            child_meet_info = {
                'id': existing[0] if existing else str(uuid.uuid4()),
                'name': name,
                'meet_type': meet_info.get('meet_type'),
                'meet_date': earliest_date,
                'location': meet_info.get('location'),
                'city': city,
            }

            # Update meet_id on group results to the child meet id
            for r in group:
                r['meet_id'] = child_meet_info['id']

            # Insert and collect summary
            summary = insert_data_simple(conn, athletes, group, events, child_meet_info)
            per_meet_summaries.append((name, child_meet_info['meet_date'], child_meet_info.get('city'), summary))
            total_meets_created += 0 if existing else 1

        # Build summary message
        lines = [f"Successfully converted {filename}."]
        for name, d, city, s in per_meet_summaries:
            ins = s.get('inserted_results', 0); sk = s.get('skipped_results', 0)
            city_str = f", {city}" if city else ""
            lines.append(f"- {name} ({d}{city_str}): {ins} added, {sk} skipped")
        message = "\n".join(lines)
        return ConversionResult(
            success=True,
            message=message,
            athletes=len(athletes),
            results=len(results),
            events=len(events),
            meets=max(1, len(results_by_meet))
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
            SELECT id, name, gender, birth_date, club_name, state_code, nation
            FROM athletes
            WHERE UPPER(name) LIKE ?
            ORDER BY name
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
