"""Dragon Keeper engagement tracking endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from api.services.dragon_keeper.engagement import (
    record_visit,
    record_actions,
    get_engagement_data,
)

router = APIRouter()


class ActionRequest(BaseModel):
    count: int = 1


@router.post("/engagement/visit")
def post_visit():
    return record_visit()


@router.post("/engagement/action")
def post_action(req: ActionRequest):
    return record_actions(req.count)


@router.get("/engagement")
def get_engagement():
    return get_engagement_data()
