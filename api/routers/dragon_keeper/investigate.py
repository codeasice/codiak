from fastapi import APIRouter
from pydantic import BaseModel
from api.services.dragon_keeper.investigate import investigate_payee

router = APIRouter()


class InvestigateRequest(BaseModel):
    payee_name: str
    amount: float | None = None
    memo: str | None = None


@router.post("/investigate")
def investigate(req: InvestigateRequest):
    return investigate_payee(req.payee_name, req.amount, req.memo)
