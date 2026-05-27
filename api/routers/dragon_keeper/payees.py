"""Payee metadata (display names and notes) API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.models.dragon_keeper.db import get_db, _now_utc

router = APIRouter()


@router.get("/payees")
def list_payees():
    """Return all payees with their display_name and note."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, name, display_name, note FROM payees WHERE deleted = 0 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


class UpdatePayeeRequest(BaseModel):
    display_name: str | None = None
    note: str | None = None


@router.patch("/payees/{payee_id}")
def update_payee(payee_id: str, req: UpdatePayeeRequest):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM payees WHERE id = ?", (payee_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Payee not found")
        conn.execute(
            "UPDATE payees SET display_name = ?, note = ?, updated_at = ? WHERE id = ?",
            (req.display_name or None, req.note or None, _now_utc(), payee_id),
        )
        conn.commit()
        return {"status": "updated", "id": payee_id}
    finally:
        conn.close()
