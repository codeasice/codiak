"""Account summary API endpoint."""
from fastapi import APIRouter
from api.services.dragon_keeper.account_summary import get_account_summary

router = APIRouter()


@router.get("/account-summary")
def account_summary():
    return get_account_summary()
