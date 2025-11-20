"""
Authentication API endpoints for admin panel
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

router = APIRouter()

# Simple password authentication
ADMIN_PASSWORD = "MAS2025"


class AuthRequest(BaseModel):
    password: str


@router.get("/admin/test")
async def test_admin():
    """Test admin endpoint"""
    return {"message": "Admin router is working"}


@router.post("/admin/authenticate")
async def authenticate(request: AuthRequest):
    """Authenticate admin user"""
    if request.password == ADMIN_PASSWORD:
        return {"success": True, "message": "Authentication successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")
