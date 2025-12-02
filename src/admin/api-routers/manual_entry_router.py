"""
Manual Entry API endpoints
NEW FEATURE - Creates the missing /admin/manual-results endpoint
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
from datetime import datetime

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from scripts.convert_meets_to_sqlite_simple import get_database_connection

router = APIRouter()


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
            "SELECT id FROM meets WHERE meet_name = ?",
            (submission.meet_name,)
        )
        meet_row = cursor.fetchone()

        if not meet_row:
            # Create new meet
            meet_id = f"manual_{datetime.now().timestamp()}"
            cursor.execute("""
                INSERT INTO meets (id, meet_name, meet_type, meet_date, meet_city, meet_course)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                meet_id,
                submission.meet_name.strip(),
                submission.meet_alias.strip() or "Manual Entry",
                submission.meet_date.strip(),
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
                    WHERE event_distance = ? AND event_stroke = ? AND gender = ?
                """, (result.distance, result.stroke.upper(), result.event_gender.upper()))

                event_row = cursor.fetchone()
                if not event_row:
                    errors.append(f"Event {result.distance}{result.stroke} {result.event_gender} not found")
                    continue

                event_id = event_row[0]

                # Insert result
                cursor.execute("""
                    INSERT INTO results (
                        athlete_id, event_id, meet_id, time_string, comp_place,
                        club_name, state_code
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
