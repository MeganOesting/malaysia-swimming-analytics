"""
File Upload & Conversion API endpoints
Compatibility layer - imports from src/web/routers/admin.py
Full extraction and refactoring to follow
"""
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.web.routers.admin import (
    router,
    convert_excel,
    convert_clubs,
    analyze_athlete_info,
    ConversionResult,
    ClubConversionResult,
)

__all__ = [
    "router",
    "convert_excel",
    "convert_clubs",
    "analyze_athlete_info",
    "ConversionResult",
    "ClubConversionResult",
]
