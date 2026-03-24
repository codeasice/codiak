"""Dragon Keeper sync API endpoints."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.services.dragon_keeper.sync_engine import run_sync, discover_budgets, SyncError

router = APIRouter()


class SyncRequest(BaseModel):
    budget_id: str | None = None


class SyncResponse(BaseModel):
    status: str
    sync_type: str
    budget_id: str
    accounts_synced: int
    categories_synced: int
    category_groups_synced: int
    payees_synced: int
    transactions_synced: int
    server_knowledge: int
    synced_at: str


class ErrorResponse(BaseModel):
    error: str
    code: str
    detail: str


@router.post("/sync", response_model=SyncResponse)
def sync_ynab_data(req: SyncRequest | None = None):
    try:
        budget_id = req.budget_id if req else None
        result = run_sync(budget_id=budget_id)
        return SyncResponse(**result)
    except SyncError as e:
        status = 422 if e.code == "YNAB_API_KEY_MISSING" else \
                 429 if e.code == "YNAB_RATE_LIMITED" else 502
        return JSONResponse(
            status_code=status,
            content={"error": "sync_failed", "code": e.code, "detail": e.detail},
        )


@router.get("/budgets")
def list_budgets():
    try:
        budgets = discover_budgets()
        return {"budgets": budgets}
    except SyncError as e:
        status = 422 if e.code == "YNAB_API_KEY_MISSING" else 502
        return JSONResponse(
            status_code=status,
            content={"error": "budgets_failed", "code": e.code, "detail": e.detail},
        )
