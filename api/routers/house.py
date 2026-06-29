from fastapi import APIRouter
from api.services.house_service import get_rooms

router = APIRouter()


@router.get("/rooms")
def list_rooms():
    return get_rooms()
