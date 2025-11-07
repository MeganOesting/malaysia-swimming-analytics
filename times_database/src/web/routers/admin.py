"""
Admin API endpoints for Excel file upload and conversion
"""

import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import sqlite3
import re

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import our conversion logic
from scripts.convert_meets_proper import (
    iter_valid_sheets, 
    process_sheet, 
    extract_meet_info,
    convert_time_to_seconds,
    SKIP_SHEET_TOKENS,
    EVENT_OPTIONS,
    STROKE_MAP,
    ALLOWED_DISTANCES
)

router = APIRouter()

# Simple password authentication (in production, use proper auth)
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


def get_database_connection():
    """Get SQLite connection to the canonical database."""
    db_path = CANONICAL_DB_PATH
    return sqlite3.connect(str(db_path))

@router.get("/meets")
async def list_meets() -> Dict[str, List[Dict[str, Any]]]:
    """Return meets with metadata expected by the admin dashboard."""
    conn = get_database_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT m.id,
                       m.name,
                       m.meet_type,
                       m.alias,
                       m.meet_date,
                       m.location,
                       m.city,
                       COUNT(r.id) AS result_count
                FROM meets m
                LEFT JOIN results r ON r.meet_id = m.id
                GROUP BY m.id, m.name, m.meet_type, m.alias, m.meet_date, m.location, m.city, m.created_at
                ORDER BY COALESCE(m.meet_date, m.created_at) DESC
                """
            )
        except sqlite3.OperationalError:
            return {"meets": []}
        meets = []
        for row in cursor.fetchall():
            alias_value = (row["alias"] or "").strip() if row["alias"] else ""
            meet_type_value = (row["meet_type"] or "").strip()
            code_value = alias_value or meet_type_value
            city_value = (row["city"] or "").strip() if row["city"] else ""
            meets.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "alias": alias_value,
                    "code": code_value,
                    "date": row["meet_date"],
                    "city": city_value,
                    "result_count": row["result_count"],
                }
            )
        return {"meets": meets}
    finally:
        conn.close()

@router.delete("/meets/{meet_id}")
async def delete_meet(meet_id: str) -> Dict[str, Any]:
    """Delete a meet and its associated results."""
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results WHERE meet_id = ?", (meet_id,))
        cursor.execute("DELETE FROM meets WHERE id = ?", (meet_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Meet not found")
        conn.commit()
        return {"message": "Meet deleted", "meet_id": meet_id}
    finally:
        conn.close()

@router.get("/meets/{meet_id}/pdf", response_class=HTMLResponse)
async def generate_meet_pdf(meet_id: str) -> HTMLResponse:
    """Return a printable HTML report for the specified meet."""
    conn = get_database_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, meet_type, alias, meet_date, location, city FROM meets WHERE id = ?",
            (meet_id,),
        )
        meet = cursor.fetchone()
        if not meet:
            raise HTTPException(status_code=404, detail="Meet not found")

        cursor.execute(
            """
            SELECT a.name AS athlete_name,
                   a.gender,
                   e.distance,
                   e.stroke,
                   r.time_string,
                   r.place,
                   r.day_age,
                   r.year_age,
                   r.course
            FROM results r
            JOIN athletes a ON r.athlete_id = a.id
            JOIN events e ON r.event_id = e.id
            WHERE r.meet_id = ?
            ORDER BY e.distance, e.stroke, a.gender, r.time_seconds
            """,
            (meet_id,),
        )
        rows = cursor.fetchall()

        events: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            event_key = f"{row['distance']}{row['stroke']}{row['gender']}"
            if event_key not in events:
                events[event_key] = {
                    "distance": row["distance"],
                    "stroke": row["stroke"],
                    "gender": row["gender"],
                    "results": [],
                    "seen": {},
                }

            athlete_name = row["athlete_name"] or ""
            time_string = row["time_string"] or ""
            name_norm = " ".join(str(athlete_name).split()).upper()
            time_norm = str(time_string).strip()
            norm_key = (name_norm, time_norm)
            existing_idx = events[event_key]["seen"].get(norm_key)
            if existing_idx is not None:
                existing = events[event_key]["results"][existing_idx]
                new_place = row["place"]
                old_place = existing.get("place")
                try:
                    if new_place is not None and (old_place is None or int(new_place) < int(old_place)):
                        existing["place"] = new_place
                except Exception:
                    pass
                continue

            events[event_key]["seen"][norm_key] = len(events[event_key]["results"])
            events[event_key]["results"].append(
                {
                    "athlete_name": athlete_name,
                    "time_string": time_string,
                    "place": row["place"],
                    "day_age": row["day_age"],
                    "year_age": row["year_age"],
                    "course": row["course"],
                }
            )

        stroke_map = {
            "FR": "Free",
            "FRE": "Free",
            "FREESTYLE": "Free",
            "BK": "Back",
            "BAC": "Back",
            "BACKSTROKE": "Back",
            "BR": "Breast",
            "BRE": "Breast",
            "BREASTSTROKE": "Breast",
            "BU": "Fly",
            "FLY": "Fly",
            "BUTTERFLY": "Fly",
            "ME": "IM",
            "MED": "IM",
            "IM": "IM",
            "MEDLEY": "IM",
        }

        gender_map = {
            "M": "Men's",
            "F": "Women's",
        }

        def event_sort_key(event_key: str) -> tuple:
            stroke = events[event_key]["stroke"]
            distance = events[event_key]["distance"]
            gender = events[event_key]["gender"]

            stroke_order = {
                "FR": 0,
                "FRE": 0,
                "FREESTYLE": 0,
                "BK": 1,
                "BAC": 1,
                "BACKSTROKE": 1,
                "BR": 2,
                "BRE": 2,
                "BREASTSTROKE": 2,
                "BU": 3,
                "FLY": 3,
                "BUTTERFLY": 3,
                "ME": 4,
                "IM": 4,
                "MED": 4,
                "MEDLEY": 4,
            }

            stroke_priority = stroke_order.get(str(stroke).upper(), 5)
            gender_priority = 0 if str(gender).upper().startswith("M") else 1
            try:
                distance_value = float(distance)
            except (TypeError, ValueError):
                try:
                    distance_value = float(str(distance).strip().rstrip("mM"))
                except Exception:
                    distance_value = 0.0
            return (gender_priority, stroke_priority, distance_value)

        alias_raw = None
        if hasattr(meet, "keys") and "alias" in meet.keys():
            alias_raw = meet["alias"]
        alias_value = (alias_raw if alias_raw else meet["meet_type"] or "").strip()
        title_components: List[str] = []
        base_name = (meet["name"] or "").strip()
        if base_name:
            if alias_value:
                title_components.append(f"{base_name} ({alias_value})")
            else:
                title_components.append(base_name)
        elif alias_value:
            title_components.append(alias_value)
        city_value = (meet["city"] or "").strip() if meet["city"] else ""
        date_value = (meet["meet_date"] or "").strip() if meet["meet_date"] else ""
        if city_value:
            title_components.append(city_value)
        if date_value:
            title_components.append(date_value)
        title_text = " • ".join(title_components) if title_components else (base_name or alias_value or "Meet Results")

        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset=\"UTF-8\">",
            f"    <title>{meet['name']} - Results</title>",
            "    <style>",
            "        body { font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 20px; font-size: 12pt; line-height: 1.4; }",
            "        h1 { color: #2c3e50; margin-bottom: 4px; font-size: 16pt; }",
            "        h2 { color: #4b5563; margin-top: 0; font-weight: normal; font-size: 12pt; }",
            "        .columns { column-count: 2; column-gap: 24px; }",
            "        .event-section { margin-bottom: 16px; break-inside: avoid-column; }",
            "        .event-title { font-size: 14pt; font-weight: bold; margin-bottom: 4px; color: #34495e; }",
            "        .results-text { font-family: 'Courier New', monospace; white-space: pre; font-size: 11pt; line-height: 1.05; margin: 0; }",
            "    </style>",
            "</head>",
            "<body>",
        ]

        html_lines.append(f"    <h1>{title_text}</h1>")
        html_lines.append("    <div class=\"columns\">")

        for key in sorted(events.keys(), key=event_sort_key):
            event = events[key]
            event_stroke = str(event["stroke"]).upper() if event["stroke"] else ""
            event_gender = str(event["gender"]).upper() if event["gender"] else ""
            event_title = f"{gender_map.get(event_gender, event_gender)} {event['distance']}m {stroke_map.get(event_stroke, event['stroke'])}"
            course = event["results"][0].get("course") if event["results"] else ""
            if course:
                event_title = f"{event_title} {course}"

            html_lines.append("        <div class=\"event-section\">")
            html_lines.append(f"            <div class=\"event-title\">{event_title}</div>")
            html_lines.append("            <pre class=\"results-text\">")

            for idx, result in enumerate(event["results"], start=1):
                place_str = str(idx).rjust(4)
                name_str = (result.get("athlete_name") or "").ljust(40)[:40]
                time_str = (result.get("time_string") or "").rjust(8)[:8]
                age_val = result.get("year_age")
                if age_val is None or age_val == "":
                    age_val = result.get("day_age")
                age_str = str(age_val).rjust(3)[:3] if age_val not in (None, "") else "   "
                course_str = (result.get("course") or "").rjust(4)[:4]
                html_lines.append(f"{place_str} {name_str} {age_str}  {time_str} {course_str}")

            html_lines.append("            </pre>")
            html_lines.append("        </div>")

        html_lines.extend([
            "    </div>",
            "</body>",
            "</html>",
        ])

        return HTMLResponse("\n".join(html_lines))
    finally:
        conn.close()

@router.get("/test")
async def test_admin():
    """Test admin endpoint"""
    return {"message": "Admin router is working"}

@router.post("/authenticate")
async def authenticate(request: AuthRequest):
    """Authenticate admin user"""
    print(f"Received password: '{request.password}'")
    print(f"Expected password: '{ADMIN_PASSWORD}'")
    print(f"Passwords match: {request.password == ADMIN_PASSWORD}")
    
    if request.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Authentication successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

@router.post("/convert-excel", response_model=ConversionResult)
async def convert_excel(
    file: UploadFile = File(...),
    meet_name: str = Form(None),
    meet_code: str = Form(None),
    existing_meet_id: str = Form(None)
):
    """Convert uploaded Excel file to database entries"""
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Process the file
        result = await process_uploaded_file(temp_file_path, file.filename, meet_name, meet_code, existing_meet_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

async def process_uploaded_file(file_path: str, filename: str, meet_name: str, meet_code: str, existing_meet_id: str = None) -> ConversionResult:
    """Process uploaded Excel file and add to database"""
    
    print(f"Processing uploaded file: {filename}")
    print(f"Meet Name: {meet_name}")
    print(f"Meet Code: {meet_code}")
    print(f"Existing Meet ID: {existing_meet_id}")
    
    # Determine if we're creating a new meet or adding to existing
    if existing_meet_id:
        # Add to existing meet
        conn = get_database_connection()
        try:
            cursor = conn.cursor()
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
                'created_at': existing_meet[5]  # created_at
            }
        finally:
            conn.close()
    else:
        # Create new meet
        meet_info = {
            'id': str(uuid.uuid4()),
            'name': meet_name,
            'meet_type': meet_code,
            'meet_date': datetime.now().strftime('%Y-%m-%d'),
            'location': 'Uploaded Meet',
            'created_at': datetime.now().isoformat()
        }
    
    # Get valid sheets using old build logic
    valid_sheets = iter_valid_sheets(Path(file_path))
    print(f"Valid sheets found: {valid_sheets}")
    
    if not valid_sheets:
        return ConversionResult(
            success=False,
            message="No valid sheets found in the Excel file. Make sure the file contains swimming event data."
        )
    
    # Process each sheet
    all_athletes = []
    all_results = []
    all_events = []
    
    for sheet_name in valid_sheets:
        print(f"Processing sheet: {sheet_name}")
        
        try:
            # Read sheet
            engine = "xlrd" if str(file_path).lower().endswith(".xls") else None
            if engine:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, engine=engine)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            print(f"  Sheet shape: {df.shape}")
            
            # Process for both genders
            for gender in ['M', 'F']:
                athletes, results, events = process_sheet_data(
                    df, meet_info['id'], gender
                )
                all_athletes.extend(athletes)
                all_results.extend(results)
                all_events.extend(events)
                
                print(f"  {gender}: {len(athletes)} athletes, {len(results)} results, {len(events)} events")
        
        except Exception as e:
            print(f"  Error processing sheet {sheet_name}: {e}")
            continue
    
    if not all_results:
        return ConversionResult(
            success=False,
            message="No valid swimming results found in the Excel file. Please check the file format."
        )
    
    # Remove duplicates
    unique_athletes = remove_duplicate_athletes(all_athletes)
    unique_events = remove_duplicate_events(all_events)
    
    print(f"Total unique athletes: {len(unique_athletes)}")
    print(f"Total unique events: {len(unique_events)}")
    print(f"Total results: {len(all_results)}")
    
    # Insert into database
    conn = get_database_connection()
    try:
        if existing_meet_id:
            # Add to existing meet - don't insert meet again
            insert_new_data(conn, unique_athletes, all_results, unique_events, [])
            message = f"Successfully added data from {filename} to existing meet. Data is now available in the main application."
        else:
            # Create new meet
            insert_new_data(conn, unique_athletes, all_results, unique_events, [meet_info])
            message = f"Successfully converted {filename}. Data is now available in the main application."
        
        return ConversionResult(
            success=True,
            message=message,
            athletes=len(unique_athletes),
            results=len(all_results),
            events=len(unique_events),
            meets=0 if existing_meet_id else 1
        )
    
    except Exception as e:
        print(f"Database error: {e}")
        return ConversionResult(
            success=False,
            message=f"Database error: {str(e)}"
        )
    
    finally:
        conn.close()

def process_sheet_data(df, meet_id, gender):
    """Process a single sheet following the corrected column mapping"""
    athletes = []
    results = []
    events = []
    
    # Skip header rows (row 1: meet info, row 2: headers, row 3+: data)
    df_data = df.iloc[2:].copy() if len(df) > 2 else df

    if len(df_data) == 0:
        return athletes, results, events

    # Re-map columns for data section (corrected mapping)
    colB_data = df_data.get(1)   # Gender
    colC_data = df_data.get(2)    # Distance
    colD_data = df_data.get(3)    # Stroke
    colE_data = df_data.get(4)    # Name
    colF_data = df_data.get(5)    # Birthdate
    colG_data = df_data.get(6)    # Nation
    colH_data = df_data.get(7)    # Club Code
    colI_data = df_data.get(8)    # SWIMTIME (display time)
    colJ_data = df_data.get(9)   # SWIMTIME_N (time in seconds)
    colK_data = df_data.get(10)   # PTS_FINA (AQUA points)
    colL_data = df_data.get(11)   # Place
    colM_data = df_data.get(12)   # Place (alternative)
    colN_data = df_data.get(13)   # Meet date
    colO_data = df_data.get(14)   # Club name
    colP_data = df_data.get(15)   # Club name (alternative)
    colQ_data = df_data.get(16)   # CLUBNAME
    
    if colB_data is None or colC_data is None or colD_data is None or colE_data is None:
        return athletes, results, events

    # Process data with corrected column mapping
    gender_col = colB_data.astype(str).str.strip().str.upper()
    distance_col = pd.to_numeric(colC_data, errors='coerce')
    stroke_col = colD_data.astype(str).str.strip().str.upper()
    name_col = colE_data.astype(str).str.strip()
    
    # Candidate mask: gender + has name + distance in allowed set
    mask = (
        (gender_col == gender) &
        (name_col != "") &
        (distance_col.isin(ALLOWED_DISTANCES))
    )
    
    # Get the actual data rows that match our criteria
    data_rows = df_data[mask]
    
    for idx, row in data_rows.iterrows():
        try:
            # Extract data using the row data directly
            swimmer_name = str(row.iloc[4]).strip()  # Column 4: FULLNAME
            if not swimmer_name or swimmer_name == 'nan':
                continue

            distance = int(row.iloc[2])  # Column 2: DISTANCE
            stroke = str(row.iloc[3]).strip().upper()  # Column 3: STROKE

            # Keep stroke as abbreviation for backend storage
            event_name = f"{distance}m {stroke}"

            # Check if event is in our allowed list (using abbreviations)
            if event_name not in EVENT_OPTIONS:
                continue

            # Get other data - corrected column mapping based on actual headers
            time_str = str(row.iloc[8]) if not pd.isna(row.iloc[8]) else ""  # Column 8: SWIMTIME (display time)
            time_seconds = 0
            try:
                if not pd.isna(row.iloc[9]):  # Column 9: SWIMTIME_N (time in seconds for calculations)
                    time_seconds = float(row.iloc[9])
            except:
                pass

            aqua_points = 0
            try:
                if not pd.isna(row.iloc[10]) and str(row.iloc[10]).replace('.', '').isdigit():  # Column 10: PTS_FINA
                    aqua_points = int(float(row.iloc[10]))
            except:
                pass

            place = 0
            try:
                if not pd.isna(row.iloc[12]) and str(row.iloc[12]).replace('.', '').isdigit():  # Column 12: PLACE
                    place = int(float(row.iloc[12]))
            except:
                pass

            team = str(row.iloc[16]) if not pd.isna(row.iloc[16]) else ""  # Column 16: CLUBNAME

            # Calculate age from birthdate (Column 5: BIRTHDATE)
            age = None
            try:
                if not pd.isna(row.iloc[5]):  # Column 5: BIRTHDATE
                    birthdate = row.iloc[5]
                    if hasattr(birthdate, 'year'):  # It's a datetime object
                        current_year = datetime.now().year
                        age = current_year - birthdate.year
                    else:
                        # Try to parse as string
                        birthdate_str = str(birthdate)
                        if '.' in birthdate_str:
                            day, month, year = birthdate_str.split('.')
                            birth_year = int(year)
                            current_year = datetime.now().year
                            age = current_year - birth_year
            except:
                pass

            if age is None:
                age = 18  # Default age

            # Use time_seconds from column 9 (already in seconds)
            if time_seconds == 0:
                continue
            
            # Create athlete
            athlete_id = str(uuid.uuid4())
            athlete = {
                'id': athlete_id,
                'name': swimmer_name,
                'gender': gender,
                'birthdate': str(row.iloc[5]) if not pd.isna(row.iloc[5]) else None, # Store original birthdate
                'nation': str(row.iloc[6]) if not pd.isna(row.iloc[6]) else None, # Column 6: NATION
                'club_code': str(row.iloc[7]) if not pd.isna(row.iloc[7]) else None, # Column 7: CLUBCODE
                'club_name': team, # Using CLUBNAME from column 16
                'age': age,
                'created_at': datetime.now().isoformat()
            }
            athletes.append(athlete)

            # Create event
            event_id = str(uuid.uuid4())
            event = {
                'id': event_id,
                'distance': distance,
                'stroke': stroke,  # Store abbreviation as-is
                'gender': gender,
                'created_at': datetime.now().isoformat()
            }
            events.append(event)

            # Create result
            result = {
                'id': str(uuid.uuid4()),
                'meet_id': meet_id,
                'athlete_id': athlete_id,
                'event_id': event_id,
                'swim_time': time_str, # Store display time
                'swim_time_seconds': time_seconds, # Store time in seconds
                'fina_points': aqua_points,
                'place': place,
                'created_at': datetime.now().isoformat()
            }
            results.append(result)
            
        except Exception as e:
            print(f"    Error processing row {idx}: {e}")
            continue
    
    return athletes, results, events

def remove_duplicate_athletes(athletes):
    """Remove duplicate athletes by name"""
    unique_athletes = []
    seen_names = set()
    for athlete in athletes:
        if athlete['name'] not in seen_names:
            unique_athletes.append(athlete)
            seen_names.add(athlete['name'])
    return unique_athletes

def remove_duplicate_events(events):
    """Remove duplicate events by distance, stroke, and gender"""
    unique_events = []
    seen_events = set()
    for event in events:
        event_key = f"{event['distance']}_{event['stroke']}_{event['gender']}"
        if event_key not in seen_events:
            unique_events.append(event)
            seen_events.add(event_key)
    return unique_events

def insert_new_data(conn, athletes, results, events, meets):
    """Insert new data into database"""
    cursor = conn.cursor()
    
    # Insert meets
    for meet in meets:
        cursor.execute("""
            INSERT OR REPLACE INTO meets (id, name, meet_type, meet_date, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (meet['id'], meet['name'], meet['meet_type'], meet['meet_date'], meet['location'], meet['created_at']))
    
    # Insert athletes
    for athlete in athletes:
        cursor.execute("""
            INSERT OR REPLACE INTO athletes (id, name, gender, birthdate, nation, club_code, club_name, age, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (athlete['id'], athlete['name'], athlete['gender'], athlete['birthdate'], 
              athlete['nation'], athlete['club_code'], athlete['club_name'], athlete['age'], athlete['created_at']))
    
    # Insert events
    for event in events:
        cursor.execute("""
            INSERT OR REPLACE INTO events (id, distance, stroke, gender, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (event['id'], event['distance'], event['stroke'], event['gender'], event['created_at']))
    
    # Insert results
    for result in results:
        cursor.execute("""
            INSERT INTO results (id, meet_id, athlete_id, event_id, swim_time, swim_time_seconds, fina_points, place, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result['id'], result['meet_id'], result['athlete_id'], result['event_id'], 
              result['swim_time'], result['swim_time_seconds'], result['fina_points'], result['place'], result['created_at']))
    
    conn.commit()
