"""
Athlete Management API endpoints
Compatibility layer - imports from src/web/routers/admin.py
Full extraction and refactoring to follow
"""
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.web.routers.admin import (
    router,
    search_athletes,
    get_athlete_detail,
    update_athlete,
    add_athlete_alias,
    get_athlete_results,
    export_athletes_excel,
    AthleteUpdateRequest,
    AthleteSearchResponse,
)

# Re-export all athlete endpoints under this router
__all__ = [
    "router",
    "search_athletes",
    "get_athlete_detail", 
    "update_athlete",
    "add_athlete_alias",
    "get_athlete_results",
    "export_athletes_excel",
    "AthleteUpdateRequest",
    "AthleteSearchResponse",
]
