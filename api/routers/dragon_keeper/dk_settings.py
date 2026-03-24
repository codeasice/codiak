"""Dragon Keeper settings API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from api.models.dragon_keeper.db import get_db, get_setting, set_setting

router = APIRouter()

SETTINGS_KEYS = {
    "projection_days": {"default": "30", "type": "int"},
    "buffer_amount": {"default": "100", "type": "float"},
    "ynab_budget_id": {"default": "", "type": "str"},
}


@router.get("/settings")
def get_settings():
    conn = get_db()
    try:
        result = {}
        for key, meta in SETTINGS_KEYS.items():
            val = get_setting(conn, key)
            if val is None:
                val = meta["default"]
            if meta["type"] == "int":
                result[key] = int(val) if val else int(meta["default"])
            elif meta["type"] == "float":
                result[key] = float(val) if val else float(meta["default"])
            else:
                result[key] = val
        return result
    finally:
        conn.close()


class UpdateSettingsRequest(BaseModel):
    projection_days: int | None = None
    buffer_amount: float | None = None


@router.patch("/settings")
def update_settings(req: UpdateSettingsRequest):
    conn = get_db()
    try:
        updated = []
        if req.projection_days is not None:
            set_setting(conn, "projection_days", str(max(7, min(365, req.projection_days))))
            updated.append("projection_days")
        if req.buffer_amount is not None:
            set_setting(conn, "buffer_amount", str(max(0, req.buffer_amount)))
            updated.append("buffer_amount")
        conn.commit()
        return {"status": "updated", "updated_keys": updated}
    finally:
        conn.close()
