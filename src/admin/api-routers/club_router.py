"""
Club Management API endpoints
Compatibility layer - imports from src/web/routers/admin.py
Full extraction and refactoring to follow
"""
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.web.routers.admin import (
    router,
    get_unmatched_clubs,
    create_club,
    list_clubs,
    list_states,
    update_club,
    search_clubs,
    resolve_club_miss,
    get_club_roster,
    ClubCreateRequest,
    ClubResolutionRequest,
)

__all__ = [
    "router",
    "get_unmatched_clubs",
    "create_club",
    "list_clubs",
    "list_states",
    "update_club",
    "search_clubs",
    "resolve_club_miss",
    "get_club_roster",
    "ClubCreateRequest",
    "ClubResolutionRequest",
]
