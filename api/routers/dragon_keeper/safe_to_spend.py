"""Safe-to-Spend API endpoint."""
from fastapi import APIRouter
from api.services.dragon_keeper.projection import project_cash_flow

router = APIRouter()


@router.get("/safe-to-spend")
def get_safe_to_spend():
    return project_cash_flow()
