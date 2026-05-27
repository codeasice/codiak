"""Account summary service for dashboard cards."""
import logging
from api.models.dragon_keeper.db import get_db
from api.services.dragon_keeper.paycheck_tracer import get_current_period_remaining

logger = logging.getLogger("dragon_keeper.account_summary")


def get_account_summary() -> dict:
    conn = get_db()
    try:
        # Checking accounts
        checking_rows = conn.execute("""
            SELECT id, name, balance
            FROM accounts
            WHERE type = 'checking' AND on_budget = 1 AND closed = 0 AND deleted = 0
            ORDER BY name
        """).fetchall()
        checking_accounts = [{"id": r["id"], "name": r["name"], "balance": r["balance"]} for r in checking_rows]
        checking_total = sum(a["balance"] for a in checking_accounts)

        # Credit cards
        cc_rows = conn.execute("""
            SELECT id, name, balance
            FROM accounts
            WHERE type = 'creditCard' AND closed = 0 AND deleted = 0
            ORDER BY name
        """).fetchall()
        credit_cards = [{"id": r["id"], "name": r["name"], "balance": r["balance"]} for r in cc_rows]
        credit_card_total = sum(a["balance"] for a in credit_cards)

        has_data = conn.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()["cnt"] > 0

        remaining = get_current_period_remaining()

        return {
            "checking": {
                "total": round(checking_total, 2),
                "accounts": checking_accounts,
            },
            "credit_cards": {
                "total": round(credit_card_total, 2),
                "accounts": credit_cards,
            },
            "remaining_period": remaining,
            "has_data": has_data,
        }
    finally:
        conn.close()
