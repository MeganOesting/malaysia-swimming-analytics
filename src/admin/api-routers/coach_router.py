"""
Coach Management API endpoints
Compatibility layer - imports from src/web/routers/admin.py
Full extraction and refactoring to follow
"""
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.web.routers.admin import (
    router,
    list_coaches,
    create_coach,
    update_coach,
    delete_coach,
    CoachCreateRequest,
)

__all__ = [
    "router",
    "list_coaches",
    "create_coach",
    "update_coach",
    "delete_coach",
    "CoachCreateRequest",
]
