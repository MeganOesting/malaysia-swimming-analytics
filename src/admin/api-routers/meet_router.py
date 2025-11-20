"""
Meet Management API endpoints
Compatibility layer - imports from src/web/routers/admin.py
Full extraction and refactoring to follow
"""
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.web.routers.admin import (
    router,
    get_meets,
    update_meet_alias,
    delete_meet,
    get_meet_pdf,
    AliasUpdate,
)

__all__ = [
    "router",
    "get_meets",
    "update_meet_alias",
    "delete_meet",
    "get_meet_pdf",
    "AliasUpdate",
]
