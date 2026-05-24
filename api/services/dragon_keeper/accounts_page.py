"""Accounts page service — per-account balances and monthly activity."""
from api.models.dragon_keeper.db import get_db


def get_accounts_with_activity() -> dict:
    conn = get_db()
    try:
        accounts = conn.execute("""
            SELECT id, name, type, balance, cleared_balance, uncleared_balance,
                   on_budget, note, interest_rate, credit_limit
            FROM accounts
            WHERE closed = 0 AND deleted = 0
            ORDER BY
                CASE type
                    WHEN 'checking' THEN 1
                    WHEN 'savings'  THEN 2
                    WHEN 'creditCard' THEN 3
                    ELSE 4
                END,
                name
        """).fetchall()

        if not accounts:
            return {"accounts": []}

        account_ids = [a["id"] for a in accounts]
        placeholders = ",".join("?" * len(account_ids))

        activity_rows = conn.execute(f"""
            SELECT
                account_id,
                strftime('%Y-%m', date) AS month,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) AS debits,
                SUM(CASE WHEN amount > 0 THEN amount            ELSE 0 END) AS credits
            FROM transactions
            WHERE account_id IN ({placeholders})
              AND deleted = 0
              AND date >= date('now', '-7 months')
            GROUP BY account_id, month
            ORDER BY account_id, month
        """, account_ids).fetchall()

        activity_map: dict[str, list] = {a["id"]: [] for a in accounts}
        for row in activity_rows:
            activity_map[row["account_id"]].append({
                "month": row["month"],
                "debits": round(row["debits"], 2),
                "credits": round(row["credits"], 2),
            })

        return {
            "accounts": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "type": a["type"],
                    "balance": round(a["balance"], 2),
                    "cleared_balance": round(a["cleared_balance"], 2),
                    "uncleared_balance": round(a["uncleared_balance"], 2),
                    "on_budget": bool(a["on_budget"]),
                    "note": a["note"],
                    "interest_rate": a["interest_rate"],
                    "credit_limit": a["credit_limit"],
                    "monthly_activity": activity_map[a["id"]],
                }
                for a in accounts
            ]
        }
    finally:
        conn.close()


def set_credit_limit(account_id: str, limit: float | None) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute(
            "UPDATE accounts SET credit_limit = ? WHERE id = ? AND deleted = 0",
            (limit, account_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def set_interest_rate(account_id: str, rate: float | None) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute(
            "UPDATE accounts SET interest_rate = ? WHERE id = ? AND deleted = 0",
            (rate, account_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
