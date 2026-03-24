"""Rule preview and bulk reclassify API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.dragon_keeper.rule_preview import preview_matches, reclassify_transactions

router = APIRouter()


class PreviewRequest(BaseModel):
    payee_pattern: str
    match_type: str
    min_amount: float | None = None
    max_amount: float | None = None


class ReclassifyRequest(BaseModel):
    payee_pattern: str
    match_type: str
    category_id: str
    min_amount: float | None = None
    max_amount: float | None = None


@router.post("/rules/preview")
def rule_preview(req: PreviewRequest):
    return preview_matches(
        payee_pattern=req.payee_pattern,
        match_type=req.match_type,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
    )


@router.post("/rules/reclassify")
def rule_reclassify(req: ReclassifyRequest):
    return reclassify_transactions(
        payee_pattern=req.payee_pattern,
        match_type=req.match_type,
        category_id=req.category_id,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
    )
