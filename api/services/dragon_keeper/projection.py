"""Cash flow projection engine — projects forward N days to find true safe-to-spend."""
import logging
from datetime import datetime, timedelta
from api.models.dragon_keeper.db import get_db, get_setting

logger = logging.getLogger("dragon_keeper.projection")

DEFAULT_PROJECTION_DAYS = 30
DEFAULT_BUFFER_AMOUNT = 100.0


def get_projection_settings(conn) -> tuple[int, float]:
    days_str = get_setting(conn, "projection_days")
    buffer_str = get_setting(conn, "buffer_amount")
    days = int(days_str) if days_str else DEFAULT_PROJECTION_DAYS
    buffer = float(buffer_str) if buffer_str else DEFAULT_BUFFER_AMOUNT
    return days, buffer


def project_cash_flow() -> dict:
    """Project cash flow forward and calculate true safe-to-spend.

    Returns:
        starting_balance, projection_days, buffer_amount,
        upcoming_income, upcoming_expenses, daily_projections,
        min_projected_balance, safe_to_spend, status,
        upcoming_items (list of recurring items in the window)
    """
    conn = get_db()
    try:
        projection_days, buffer = get_projection_settings(conn)
        today = datetime.now().date()
        end_date = today + timedelta(days=projection_days)

        checking = conn.execute("""
            SELECT COALESCE(SUM(balance), 0.0) as total
            FROM accounts
            WHERE type IN ('checking') AND on_budget = 1 AND closed = 0 AND deleted = 0
        """).fetchone()["total"]

        credit_debt = conn.execute("""
            SELECT COALESCE(SUM(balance), 0.0) as total
            FROM accounts
            WHERE type = 'creditCard' AND closed = 0 AND deleted = 0
        """).fetchone()["total"]

        starting_balance = round(checking + credit_debt, 2)

        pending_outflows = conn.execute("""
            SELECT COALESCE(SUM(ABS(amount)), 0.0) as total
            FROM transactions
            WHERE amount < 0 AND cleared = 'uncleared'
            AND date >= date('now') AND deleted = 0
        """).fetchone()["total"]

        recurring_items = conn.execute("""
            SELECT id, payee_name, type, cadence, expected_amount,
                   expected_day, next_expected_date, confirmed, include_in_sts
            FROM recurring_items
            WHERE include_in_sts = 1
            ORDER BY next_expected_date
        """).fetchall()

        events: list[dict] = []
        upcoming_items: list[dict] = []

        for item in recurring_items:
            item_dict = dict(item)
            next_date_str = item_dict["next_expected_date"]
            if not next_date_str:
                continue

            next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()

            def _add_event(d):
                amt = item_dict["expected_amount"]
                if item_dict["type"] == "expense":
                    amt = -amt
                events.append({
                    "date": d.isoformat(),
                    "amount": round(amt, 2),
                    "payee_name": item_dict["payee_name"],
                    "type": item_dict["type"],
                    "recurring_id": item_dict["id"],
                })

            cadence = item_dict["cadence"]

            if cadence == "biweekly":
                current = next_date
                while current <= end_date:
                    if current >= today:
                        _add_event(current)
                    current += timedelta(days=14)
            elif cadence == "monthly":
                current = next_date
                while current <= end_date:
                    if current >= today:
                        _add_event(current)
                    month = current.month + 1
                    year = current.year
                    if month > 12:
                        month = 1
                        year += 1
                    try:
                        current = current.replace(year=year, month=month)
                    except ValueError:
                        current = current.replace(year=year, month=month, day=28)
            elif cadence == "annual":
                if today <= next_date <= end_date:
                    _add_event(next_date)

            if today <= next_date <= end_date:
                upcoming_items.append({
                    "id": item_dict["id"],
                    "payee_name": item_dict["payee_name"],
                    "type": item_dict["type"],
                    "cadence": item_dict["cadence"],
                    "expected_amount": item_dict["expected_amount"],
                    "next_expected_date": next_date_str,
                    "confirmed": bool(item_dict["confirmed"]),
                })

        events.sort(key=lambda e: e["date"])

        balance = starting_balance - pending_outflows
        min_balance = balance
        min_balance_date = today.isoformat()

        total_upcoming_income = sum(e["amount"] for e in events if e["type"] == "income")
        total_upcoming_expenses = sum(abs(e["amount"]) for e in events if e["type"] == "expense")

        daily_projections: list[dict] = []
        current_day = today
        event_idx = 0

        while current_day <= end_date:
            day_str = current_day.isoformat()
            day_events = []
            while event_idx < len(events) and events[event_idx]["date"] == day_str:
                balance += events[event_idx]["amount"]
                day_events.append(events[event_idx])
                event_idx += 1

            daily_projections.append({
                "date": day_str,
                "balance": round(balance, 2),
                "events": day_events,
            })

            if balance < min_balance:
                min_balance = balance
                min_balance_date = day_str

            current_day += timedelta(days=1)

        min_balance = round(min_balance, 2)
        safe_to_spend = round(min_balance - buffer, 2)

        if safe_to_spend <= 0:
            status = "critical"
        elif safe_to_spend < buffer:
            status = "caution"
        else:
            status = "healthy"

        has_data = conn.execute("SELECT COUNT(*) as cnt FROM accounts").fetchone()["cnt"] > 0

        return {
            "starting_balance": starting_balance,
            "pending_outflows": round(pending_outflows, 2),
            "projection_days": projection_days,
            "buffer_amount": buffer,
            "upcoming_income": round(total_upcoming_income, 2),
            "upcoming_expenses": round(total_upcoming_expenses, 2),
            "min_projected_balance": min_balance,
            "min_balance_date": min_balance_date,
            "safe_to_spend": safe_to_spend,
            "status": status,
            "upcoming_items": upcoming_items,
            "daily_projections": daily_projections,
            "has_data": has_data,
        }
    finally:
        conn.close()
