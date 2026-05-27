"""Paycheck Tracer — shows where each paycheck goes by category."""
import calendar
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from api.models.dragon_keeper.db import get_db

logger = logging.getLogger("dragon_keeper.paycheck_tracer")


def get_current_period_remaining() -> dict:
    """Return spent/remaining for the active pay period (used by dashboard card)."""
    result = trace_paycheck()
    current = next((p for p in result.get("periods", []) if p.get("is_current")), None)
    if not current:
        return {"total": 0.0, "spent": 0.0, "paycheck_amount": 0.0, "period_start": None, "period_end": None}
    return {
        "total": current["total_saved"],
        "spent": current["total_spent"],
        "paycheck_amount": current["paycheck_amount"],
        "period_start": current["period_start"],
        "period_end": current["period_end"],
    }


def get_income_sources() -> list[dict]:
    """Return all detected recurring income items, ordered by most recently seen."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, payee_name, cadence, expected_amount, occurrence_count,
                   last_seen_date, confirmed
            FROM recurring_items
            WHERE type = 'income'
            ORDER BY last_seen_date DESC, occurrence_count DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def trace_paycheck(income_item_id: int | None = None, num_periods: int = 6, account_id: str | None = None) -> dict:
    """Trace where paychecks went over recent pay periods.

    Returns:
        income_source, periods (list of pay period breakdowns),
        category_averages (average % per category across all periods)
    """
    conn = get_db()
    try:
        if income_item_id:
            source = conn.execute(
                "SELECT * FROM recurring_items WHERE id = ? AND type = 'income'",
                (income_item_id,),
            ).fetchone()
        else:
            source = conn.execute("""
                SELECT * FROM recurring_items
                WHERE type = 'income'
                ORDER BY last_seen_date DESC, occurrence_count DESC
                LIMIT 1
            """).fetchone()

        if not source:
            return {"income_source": None, "periods": [], "category_averages": []}

        source_dict = dict(source)
        payee = source_dict["payee_name"]

        paycheck_rows = conn.execute("""
            SELECT date, amount FROM transactions
            WHERE payee_name = ? AND amount > 0 AND deleted = 0
            AND transfer_account_id IS NULL
            AND (? IS NULL OR account_id = ?)
            ORDER BY date DESC
        """, (payee, account_id, account_id)).fetchall()

        if len(paycheck_rows) < 2:
            return {
                "income_source": _format_source(source_dict),
                "periods": [],
                "category_averages": [],
            }

        # Deduplicate same-day paychecks (sum them)
        by_date: dict[str, float] = {}
        for r in paycheck_rows:
            by_date[r["date"]] = by_date.get(r["date"], 0) + r["amount"]

        paycheck_dates = sorted(by_date.keys(), reverse=True)

        periods = []
        # Each period: [paycheck_date, next_paycheck_date)
        # We need num_periods + 1 dates to form num_periods windows
        dates_needed = min(num_periods + 1, len(paycheck_dates))

        for i in range(dates_needed - 1):
            period_start = paycheck_dates[i + 1]
            period_end = paycheck_dates[i]
            paycheck_amount = by_date[period_start]

            breakdown = _get_period_spending(conn, period_start, period_end, account_id)

            total_spent = sum(c["amount"] for c in breakdown)
            total_saved = paycheck_amount - total_spent

            periods.append({
                "period_start": period_start,
                "period_end": period_end,
                "paycheck_amount": round(paycheck_amount, 2),
                "total_spent": round(total_spent, 2),
                "total_saved": round(total_saved, 2),
                "save_rate": round((total_saved / paycheck_amount * 100) if paycheck_amount else 0, 1),
                "categories": breakdown,
                "is_current": False,
                "period_end_is_estimate": False,
            })

        # Reverse to chronological order
        periods.reverse()

        # Append the current active period (from last paycheck to estimated next)
        today = datetime.now().strftime("%Y-%m-%d")
        last_paycheck = paycheck_dates[0]
        if last_paycheck <= today:
            next_estimated = _estimate_next_date(last_paycheck, source_dict["cadence"])
            current_breakdown = _get_period_spending(conn, last_paycheck, today, account_id)
            current_spent = sum(c["amount"] for c in current_breakdown)
            current_amount = by_date[last_paycheck]
            periods.append({
                "period_start": last_paycheck,
                "period_end": next_estimated,
                "paycheck_amount": round(current_amount, 2),
                "total_spent": round(current_spent, 2),
                "total_saved": round(current_amount - current_spent, 2),
                "save_rate": round(((current_amount - current_spent) / current_amount * 100) if current_amount else 0, 1),
                "categories": current_breakdown,
                "is_current": True,
                "period_end_is_estimate": True,
            })

        category_averages = _compute_averages(periods)

        return {
            "income_source": _format_source(source_dict),
            "periods": periods,
            "category_averages": category_averages,
        }
    finally:
        conn.close()


def _get_period_spending(conn, start_date: str, end_date: str, account_id: str | None = None) -> list[dict]:
    """Get spending breakdown by category for a pay period."""
    rows = conn.execute("""
        SELECT
            COALESCE(category_name, 'Uncategorized') as category,
            SUM(ABS(amount)) as total,
            COUNT(*) as txn_count
        FROM transactions
        WHERE date >= ? AND date < ?
        AND amount < 0
        AND deleted = 0
        AND transfer_account_id IS NULL
        AND (? IS NULL OR account_id = ?)
        GROUP BY COALESCE(category_name, 'Uncategorized')
        ORDER BY total DESC
    """, (start_date, end_date, account_id, account_id)).fetchall()

    return [
        {
            "category": r["category"],
            "amount": round(r["total"], 2),
            "transaction_count": r["txn_count"],
        }
        for r in rows
    ]


def _estimate_next_date(date_str: str, cadence: str) -> str:
    """Estimate the next paycheck date based on cadence."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    if cadence == "biweekly":
        next_d = d + timedelta(days=14)
    elif cadence == "monthly":
        month = d.month % 12 + 1
        year = d.year + (1 if d.month == 12 else 0)
        day = min(d.day, calendar.monthrange(year, month)[1])
        next_d = d.replace(year=year, month=month, day=day)
    else:
        next_d = d.replace(year=d.year + 1)
    return next_d.strftime("%Y-%m-%d")


def _format_source(source: dict) -> dict:
    return {
        "id": source["id"],
        "payee_name": source["payee_name"],
        "cadence": source["cadence"],
        "expected_amount": source["expected_amount"],
        "occurrence_count": source["occurrence_count"],
    }


def _compute_averages(periods: list[dict]) -> list[dict]:
    """Compute average spend per category across all complete (non-current) periods."""
    complete = [p for p in periods if not p["is_current"]]
    if not complete:
        return []

    category_totals: dict[str, list[float]] = defaultdict(list)
    avg_paycheck = sum(p["paycheck_amount"] for p in complete) / len(complete)

    for p in complete:
        cats_in_period = set()
        for c in p["categories"]:
            category_totals[c["category"]].append(c["amount"])
            cats_in_period.add(c["category"])
        for cat in category_totals:
            if cat not in cats_in_period:
                category_totals[cat].append(0)

    averages = []
    for cat, amounts in category_totals.items():
        avg = sum(amounts) / len(amounts)
        pct = (avg / avg_paycheck * 100) if avg_paycheck else 0
        averages.append({
            "category": cat,
            "avg_amount": round(avg, 2),
            "avg_percent": round(pct, 1),
            "period_count": len(amounts),
        })

    averages.sort(key=lambda x: x["avg_amount"], reverse=True)
    return averages
