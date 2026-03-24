"""Paycheck Tracer API endpoints."""
from fastapi import APIRouter, Query
from api.services.dragon_keeper.paycheck_tracer import get_income_sources, trace_paycheck

router = APIRouter()


@router.get("/paycheck-tracer/sources")
def list_income_sources():
    """Get all detected recurring income items for source selection."""
    return {"sources": get_income_sources()}


@router.get("/paycheck-tracer")
def get_paycheck_trace(
    income_item_id: int | None = Query(None, description="Recurring item ID for the paycheck. Auto-selects primary if omitted."),
    periods: int = Query(6, ge=2, le=26, description="Number of pay periods to trace"),
):
    return trace_paycheck(income_item_id, periods)
