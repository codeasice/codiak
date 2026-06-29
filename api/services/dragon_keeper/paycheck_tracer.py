"""Paycheck Tracer — shows where each paycheck goes by category."""
import calendar
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from api.models.dragon_keeper.db import get_db
from api.services.dragon_keeper.recurring_linking import get_payee_names_for_item

logger = logging.getLogger("dragon_keeper.paycheck_tracer")

# Payee name fragments that indicate internal transfers, not wages
_TRANSFER_NAME_MARKERS = ("deposit from", "transfer from", "transfer to", "share 00")


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
    """Return all detected recurring income items, best paycheck candidates first."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT id, payee_name, cadence, expected_amount, occurrence_count,
                   last_seen_date, confirmed
            FROM recurring_items
            WHERE type = 'income'
            ORDER BY confirmed DESC, expected_amount DESC, occurrence_count DESC,
                     last_seen_date DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _looks_like_transfer(payee_name: str) -> bool:
    lower = payee_name.lower()
    return any(marker in lower for marker in _TRANSFER_NAME_MARKERS)


def _get_paycheck_deposits(conn, payee_names: list[str]) -> list[dict]:
    """Return positive deposit transactions for one or more linked payee names."""
    if not payee_names:
        return []
    lower_names = list({name.lower() for name in payee_names})
    placeholders = ",".join("?" * len(lower_names))
    return conn.execute(f"""
        SELECT date, amount FROM transactions
        WHERE LOWER(payee_name) IN ({placeholders})
        AND amount > 0 AND deleted = 0
        AND transfer_account_id IS NULL
        ORDER BY date DESC
    """, lower_names).fetchall()


def _select_default_income_source(conn) -> dict | None:
    """Pick the income item most likely to be the primary paycheck."""
    rows = conn.execute("""
        SELECT * FROM recurring_items
        WHERE type = 'income'
        ORDER BY confirmed DESC, expected_amount DESC, occurrence_count DESC,
                 last_seen_date DESC
    """).fetchall()
    if not rows:
        return None

    best: dict | None = None
    best_score = -1
    for row in rows:
        item = dict(row)
        payee_names = get_payee_names_for_item(conn, item["id"])
        deposits = _get_paycheck_deposits(conn, payee_names)
        if len(deposits) < 2:
            continue
        score = item.get("expected_amount", 0) * item.get("occurrence_count", 1)
        if item.get("confirmed"):
            score += 10_000
        if _looks_like_transfer(item["payee_name"]):
            score -= 50_000
        if score > best_score:
            best_score = score
            best = item

    return best or dict(rows[0])


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
            source = _select_default_income_source(conn)

        if not source:
            return {"income_source": None, "periods": [], "category_averages": []}

        source_dict = dict(source)
        payee_names = get_payee_names_for_item(conn, source_dict["id"])

        paycheck_rows = _get_paycheck_deposits(conn, payee_names)

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
                "is_projected": False,
                "period_end_is_estimate": False,
            })

        # Reverse to chronological order
        periods.reverse()

        # Append the current active period (from last paycheck to estimated next)
        today = datetime.now().strftime("%Y-%m-%d")
        last_paycheck = paycheck_dates[0]
        if last_paycheck <= today:
            next_estimated = _estimate_next_paycheck(source_dict, last_paycheck, paycheck_dates)
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
                "is_projected": False,
                "period_end_is_estimate": True,
            })

            projected_start = next_estimated
            projected_end = _estimate_next_paycheck(source_dict, projected_start, paycheck_dates)
            recent_amounts = [by_date[d] for d in paycheck_dates[:3]]
            projected_amount = source_dict.get("expected_amount") or (
                round(sum(recent_amounts) / len(recent_amounts), 2) if recent_amounts else 0
            )
            periods.append({
                "period_start": projected_start,
                "period_end": projected_end,
                "paycheck_amount": round(projected_amount, 2),
                "total_spent": 0,
                "total_saved": 0,
                "save_rate": 0,
                "categories": [],
                "is_current": False,
                "is_projected": True,
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


def _estimate_next_paycheck(source: dict, last_paycheck: str, paycheck_dates: list[str]) -> str:
    """Estimate the next paycheck date using deposit history, then recurring metadata."""
    d = datetime.strptime(last_paycheck, "%Y-%m-%d")
    today = datetime.now().date()

    inferred = _infer_next_from_paycheck_history(d, paycheck_dates, today)
    if inferred:
        return inferred.strftime("%Y-%m-%d")

    stored = source.get("next_expected_date")
    if stored and stored > last_paycheck:
        return stored

    cadence = source.get("cadence", "biweekly")
    if cadence == "biweekly":
        next_d = _advance_biweekly(d, today)
    elif cadence == "monthly":
        next_d = _advance_monthly(d, source.get("expected_day") or d.day, today)
    elif cadence == "semi_monthly":
        day_early = source.get("expected_day") or d.day
        day_late = source.get("expected_day_2") or day_early
        next_d = _next_semi_monthly(day_early, day_late)
    elif cadence == "annual":
        next_d = _advance_annual(d, today)
    else:
        next_d = _advance_biweekly(d, today)
    return next_d.strftime("%Y-%m-%d")


def _infer_next_from_paycheck_history(
    last_paycheck: datetime, paycheck_dates: list[str], today
) -> datetime | None:
    """When deposits follow a stable interval, project the next one from history."""
    if len(paycheck_dates) < 3:
        return None
    sorted_dates = sorted(paycheck_dates)
    intervals = [
        (datetime.strptime(sorted_dates[i], "%Y-%m-%d") - datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")).days
        for i in range(1, len(sorted_dates))
    ]
    median = sorted(intervals)[len(intervals) // 2]
    if not (12 <= median <= 16 or 28 <= median <= 31):
        return None
    matching = sum(1 for i in intervals if abs(i - median) <= 2)
    if matching < len(intervals) * 0.7:
        return None
    candidate = last_paycheck + timedelta(days=median)
    while candidate.date() <= today:
        candidate += timedelta(days=median)
    return candidate


def _advance_biweekly(last_date: datetime, today) -> datetime:
    candidate = last_date + timedelta(days=14)
    while candidate.date() <= today:
        candidate += timedelta(days=14)
    return candidate


def _advance_monthly(last_date: datetime, day: int, today) -> datetime:
    year, month = last_date.year, last_date.month
    month += 1
    if month > 12:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    candidate = datetime(year, month, min(day, last_day))
    while candidate.date() <= today:
        month += 1
        if month > 12:
            month = 1
            year += 1
        last_day = calendar.monthrange(year, month)[1]
        candidate = datetime(year, month, min(day, last_day))
    return candidate


def _advance_annual(last_date: datetime, today) -> datetime:
    candidate = last_date.replace(year=today.year)
    if candidate.date() <= today:
        candidate = candidate.replace(year=candidate.year + 1)
    return candidate


def _next_semi_monthly(day_early: int, day_late: int) -> datetime:
    """Next semi-monthly occurrence after today."""
    today = datetime.now().date()
    y, m = today.year, today.month
    candidates: list[datetime] = []
    for offset in range(0, 4):
        month = m + offset
        year = y + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        for day in (day_early, day_late):
            last_day = calendar.monthrange(year, month)[1]
            candidates.append(datetime(year, month, min(day, last_day)))
    future = sorted(d for d in candidates if d.date() > today)
    return future[0] if future else datetime(y, m, min(day_late, calendar.monthrange(y, m)[1]))


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
    complete = [p for p in periods if not p["is_current"] and not p.get("is_projected")]
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
