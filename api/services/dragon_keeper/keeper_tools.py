"""Shared tool implementations for the Keeper Agent and MCP server.

Both the in-app chat agent (OpenAI function calling) and the MCP server are
thin wrappers over these functions. New capabilities go here first.
"""
import logging
import re
import sqlite3

from api.models.dragon_keeper.db import (
    get_db,
    get_spending_summary,
    get_account_balances,
    get_recent_spending_by_category,
    get_queue_stats,
    get_pending_review_transactions,
    approve_categorization,
    enqueue_write_back,
    get_current_streak,
    create_rule,
    update_rule,
)
from api.services.dragon_keeper.safe_to_spend import calculate_safe_to_spend
from api.services.dragon_keeper.learning import check_and_create_rule

logger = logging.getLogger("dragon_keeper.keeper_tools")

_EMOJI_RE = re.compile(
    r"[\U00002600-\U000027BF\U0001F300-\U0001FAFF\U0000FE00-\U0000FE0F\U0000200D]+"
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def find_category(conn: sqlite3.Connection, name: str) -> dict | None:
    """Fuzzy category lookup: exact LIKE, then emoji-stripped fallback."""
    row = conn.execute(
        "SELECT id, name FROM categories WHERE name LIKE ? AND deleted = 0",
        (f"%{name}%",),
    ).fetchone()
    if row:
        return dict(row)

    stripped = _strip_emoji(name)
    if stripped != name:
        row = conn.execute(
            "SELECT id, name FROM categories WHERE name LIKE ? AND deleted = 0",
            (f"%{stripped}%",),
        ).fetchone()
        if row:
            return dict(row)

    name_lower = stripped.lower()
    for cat in conn.execute("SELECT id, name FROM categories WHERE deleted = 0").fetchall():
        if name_lower in _strip_emoji(cat["name"]).lower():
            return dict(cat)
    return None


def tool_query_spending(
    payee: str | None = None,
    category: str | None = None,
    days: int = 30,
) -> dict:
    conn = get_db()
    try:
        return get_spending_summary(
            conn,
            payee_pattern=payee,
            category_name=category,
            days=days if days else None,
        )
    finally:
        conn.close()


def tool_get_balances() -> dict:
    conn = get_db()
    try:
        balances = get_account_balances(conn)
    finally:
        conn.close()
    return {"accounts": balances, "safe_to_spend": calculate_safe_to_spend()}


def tool_get_spending_breakdown(days: int = 30) -> dict:
    conn = get_db()
    try:
        cats = get_recent_spending_by_category(conn, days=days)
    finally:
        conn.close()
    return {"categories": cats, "days": days}


def tool_get_pending_categorizations() -> dict:
    conn = get_db()
    try:
        items = get_pending_review_transactions(conn)
    finally:
        conn.close()
    return {"pending": items, "count": len(items)}


def tool_approve_transactions(transaction_ids: list[str]) -> dict:
    conn = get_db()
    try:
        pending_map = {item["id"]: item for item in get_pending_review_transactions(conn)}
        approved = 0
        for tid in transaction_ids:
            item = pending_map.get(tid)
            if item and item.get("suggested_category_id"):
                cid = item["suggested_category_id"]
                approve_categorization(conn, tid, cid)
                enqueue_write_back(conn, tid, cid)
                approved += 1
                if item.get("payee_name"):
                    check_and_create_rule(item["payee_name"], cid)
        conn.commit()
    finally:
        conn.close()
    return {"approved_count": approved, "requested": len(transaction_ids)}


def tool_correct_transaction(transaction_id: str, category_name: str) -> dict:
    """Correct a single transaction's category and enqueue write-back."""
    conn = get_db()
    try:
        cat = find_category(conn, category_name)
        if not cat:
            return {"error": f"Category '{category_name}' not found"}
        approve_categorization(conn, transaction_id, cat["id"])
        enqueue_write_back(conn, transaction_id, cat["id"])
        conn.commit()
        txn = conn.execute(
            "SELECT payee_name FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()
        if txn and txn["payee_name"]:
            check_and_create_rule(txn["payee_name"], cat["id"])
    finally:
        conn.close()
    return {"status": "corrected", "transaction_id": transaction_id, "category": cat["name"]}


def tool_recategorize_by_payee(
    payee: str,
    new_category: str,
    current_category: str | None = None,
) -> dict:
    """Bulk recategorize transactions matching a payee pattern (partial match).

    Also creates or updates an exact-match rule for future transactions.
    Use set_payee_category (rules_management) for strict exact-match semantics.
    """
    conn = get_db()
    try:
        cat = find_category(conn, new_category)
        if not cat:
            return {"error": f"Category '{new_category}' not found"}
        new_cid = cat["id"]

        where = "t.payee_name LIKE ? AND t.deleted = 0 AND t.transfer_account_id IS NULL"
        params: list = [f"%{payee}%"]

        if current_category:
            cur_cat = find_category(conn, current_category)
            if cur_cat:
                where += " AND t.category_id = ?"
                params.append(cur_cat["id"])
            else:
                where += " AND c.name LIKE ?"
                params.append(f"%{current_category}%")

        rows = conn.execute(f"""
            SELECT t.id FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE {where}
        """, params).fetchall()

        if not rows:
            return {"error": f"No transactions found matching payee '{payee}'. Rule not created."}

        for r in rows:
            conn.execute("""
                UPDATE transactions
                SET category_id = ?, categorization_status = 'approved',
                    suggested_category_id = ?, suggestion_confidence = 1.0,
                    suggestion_source = 'manual'
                WHERE id = ?
            """, (new_cid, new_cid, r["id"]))
            enqueue_write_back(conn, r["id"], new_cid)

        existing = conn.execute(
            "SELECT id FROM categorization_rules WHERE LOWER(payee_pattern) = LOWER(?) AND match_type = 'exact' LIMIT 1",
            (payee,),
        ).fetchone()
        if existing:
            update_rule(conn, existing["id"], payee, "exact", new_cid, None, None, 1.0)
            rule_action = "updated"
        else:
            create_rule(conn, payee, "exact", new_cid, None, None, 1.0, "manual")
            rule_action = "created"

        conn.commit()
    finally:
        conn.close()
    return {
        "updated": len(rows),
        "payee_filter": payee,
        "new_category": cat["name"],
        "rule": rule_action,
    }


def tool_search_categories(query: str) -> dict:
    """Search for categories by name. Returns actual matches from the database."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT c.name, cg.name as group_name
            FROM categories c
            LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE LOWER(c.name) LIKE LOWER(?) AND c.deleted = 0 AND c.hidden = 0
            ORDER BY cg.name, c.name
        """, (f"%{query}%",)).fetchall()
        matches = [{"name": r["name"], "group": r["group_name"]} for r in rows]
        return {"query": query, "matches": matches, "count": len(matches)}
    finally:
        conn.close()


def tool_sync(flush_queue: bool = True) -> dict:
    """Pull fresh data from YNAB and optionally push approved categorizations back."""
    from api.services.dragon_keeper.sync_engine import run_sync, SyncError
    from api.services.dragon_keeper.write_back import process_write_back_queue
    try:
        result = run_sync()
        if flush_queue:
            result["write_back"] = process_write_back_queue()
        return result
    except SyncError as e:
        return {"error": e.code, "detail": e.detail}


def tool_generate_debrief() -> dict:
    conn = get_db()
    try:
        breakdown = get_recent_spending_by_category(conn, days=7)
        streak = get_current_streak(conn)
        queue = get_queue_stats(conn)
    finally:
        conn.close()
    return {
        "safe_to_spend": calculate_safe_to_spend(),
        "week_spending": breakdown[:10],
        "streak": streak,
        "queue": queue,
    }
