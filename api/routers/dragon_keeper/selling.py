"""Selling items API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.dragon_keeper.selling_service import (
    get_selling_items,
    update_current_value,
    update_sold_date,
    move_selling_item,
)

router = APIRouter()


class ValueUpdate(BaseModel):
    current_value: float


class SoldDateUpdate(BaseModel):
    date: str | None = None


class MoveRequest(BaseModel):
    direction: str


@router.get("/selling")
def list_selling_items():
    return get_selling_items()


@router.patch("/selling/{filename}/current-value")
def patch_current_value(filename: str, body: ValueUpdate):
    if not update_current_value(filename, body.current_value):
        raise HTTPException(status_code=404, detail="Selling item not found")
    return {"ok": True}


@router.patch("/selling/{filename}/sold-date")
def patch_sold_date(filename: str, body: SoldDateUpdate):
    if not update_sold_date(filename, body.date):
        raise HTTPException(status_code=404, detail="Selling item not found")
    return {"ok": True}


@router.post("/selling/{filename}/move")
def move(filename: str, body: MoveRequest):
    if body.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="direction must be 'up' or 'down'")
    if not move_selling_item(filename, body.direction):
        raise HTTPException(status_code=400, detail="Cannot move in that direction")
    return {"ok": True}
