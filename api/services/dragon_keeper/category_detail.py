"""Category detail service — fetches spending timeline and transactions for a single category."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    get_category_transactions,
    get_category_spending_over_time,
)

logger = logging.getLogger("dragon_keeper.category_detail")


def get_category_detail(category_id: str) -> dict:
    """Return spending-over-time, recent transactions, and metadata for one category."""
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT c.id, c.name as category_name, cg.name as group_name
            FROM categories c
            JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE c.id = ?
            """,
            (category_id,),
        ).fetchone()

        if not row:
            return {
                "category_id": category_id,
                "category_name": "Unknown",
                "group_name": "Unknown",
                "spending_over_time": [],
                "transactions": [],
                "total_spending": 0,
                "transaction_count": 0,
            }

        spending = get_category_spending_over_time(conn, category_id, periods=12)
        transactions = get_category_transactions(conn, category_id, limit=100)

        total_spending = round(sum(p["total"] for p in spending), 2)
        transaction_count = len(transactions)

        return {
            "category_id": row["id"],
            "category_name": row["category_name"],
            "group_name": row["group_name"],
            "spending_over_time": [
                {
                    "period_start": p["period_start"],
                    "total": round(p["total"], 2),
                    "txn_count": p["txn_count"],
                }
                for p in spending
            ],
            "transactions": [
                {
                    "id": t["id"],
                    "date": t["date"],
                    "amount": t["amount"],
                    "payee_name": t["payee_name"],
                    "memo": t["memo"],
                    "account_id": t["account_id"],
                    "account_name": t["account_name"],
                }
                for t in transactions
            ],
            "total_spending": total_spending,
            "transaction_count": transaction_count,
        }
    finally:
        conn.close()
