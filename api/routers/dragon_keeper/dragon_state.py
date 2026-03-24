"""Dragon state and keeper greeting API endpoints."""
from fastapi import APIRouter
from api.services.dragon_keeper.dragon_state import compute_dragon_state, generate_greeting

router = APIRouter()


@router.get("/dragon-state")
def get_dragon_state():
    return compute_dragon_state()


@router.get("/greeting")
def get_greeting():
    return generate_greeting()
