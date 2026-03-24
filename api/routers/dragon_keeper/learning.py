"""Learning and manual review API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.dragon_keeper.learning import (
    add_manual_review_payee,
    remove_manual_review_payee,
    get_manual_review_list,
)

router = APIRouter()


class ManualReviewRequest(BaseModel):
    payee_name: str


@router.get("/manual-review-payees")
def list_manual_review():
    return {"payees": get_manual_review_list()}


@router.post("/manual-review-payees")
def add_manual_review(req: ManualReviewRequest):
    added = add_manual_review_payee(req.payee_name)
    return {"added": added, "payee_name": req.payee_name}


@router.delete("/manual-review-payees")
def remove_manual_review(req: ManualReviewRequest):
    removed = remove_manual_review_payee(req.payee_name)
    return {"removed": removed, "payee_name": req.payee_name}
