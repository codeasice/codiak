"""Spending trends API endpoint."""
from fastapi import APIRouter
from api.services.dragon_keeper.spending_trends import get_spending_trends

router = APIRouter()


@router.get("/spending-trends")
def spending_trends():
    return get_spending_trends()
