"""Planning page API — aggregated purchases, savings, and selling."""
from fastapi import APIRouter
from api.services.dragon_keeper.planning_service import get_planning

router = APIRouter()


@router.get("/planning")
def list_planning():
    return get_planning()
