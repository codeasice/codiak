"""Transaction Explorer API endpoints."""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from api.services.dragon_keeper.transaction_explorer import (
    search_transactions,
    get_payee_summary,
    bulk_recategorize_transactions,
)

router = APIRouter()


@router.get("/transactions")
def list_transactions(
    payee: str | None = Query(None, description="Payee name substring filter"),
    category_id: str | None = Query(None, description="Category ID filter"),
    date_from: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    amount_min: float | None = Query(None, description="Minimum absolute amount"),
    amount_max: float | None = Query(None, description="Maximum absolute amount"),
    sort_by: str = Query("date", description="Sort column: date, payee, amount, category"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
):
    return search_transactions(
        payee=payee,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


@router.get("/transactions/payee-summary")
def payee_summary(payee: str = Query(..., description="Payee name to summarize")):
    return get_payee_summary(payee)


class BulkRecategorizeRequest(BaseModel):
    transaction_ids: list[str]
    category_id: str


@router.post("/transactions/bulk-recategorize")
def bulk_recategorize(req: BulkRecategorizeRequest):
    return bulk_recategorize_transactions(req.transaction_ids, req.category_id)
