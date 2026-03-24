"""Write-back API endpoints."""
from fastapi import APIRouter
from api.services.dragon_keeper.write_back import process_write_back_queue, get_write_back_status

router = APIRouter()


@router.post("/write-back/process")
def trigger_write_back():
    return process_write_back_queue()


@router.get("/write-back/status")
def write_back_status():
    return get_write_back_status()
