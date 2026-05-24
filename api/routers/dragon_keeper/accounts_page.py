"""Accounts page API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.dragon_keeper.accounts_page import get_accounts_with_activity, set_interest_rate, set_credit_limit

router = APIRouter()


class InterestRateUpdate(BaseModel):
    rate: float | None = None


class CreditLimitUpdate(BaseModel):
    limit: float | None = None


@router.get("/accounts-page")
def accounts_page():
    return get_accounts_with_activity()


@router.put("/accounts-page/{account_id}/interest-rate")
def update_interest_rate(account_id: str, body: InterestRateUpdate):
    ok = set_interest_rate(account_id, body.rate)
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"ok": True}


@router.put("/accounts-page/{account_id}/credit-limit")
def update_credit_limit(account_id: str, body: CreditLimitUpdate):
    ok = set_credit_limit(account_id, body.limit)
    if not ok:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"ok": True}
