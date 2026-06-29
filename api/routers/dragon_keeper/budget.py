"""Budget API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.dragon_keeper.budget_service import get_budget, upsert_budget_target, set_per_period_income

router = APIRouter()


@router.get("/budget")
def budget():
    return get_budget()


class TargetRequest(BaseModel):
    category_id: str
    amount: float | None = None


@router.patch("/budget/target")
def update_target(req: TargetRequest):
    upsert_budget_target(req.category_id, req.amount)
    return {"status": "ok"}


class IncomeRequest(BaseModel):
    amount: float


@router.patch("/budget/income")
def update_income(req: IncomeRequest):
    set_per_period_income(req.amount)
    return {"status": "ok"}
