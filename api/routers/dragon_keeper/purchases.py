"""Purchases page API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.dragon_keeper.purchases_service import (
    get_purchases, update_cost, update_purchase_date, move_purchase,
)

router = APIRouter()


class CostUpdate(BaseModel):
    cost: float


class PurchaseDateUpdate(BaseModel):
    date: str | None = None


class MoveRequest(BaseModel):
    direction: str  # "up" or "down"


@router.get("/purchases")
def list_purchases():
    return get_purchases()


@router.patch("/purchases/{filename}/cost")
def patch_cost(filename: str, body: CostUpdate):
    if not update_cost(filename, body.cost):
        raise HTTPException(status_code=404, detail="Purchase not found")
    return {"ok": True}


@router.patch("/purchases/{filename}/purchase-date")
def patch_purchase_date(filename: str, body: PurchaseDateUpdate):
    if not update_purchase_date(filename, body.date):
        raise HTTPException(status_code=404, detail="Purchase not found")
    return {"ok": True}


@router.post("/purchases/{filename}/move")
def move(filename: str, body: MoveRequest):
    if body.direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="direction must be 'up' or 'down'")
    if not move_purchase(filename, body.direction):
        raise HTTPException(status_code=400, detail="Cannot move in that direction")
    return {"ok": True}
