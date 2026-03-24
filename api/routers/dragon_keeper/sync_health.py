"""Sync health API endpoint."""
from fastapi import APIRouter
from api.services.dragon_keeper.sync_health import get_sync_health

router = APIRouter()


@router.get("/sync-health")
def sync_health():
    return get_sync_health()
