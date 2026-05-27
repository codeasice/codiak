"""Paycheck Tracer API endpoints."""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from api.services.dragon_keeper.paycheck_tracer import get_income_sources, trace_paycheck
from api.services.dragon_keeper.paycheck_config import get_paycheck_config, upsert_paycheck_config

router = APIRouter()


@router.get("/paycheck-tracer/sources")
def list_income_sources():
    return {"sources": get_income_sources()}


@router.get("/paycheck-tracer/config")
def get_config():
    return get_paycheck_config()


class DeductionItemIn(BaseModel):
    category: str
    name: str
    amount: float
    sort_order: int = 0


class PaycheckConfigIn(BaseModel):
    gross_amount: float
    take_home_amount: float
    effective_date: str
    notes: str | None = None
    deduction_items: list[DeductionItemIn] = []


@router.put("/paycheck-tracer/config")
def update_config(body: PaycheckConfigIn):
    return upsert_paycheck_config(
        gross_amount=body.gross_amount,
        take_home_amount=body.take_home_amount,
        effective_date=body.effective_date,
        notes=body.notes,
        deduction_items=[i.model_dump() for i in body.deduction_items],
    )


@router.get("/paycheck-tracer")
def get_paycheck_trace(
    income_item_id: int | None = Query(None),
    periods: int = Query(6, ge=2, le=26),
    account_id: str | None = Query(None),
):
    return trace_paycheck(income_item_id, periods, account_id)
