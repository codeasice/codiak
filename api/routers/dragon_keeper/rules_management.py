"""Rules management API endpoints – CRUD for categorization rules."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.dragon_keeper.rules_management import (
    list_rules,
    create_new_rule,
    update_existing_rule,
    delete_existing_rule,
    restore_rule,
)

router = APIRouter()


class RuleCreateRequest(BaseModel):
    payee_pattern: str
    match_type: str = "contains"
    category_id: str
    min_amount: float | None = None
    max_amount: float | None = None


class RuleUpdateRequest(BaseModel):
    payee_pattern: str
    match_type: str = "contains"
    category_id: str
    min_amount: float | None = None
    max_amount: float | None = None


class RuleRestoreRequest(BaseModel):
    payee_pattern: str
    match_type: str
    category_id: str
    min_amount: float | None = None
    max_amount: float | None = None
    confidence: float = 1.0
    source: str = "manual"
    times_applied: int = 0


@router.get("/rules")
def get_rules():
    return {"rules": list_rules()}


@router.post("/rules")
def create_rule_endpoint(req: RuleCreateRequest):
    rule = create_new_rule(
        payee_pattern=req.payee_pattern,
        match_type=req.match_type,
        category_id=req.category_id,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
    )
    return rule


@router.put("/rules/{rule_id}")
def update_rule_endpoint(rule_id: int, req: RuleUpdateRequest):
    try:
        rule = update_existing_rule(
            rule_id=rule_id,
            payee_pattern=req.payee_pattern,
            match_type=req.match_type,
            category_id=req.category_id,
            min_amount=req.min_amount,
            max_amount=req.max_amount,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule_endpoint(rule_id: int):
    try:
        deleted = delete_existing_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return deleted


@router.post("/rules/restore")
def restore_rule_endpoint(req: RuleRestoreRequest):
    rule = restore_rule(
        payee_pattern=req.payee_pattern,
        match_type=req.match_type,
        category_id=req.category_id,
        min_amount=req.min_amount,
        max_amount=req.max_amount,
        confidence=req.confidence,
        source=req.source,
        times_applied=req.times_applied,
    )
    return rule
