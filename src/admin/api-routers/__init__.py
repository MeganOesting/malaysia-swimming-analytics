"""
API Routers for admin endpoints
Compatibility layer and new features
"""

from . import auth_router
from . import athlete_router
from . import club_router
from . import coach_router
from . import meet_router
from . import upload_router
from . import manual_entry_router

__all__ = [
    "auth_router",
    "athlete_router",
    "club_router",
    "coach_router",
    "meet_router",
    "upload_router",
    "manual_entry_router",
]
