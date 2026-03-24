"""Keeper Agent chat API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from api.services.dragon_keeper.keeper_agent import chat, get_history, reset_chat

router = APIRouter(tags=["keeper-agent"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def keeper_chat(req: ChatRequest):
    result = await chat(req.message)
    return result


@router.get("/chat/history")
def keeper_history():
    return {"messages": get_history()}


@router.delete("/chat/history")
def keeper_clear():
    reset_chat()
    return {"status": "cleared"}
