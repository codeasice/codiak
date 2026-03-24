"""Sync health service."""
import logging
from datetime import datetime, timezone, timedelta
from api.models.dragon_keeper.db import get_db, get_all_sync_states

logger = logging.getLogger("dragon_keeper.sync_health")

WARNING_HOURS = 24
ERROR_DAYS = 7


def _compute_status(last_sync_at: str | None, last_sync_status: str) -> str:
    if last_sync_status == "never" or not last_sync_at:
        return "never"
    if last_sync_status != "success":
        return "error"
    try:
        synced = datetime.fromisoformat(last_sync_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = now - synced
        if age > timedelta(days=ERROR_DAYS):
            return "error"
        if age > timedelta(hours=WARNING_HOURS):
            return "warning"
        return "ok"
    except (ValueError, TypeError):
        return "error"


def get_sync_health() -> dict:
    conn = get_db()
    try:
        states = get_all_sync_states(conn)
        accounts = []
        has_warning_or_error = False
        for s in states:
            status = _compute_status(s["last_sync_at"], s["last_sync_status"])
            if status in ("warning", "error"):
                has_warning_or_error = True
            accounts.append({
                "account_id": s["account_id"],
                "account_name": s["account_name"],
                "status": status,
                "last_sync_at": s["last_sync_at"],
                "last_error": s["last_error"],
                "transactions_synced": s["transactions_synced"],
            })
        return {
            "accounts": accounts,
            "has_warning_or_error": has_warning_or_error,
            "has_data": len(accounts) > 0,
        }
    finally:
        conn.close()
