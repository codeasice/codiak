"""Recurring items (subscriptions, bills, paychecks) API endpoints."""
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.models.dragon_keeper.db import get_db, _now_utc
from api.services.dragon_keeper.recurring_detection import detect_recurring_transactions
from api.services.dragon_keeper.recurring_linking import (
    CHARGE_HISTORY_LIMIT,
    find_duplicate_suggestions,
    get_combined_charge_history,
    link_by_payee_name,
    link_recurring_items,
    load_aliases_by_recurring_id,
    preview_link,
    preview_link_by_payee_name,
    unlink_payee,
)

router = APIRouter()


@router.post("/recurring/detect")
def trigger_detection():
    return detect_recurring_transactions()


@router.get("/recurring")
def list_recurring():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, payee_name, type, cadence, expected_amount,
                   expected_day, expected_day_2, next_expected_date, confirmed, include_in_sts,
                   last_seen_date, avg_amount, occurrence_count, cancelled_date,
                   is_subscription, status, created_at, updated_at
            FROM recurring_items
            ORDER BY type DESC, next_expected_date
        """).fetchall()

        aliases_by_id = load_aliases_by_recurring_id(conn)
        items = [dict(r) for r in rows]
        for item in items:
            item["confirmed"] = bool(item["confirmed"])
            item["include_in_sts"] = bool(item["include_in_sts"])
            item["is_subscription"] = bool(item["is_subscription"])
            linked = aliases_by_id.get(item["id"], [])
            item["linked_payees"] = linked
            item["all_payee_names"] = [item["payee_name"], *linked]
            item["charge_history"] = get_combined_charge_history(conn, item["all_payee_names"])

        active = [i for i in items if i["status"] == "active"]
        confirmed = [i for i in active if i["confirmed"]]

        def _to_monthly(item: dict) -> float:
            amt = item["expected_amount"]
            if item["cadence"] == "biweekly":
                return amt * 26 / 12
            elif item["cadence"] == "semi_monthly":
                return amt * 2
            elif item["cadence"] == "annual":
                return amt / 12
            return amt

        income_total = sum(_to_monthly(i) for i in confirmed if i["type"] == "income")
        expense_total = sum(_to_monthly(i) for i in confirmed if i["type"] == "expense")
        annual_expense_total = sum(i["expected_amount"] for i in confirmed if i["type"] == "expense" and i["cadence"] == "annual")

        cancelled_charges = []
        for item in items:
            if not item["is_subscription"] or item["status"] != "cancelled" or not item["cancelled_date"]:
                continue
            payee_names = item["all_payee_names"]
            placeholders = ",".join("?" * len(payee_names))
            charge_rows = conn.execute(f"""
                SELECT date, amount, id, payee_name
                FROM transactions
                WHERE LOWER(payee_name) IN ({placeholders})
                  AND date > ?
                  AND deleted = 0
                ORDER BY date DESC
            """, (*[n.lower() for n in payee_names], item["cancelled_date"])).fetchall()
            if charge_rows:
                cancelled_charges.append({
                    "recurring_id": item["id"],
                    "payee_name": item["payee_name"],
                    "cancelled_date": item["cancelled_date"],
                    "charges": [{"date": r["date"], "amount": r["amount"], "id": r["id"]} for r in charge_rows],
                })

        return {
            "items": items,
            "monthly_income": round(income_total, 2),
            "monthly_expenses": round(expense_total, 2),
            "annual_expenses": round(annual_expense_total, 2),
            "total_count": len(active),
            "unconfirmed_count": sum(1 for i in active if not i["confirmed"]),
            "cancelled_charges": cancelled_charges,
        }
    finally:
        conn.close()


class ConfirmRequest(BaseModel):
    confirmed: bool


@router.patch("/recurring/{item_id}/confirm")
def confirm_item(item_id: int, req: ConfirmRequest):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET confirmed = ?, updated_at = ? WHERE id = ?",
            (1 if req.confirmed else 0, _now_utc(), item_id),
        )
        conn.commit()
        return {"status": "updated", "id": item_id, "confirmed": req.confirmed}
    finally:
        conn.close()


class ToggleStsRequest(BaseModel):
    include_in_sts: bool


@router.patch("/recurring/{item_id}/sts")
def toggle_sts(item_id: int, req: ToggleStsRequest):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET include_in_sts = ?, updated_at = ? WHERE id = ?",
            (1 if req.include_in_sts else 0, _now_utc(), item_id),
        )
        conn.commit()
        return {"status": "updated", "id": item_id, "include_in_sts": req.include_in_sts}
    finally:
        conn.close()


class ToggleSubscriptionRequest(BaseModel):
    is_subscription: bool


@router.patch("/recurring/{item_id}/subscription")
def toggle_subscription(item_id: int, req: ToggleSubscriptionRequest):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET is_subscription = ?, updated_at = ? WHERE id = ?",
            (1 if req.is_subscription else 0, _now_utc(), item_id),
        )
        conn.commit()
        return {"status": "updated", "id": item_id, "is_subscription": req.is_subscription}
    finally:
        conn.close()


class CancelRequest(BaseModel):
    cancelled_date: str


@router.patch("/recurring/{item_id}/cancel")
def cancel_item(item_id: int, req: CancelRequest):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET cancelled_date = ?, status = 'cancelled', include_in_sts = 0, updated_at = ? WHERE id = ?",
            (req.cancelled_date, _now_utc(), item_id),
        )
        conn.commit()
        return {"status": "cancelled", "id": item_id, "cancelled_date": req.cancelled_date}
    finally:
        conn.close()


@router.patch("/recurring/{item_id}/archive")
def archive_item(item_id: int):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET status = 'archived', include_in_sts = 0, updated_at = ? WHERE id = ?",
            (_now_utc(), item_id),
        )
        conn.commit()
        return {"status": "archived", "id": item_id}
    finally:
        conn.close()


@router.patch("/recurring/{item_id}/uncancel")
def uncancel_item(item_id: int):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE recurring_items SET cancelled_date = NULL, status = 'active', include_in_sts = 1, updated_at = ? WHERE id = ?",
            (_now_utc(), item_id),
        )
        conn.commit()
        return {"status": "active", "id": item_id}
    finally:
        conn.close()


@router.delete("/recurring/{item_id}")
def dismiss_item(item_id: int):
    conn = get_db()
    try:
        conn.execute("DELETE FROM recurring_items WHERE id = ?", (item_id,))
        conn.commit()
        return {"status": "dismissed", "id": item_id}
    finally:
        conn.close()


class UpdateRecurringRequest(BaseModel):
    expected_amount: float | None = None
    expected_day: int | None = None
    cadence: str | None = None
    type: str | None = None


@router.patch("/recurring/{item_id}")
def update_item(item_id: int, req: UpdateRecurringRequest):
    conn = get_db()
    try:
        updates = []
        params = []
        if req.expected_amount is not None:
            updates.append("expected_amount = ?")
            params.append(req.expected_amount)
        if req.expected_day is not None:
            updates.append("expected_day = ?")
            params.append(req.expected_day)
        if req.cadence is not None:
            updates.append("cadence = ?")
            params.append(req.cadence)
        if req.type is not None:
            updates.append("type = ?")
            params.append(req.type)
        if not updates:
            return {"status": "no_changes"}
        updates.append("updated_at = ?")
        params.append(_now_utc())
        params.append(item_id)
        conn.execute(f"UPDATE recurring_items SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return {"status": "updated", "id": item_id}
    finally:
        conn.close()


class LinkRecurringRequest(BaseModel):
    source_recurring_id: int | None = None
    payee_name: str | None = None
    canonical_recurring_id: int | None = None
    force_amount: bool = False


@router.get("/recurring/duplicate-suggestions")
def duplicate_suggestions():
    return {"suggestions": find_duplicate_suggestions()}


@router.get("/recurring/{item_id}/link/preview")
def link_preview(
    item_id: int,
    source_recurring_id: int | None = None,
    payee_name: str | None = None,
    canonical_recurring_id: int | None = None,
):
    if payee_name:
        return preview_link_by_payee_name(item_id, payee_name)
    if source_recurring_id is None:
        raise HTTPException(status_code=400, detail="source_recurring_id or payee_name is required")
    return preview_link(item_id, source_recurring_id, canonical_recurring_id)


@router.post("/recurring/{item_id}/link")
def link_item(item_id: int, req: LinkRecurringRequest):
    if req.payee_name:
        return link_by_payee_name(item_id, req.payee_name, req.force_amount)
    if req.source_recurring_id is None:
        raise HTTPException(status_code=400, detail="source_recurring_id or payee_name is required")
    if req.canonical_recurring_id is None:
        raise HTTPException(status_code=400, detail="canonical_recurring_id is required when linking subscriptions")
    if req.canonical_recurring_id not in (item_id, req.source_recurring_id):
        raise HTTPException(status_code=400, detail="canonical_recurring_id must be one of the two items")
    return link_recurring_items(
        item_id,
        req.source_recurring_id,
        req.canonical_recurring_id,
        req.force_amount,
    )


@router.delete("/recurring/{item_id}/link/{payee_name:path}")
def unlink_item_payee(item_id: int, payee_name: str):
    return unlink_payee(item_id, unquote(payee_name))
