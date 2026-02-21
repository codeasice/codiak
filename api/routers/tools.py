"""
Router: GET /api/tools
Returns the full tool metadata list for the React sidebar.
"""
from fastapi import APIRouter
from typing import List, Dict, Any

from tools.ui_tools_metadata import get_tools_metadata_fast

router = APIRouter()


@router.get("/tools", response_model=List[Dict[str, Any]])
def get_tools():
    """Return all tool metadata for sidebar navigation."""
    return get_tools_metadata_fast()
