"""Categorization pipeline API endpoints."""
import os
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.dragon_keeper.categorization import run_categorization_pipeline
from api.services.dragon_keeper.llm_categorizer import get_llm_pending_count, DEFAULT_MAX_TRANSACTIONS
from api.services.dragon_keeper.learning import check_and_create_rule
from api.models.dragon_keeper.db import (
    get_db, get_queue_stats, get_pending_review_transactions,
    approve_categorization, skip_categorization, enqueue_write_back,
)

router = APIRouter()


class ApproveRequest(BaseModel):
    transaction_id: str
    category_id: str


class SkipRequest(BaseModel):
    transaction_id: str


@router.post("/categorize")
def trigger_categorization(reprocess: bool = False, llm_limit: int | None = None):
    result = run_categorization_pipeline(reprocess=reprocess, llm_limit=llm_limit)
    return result


@router.get("/queue-stats")
def queue_stats():
    conn = get_db()
    try:
        stats = get_queue_stats(conn)
        pending = stats.get("pending_count", 0) or 0
        total = stats.get("total_count", 0) or 0
        categorized = stats.get("categorized_count", 0) or 0
        pct = round((categorized / total * 100) if total > 0 else 0, 1)
        awaiting_llm = get_llm_pending_count()
        return {
            "pending_count": pending,
            "approved_count": stats.get("approved_count", 0) or 0,
            "rule_applied_count": stats.get("rule_applied_count", 0) or 0,
            "skipped_count": stats.get("skipped_count", 0) or 0,
            "categorized_count": categorized,
            "total_count": total,
            "categorization_percentage": pct,
            "estimated_seconds": pending * 4,
            "llm_available": bool(os.getenv("OPENAI_API_KEY")),
            "awaiting_llm": awaiting_llm,
            "llm_batch_size": DEFAULT_MAX_TRANSACTIONS,
        }
    finally:
        conn.close()


@router.get("/queue")
def get_queue():
    conn = get_db()
    try:
        items = get_pending_review_transactions(conn)
        return {"items": items, "total_count": len(items)}
    finally:
        conn.close()


@router.post("/queue/approve")
def approve_item(req: ApproveRequest):
    conn = get_db()
    try:
        approve_categorization(conn, req.transaction_id, req.category_id)
        enqueue_write_back(conn, req.transaction_id, req.category_id)
        conn.commit()
        payee = conn.execute(
            "SELECT payee_name FROM transactions WHERE id = ?",
            (req.transaction_id,),
        ).fetchone()
        rule_created = None
        if payee and payee["payee_name"]:
            rule_created = check_and_create_rule(payee["payee_name"], req.category_id)
        return {
            "status": "approved",
            "transaction_id": req.transaction_id,
            "rule_created": rule_created,
        }
    finally:
        conn.close()


@router.post("/queue/approve-all")
def approve_all():
    conn = get_db()
    try:
        items = get_pending_review_transactions(conn)
        approved = 0
        for item in items:
            cid = item.get("suggested_category_id")
            if cid:
                approve_categorization(conn, item["id"], cid)
                enqueue_write_back(conn, item["id"], cid)
                approved += 1
        conn.commit()
        return {"approved_count": approved}
    finally:
        conn.close()


@router.post("/queue/skip")
def skip_item(req: SkipRequest):
    conn = get_db()
    try:
        skip_categorization(conn, req.transaction_id)
        conn.commit()
        return {"status": "skipped", "transaction_id": req.transaction_id}
    finally:
        conn.close()


@router.post("/queue/unskip")
def unskip_item(req: SkipRequest):
    """Return a skipped transaction back to the review queue."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE transactions SET categorization_status = 'pending_review', updated_at = ?
            WHERE id = ? AND categorization_status = 'skipped'
        """, (_now_utc(), req.transaction_id))
        conn.commit()
        return {"status": "unskipped", "transaction_id": req.transaction_id}
    finally:
        conn.close()


@router.post("/queue/unskip-all")
def unskip_all():
    """Return all skipped transactions back to the review queue."""
    conn = get_db()
    try:
        cursor = conn.execute("""
            UPDATE transactions SET categorization_status = 'pending_review', updated_at = ?
            WHERE categorization_status = 'skipped'
        """, (_now_utc(),))
        conn.commit()
        return {"status": "unskipped", "count": cursor.rowcount}
    finally:
        conn.close()


class RecategorizeRequest(BaseModel):
    transaction_id: str
    category_id: str


@router.post("/recategorize")
def recategorize_transaction(req: RecategorizeRequest):
    """Re-categorize an already-categorized transaction."""
    conn = get_db()
    try:
        conn.execute("""
            UPDATE transactions
            SET category_id = ?, categorization_status = 'approved',
                suggested_category_id = ?, suggestion_confidence = 1.0,
                suggestion_source = 'manual', updated_at = datetime('now')
            WHERE id = ?
        """, (req.category_id, req.category_id, req.transaction_id))
        enqueue_write_back(conn, req.transaction_id, req.category_id)
        conn.commit()
        payee = conn.execute(
            "SELECT payee_name FROM transactions WHERE id = ?",
            (req.transaction_id,),
        ).fetchone()
        if payee and payee["payee_name"]:
            check_and_create_rule(payee["payee_name"], req.category_id)
        return {"status": "recategorized", "transaction_id": req.transaction_id}
    finally:
        conn.close()


@router.get("/categories")
def list_categories():
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT c.id, c.name, cg.name as group_name
            FROM categories c
            JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE c.hidden = 0 AND c.deleted = 0 AND cg.hidden = 0 AND cg.deleted = 0
            ORDER BY cg.name, c.name
        """).fetchall()
        return {"categories": [dict(r) for r in rows]}
    finally:
        conn.close()
