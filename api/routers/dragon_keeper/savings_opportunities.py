"""Savings opportunities page API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.dragon_keeper.savings_opportunities_service import (
    get_savings_opportunities,
    update_savings,
    update_period,
    update_completed_date,
    update_status,
    update_actual_savings,
    mark_as_done,
    move_savings_opportunity,
    VALID_PERIODS,
    VALID_STATUSES,
)

router = APIRouter()


class SavingsUpdate(BaseModel):
    savings: float


class PeriodUpdate(BaseModel):
    period: str


class CompletedDateUpdate(BaseModel):
    date: str | None = None


class StatusUpdate(BaseModel):
    status: str


class ActualSavingsUpdate(BaseModel):
    actual_savings: float


class MoveRequest(BaseModel):
    direction: str  # "up" or "down"


@router.get("/savings-opportunities")
def list_savings_opportunities():
    return get_savings_opportunities()


@router.patch("/savings-opportunities/{filename}/savings")
def patch_savings(filename: str, body: SavingsUpdate):
    if not update_savings(filename, body.savings):
        raise HTTPException(status_code=404, detail="Savings opportunity not found")
    return {"ok": True}


@router.patch("/savings-opportunities/{filename}/period")
def patch_period(filename: str, body: PeriodUpdate):
    if body.period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period must be one of: {', '.join(sorted(VALID_PERIODS))}")
    if not update_period(filename, body.period):
        raise HTTPException(status_code=404, detail="Savings opportunity not found")
    return {"ok": True}


@router.patch("/savings-opportunities/{filename}/completed-date")
def patch_completed_date(filename: str, body: CompletedDateUpdate):
    if not update_completed_date(filename, body.date):
        raise HTTPException(status_code=404, detail="Savings opportunity not found")
    return {"ok": True}


@router.patch("/savings-opportunities/{filename}/status")
def patch_status(filename: str, body: StatusUpdate):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    if not update_status(filename, body.status):
        raise HTTPException(status_code=404, detail="Savings opportunity not found")
    return {"ok": True}


@router.patch("/savings-opportunities/{filename}/actual-savings")
def patch_actual_savings(filename: str, body: ActualSavingsUpdate):
    if not update_actual_savings(filename, body.actual_savings):
        raise HTTPException(status_code=404, detail="Savings opportunity not found")
    return {"ok": True}


@router.post("/savings-opportunities/{filename}/mark-done")
def post_mark_done(filename: str):
    if not mark_as_done(filename):
        raise HTTPException(
            status_code=400,
            detail="Cannot mark done — opportunity not found or has no savings amount",
        )
    return {"ok": True}


@router.post("/savings-opportunities/{filename}/move")
def move(filename: str, body: MoveRequest):
    if body.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="direction must be 'up' or 'down'")
    if not move_savings_opportunity(filename, body.direction):
        raise HTTPException(status_code=400, detail="Cannot move in that direction")
    return {"ok": True}
