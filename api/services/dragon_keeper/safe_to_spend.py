"""Safe-to-Spend calculation service."""
import logging
from api.models.dragon_keeper.db import get_db

logger = logging.getLogger("dragon_keeper.safe_to_spend")

STS_HEALTHY_THRESHOLD = 1000.0
STS_CAUTION_THRESHOLD = 200.0


def _get_checking_balance(conn) -> float:
    row = conn.execute("""
        SELECT COALESCE(SUM(balance), 0.0) as total
        FROM accounts
        WHERE type IN ('checking') AND on_budget = 1 AND closed = 0 AND deleted = 0
    """).fetchone()
    return row["total"]


def _get_credit_card_debt(conn) -> float:
    row = conn.execute("""
        SELECT COALESCE(SUM(balance), 0.0) as total
        FROM accounts
        WHERE type = 'creditCard' AND closed = 0 AND deleted = 0
    """).fetchone()
    return row["total"]


def _get_pending_outflows(conn) -> float:
    """Uncleared future outgoing transactions."""
    row = conn.execute("""
        SELECT COALESCE(SUM(ABS(amount)), 0.0) as total
        FROM transactions
        WHERE amount < 0
        AND cleared = 'uncleared'
        AND date >= date('now')
        AND deleted = 0
    """).fetchone()
    return row["total"]


def calculate_safe_to_spend() -> dict:
    conn = get_db()
    try:
        checking = _get_checking_balance(conn)
        credit_debt = _get_credit_card_debt(conn)
        pending = _get_pending_outflows(conn)

        # STS = checking balance + credit card balance (negative) - pending outflows
        sts = round(checking + credit_debt - pending, 2)

        if sts >= STS_HEALTHY_THRESHOLD:
            status = "healthy"
        elif sts >= STS_CAUTION_THRESHOLD:
            status = "caution"
        else:
            status = "critical"

        has_data = conn.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()["cnt"] > 0

        return {
            "amount": sts,
            "status": status,
            "checking_balance": round(checking, 2),
            "credit_card_debt": round(credit_debt, 2),
            "pending_outflows": round(pending, 2),
            "has_data": has_data,
        }
    finally:
        conn.close()
