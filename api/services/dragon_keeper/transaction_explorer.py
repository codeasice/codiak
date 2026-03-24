"""Transaction Explorer service — search, filter, paginate, and summarize transactions."""
from api.models.dragon_keeper.db import get_db


def search_transactions(
    payee: str | None = None,
    category_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    sort_by: str = "date",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    conn = get_db()
    try:
        where_parts = ["t.deleted = 0", "t.transfer_account_id IS NULL"]
        params: list = []

        if payee:
            where_parts.append("t.payee_name LIKE ?")
            params.append(f"%{payee}%")
        if category_id:
            where_parts.append("t.category_id = ?")
            params.append(category_id)
        if date_from:
            where_parts.append("t.date >= ?")
            params.append(date_from)
        if date_to:
            where_parts.append("t.date <= ?")
            params.append(date_to)
        if amount_min is not None:
            where_parts.append("ABS(t.amount) >= ?")
            params.append(amount_min)
        if amount_max is not None:
            where_parts.append("ABS(t.amount) <= ?")
            params.append(amount_max)

        where = " AND ".join(where_parts)

        allowed_sorts = {
            "date": "t.date",
            "payee": "t.payee_name",
            "amount": "ABS(t.amount)",
            "category": "c.name",
        }
        order_col = allowed_sorts.get(sort_by, "t.date")
        order_dir = "ASC" if sort_dir.lower() == "asc" else "DESC"

        count_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM transactions t WHERE {where}", params
        ).fetchone()
        total_count = count_row["cnt"] if count_row else 0

        offset = (max(1, page) - 1) * page_size

        rows = conn.execute(f"""
            SELECT t.id, t.date, t.amount, t.payee_name, t.memo,
                   t.category_id, c.name as category_name, cg.name as group_name,
                   a.name as account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            LEFT JOIN accounts a ON t.account_id = a.id
            WHERE {where}
            ORDER BY {order_col} {order_dir}
            LIMIT ? OFFSET ?
        """, params + [page_size, offset]).fetchall()

        sum_row = conn.execute(f"""
            SELECT COALESCE(SUM(ABS(t.amount)), 0) as total_amount
            FROM transactions t
            WHERE {where}
        """, params).fetchone()

        total_pages = max(1, -(-total_count // page_size))

        return {
            "transactions": [dict(r) for r in rows],
            "total_count": total_count,
            "total_amount": round(sum_row["total_amount"], 2) if sum_row else 0,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    finally:
        conn.close()


def get_payee_summary(payee: str) -> dict:
    """Get detailed summary for a payee: count, total, date range, category breakdown, recurring indicator."""
    conn = get_db()
    try:
        where = "t.deleted = 0 AND t.transfer_account_id IS NULL AND t.payee_name LIKE ?"
        params = [f"%{payee}%"]

        agg = conn.execute(f"""
            SELECT COUNT(*) as txn_count,
                   COALESCE(SUM(ABS(t.amount)), 0) as total_amount,
                   MIN(t.date) as first_date,
                   MAX(t.date) as last_date
            FROM transactions t
            WHERE {where}
        """, params).fetchone()

        if not agg or agg["txn_count"] == 0:
            return {
                "payee": payee,
                "transaction_count": 0,
                "total_amount": 0,
                "first_date": None,
                "last_date": None,
                "category_breakdown": [],
                "likely_recurring": False,
            }

        cat_rows = conn.execute(f"""
            SELECT COALESCE(c.name, 'Uncategorized') as category_name,
                   t.category_id,
                   COUNT(*) as count,
                   COALESCE(SUM(ABS(t.amount)), 0) as amount
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE {where}
            GROUP BY t.category_id
            ORDER BY count DESC
        """, params).fetchall()

        category_breakdown = [
            {
                "category_id": r["category_id"],
                "category_name": r["category_name"],
                "count": r["count"],
                "amount": round(r["amount"], 2),
            }
            for r in cat_rows
        ]

        likely_recurring = _detect_recurring(conn, payee)

        return {
            "payee": payee,
            "transaction_count": agg["txn_count"],
            "total_amount": round(agg["total_amount"], 2),
            "first_date": agg["first_date"],
            "last_date": agg["last_date"],
            "category_breakdown": category_breakdown,
            "has_mixed_categories": len(category_breakdown) > 1,
            "likely_recurring": likely_recurring,
        }
    finally:
        conn.close()


def _detect_recurring(conn, payee: str) -> bool:
    """Heuristic: if 3+ transactions exist and intervals cluster around 28-32 days, it's likely recurring."""
    rows = conn.execute("""
        SELECT date FROM transactions
        WHERE payee_name LIKE ? AND deleted = 0 AND transfer_account_id IS NULL
        ORDER BY date
    """, (f"%{payee}%",)).fetchall()

    if len(rows) < 3:
        return False

    from datetime import datetime
    dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]

    intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    monthly_intervals = [d for d in intervals if 25 <= d <= 35]

    return len(monthly_intervals) >= len(intervals) * 0.6


def bulk_recategorize_transactions(transaction_ids: list[str], category_id: str) -> dict:
    """Re-categorize multiple transactions at once and queue write-backs."""
    from api.models.dragon_keeper.db import enqueue_write_back, _now_utc

    conn = get_db()
    try:
        now = _now_utc()
        updated = 0
        for tid in transaction_ids:
            conn.execute("""
                UPDATE transactions
                SET category_id = ?, categorization_status = 'approved',
                    suggested_category_id = ?, suggestion_confidence = 1.0,
                    suggestion_source = 'manual', updated_at = ?
                WHERE id = ? AND deleted = 0
            """, (category_id, category_id, now, tid))
            if conn.total_changes:
                enqueue_write_back(conn, tid, category_id)
                updated += 1
        conn.commit()
        return {"updated": updated, "category_id": category_id}
    finally:
        conn.close()
