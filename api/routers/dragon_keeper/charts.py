"""Chart data API endpoints — balance trends, category timelines, spending flows."""
from fastapi import APIRouter, Query
from api.services.dragon_keeper.charts import (
    get_balance_history,
    get_category_timeline,
    get_spending_flow,
)

router = APIRouter()


@router.get("/charts/balance-history")
def balance_history(days: int = Query(90, ge=7, le=365)):
    return get_balance_history(days)


@router.get("/charts/category-timeline/{category_id}")
def category_timeline(category_id: str, periods: int = Query(12, ge=3, le=24)):
    return get_category_timeline(category_id, periods)


@router.get("/charts/spending-flow")
def spending_flow(
    month: str | None = Query(None, description="YYYY-MM format"),
    min_amount: float = Query(10.0, ge=0),
    max_payees: int = Query(30, ge=5, le=50),
):
    return get_spending_flow(month=month, min_amount=min_amount, max_payees=max_payees)
