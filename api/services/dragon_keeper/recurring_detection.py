"""Recurring transaction detection — identifies subscriptions, bills, and paychecks from history."""
import calendar
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, stdev
from api.models.dragon_keeper.db import get_db, _now_utc
from api.services.dragon_keeper.recurring_linking import (
    get_all_alias_payees_lower,
    recompute_recurring_item,
)

logger = logging.getLogger("dragon_keeper.recurring_detection")

CADENCE_CONFIG = {
    "biweekly": {"range": (12, 16), "min_occurrences": 4},
    "monthly":  {"range": (25, 35), "min_occurrences": 3},
    "annual":   {"range": (350, 380), "min_occurrences": 2},
}
SEMI_MONTHLY_MIN_MONTHS = 3
SEMI_MONTHLY_DAY_STDEV_MAX = 4
SEMI_MONTHLY_MIN_DAY_GAP = 8
AMOUNT_TOLERANCE = 0.15
SUBSCRIPTION_CV_THRESHOLD = 0.08  # ≤8% coefficient of variation → classify as subscription


def detect_recurring_transactions() -> dict:
    """Scan transaction history and detect recurring patterns.
    Returns {detected: int, new: int, updated: int, items: [...]}"""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT payee_name, date, amount
            FROM transactions
            WHERE deleted = 0 AND transfer_account_id IS NULL
            AND payee_name IS NOT NULL AND payee_name != ''
            ORDER BY payee_name, date
        """).fetchall()

        by_payee: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            by_payee[r["payee_name"]].append({
                "date": r["date"],
                "amount": r["amount"],
            })

        existing = _get_existing_recurring(conn)
        existing_by_payee = {r["payee_name"].lower(): r for r in existing}
        alias_to_canonical = get_all_alias_payees_lower(conn)
        existing_payees = set(existing_by_payee.keys()) | set(alias_to_canonical.keys())
        cancelled_payees = _get_cancelled_payees(conn)

        detected = []
        for payee, txns in by_payee.items():
            if payee.lower() in cancelled_payees:
                continue
            result = _analyze_payee(payee, txns)
            if result:
                detected.append(result)

        new_count = 0
        updated_count = 0
        items = []

        for item in detected:
            payee_lower = item["payee_name"].lower()
            if payee_lower in alias_to_canonical:
                recompute_recurring_item(conn, alias_to_canonical[payee_lower])
                updated_count += 1
            elif payee_lower in existing_by_payee:
                _update_existing(conn, item)
                updated_count += 1
            else:
                _insert_new(conn, item)
                new_count += 1
            items.append(item)

        conn.commit()

        return {
            "detected": len(detected),
            "new": new_count,
            "updated": updated_count,
            "items": items,
        }
    finally:
        conn.close()


def _analyze_payee(payee: str, txns: list[dict]) -> dict | None:
    """Analyze a single payee's transactions for recurring patterns."""
    min_needed = min(c["min_occurrences"] for c in CADENCE_CONFIG.values())
    if len(txns) < min_needed:
        return None

    all_dates = sorted(datetime.strptime(t["date"], "%Y-%m-%d") for t in txns)
    amounts = [t["amount"] for t in txns]

    # Deduplicate same-day transactions (keep one per day for interval analysis)
    seen_days: set[str] = set()
    dates: list[datetime] = []
    for d in all_dates:
        key = d.strftime("%Y-%m-%d")
        if key not in seen_days:
            seen_days.add(key)
            dates.append(d)

    if len(dates) >= SEMI_MONTHLY_MIN_MONTHS * 2:
        result = _check_semi_monthly(dates, amounts)
        if result:
            return {**result, "payee_name": payee}

    for cadence in ("biweekly", "monthly", "annual"):
        cfg = CADENCE_CONFIG[cadence]
        if len(dates) >= cfg["min_occurrences"]:
            result = _check_cadence(dates, amounts, cadence)
            if result:
                return {**result, "payee_name": payee}

    return None


def _amount_stats(amounts: list[float], sample_size: int) -> tuple[float, bool, bool] | None:
    """Return (avg_amount, is_income, is_subscription) or None if amounts too variable."""
    recent = [abs(a) for a in amounts[-sample_size:]]
    avg_amount = mean(recent)
    if len(amounts) >= 3 and avg_amount > 0:
        amount_cv = stdev(recent) / avg_amount if len(recent) > 1 else 0
        if amount_cv > AMOUNT_TOLERANCE * 2:
            return None
    is_income = mean(amounts[-sample_size:]) > 0
    amount_cv = (stdev(recent) / mean(recent)) if len(recent) > 1 and mean(recent) > 0 else 0
    is_subscription = not is_income and amount_cv <= SUBSCRIPTION_CV_THRESHOLD
    return avg_amount, is_income, is_subscription


def _check_semi_monthly(dates: list[datetime], amounts: list[float]) -> dict | None:
    """Detect two stable charge days per month (e.g. 18th and 29th)."""
    by_month: dict[tuple[int, int], list[int]] = defaultdict(list)
    for d in dates:
        by_month[(d.year, d.month)].append(d.day)

    month_pairs: list[tuple[int, int]] = []
    for days in by_month.values():
        if len(days) < 2:
            continue
        sorted_days = sorted(days)
        month_pairs.append((sorted_days[0], sorted_days[1]))

    if len(month_pairs) < SEMI_MONTHLY_MIN_MONTHS:
        return None

    early_days = [pair[0] for pair in month_pairs]
    late_days = [pair[1] for pair in month_pairs]
    if len(early_days) > 1 and stdev(early_days) > SEMI_MONTHLY_DAY_STDEV_MAX:
        return None
    if len(late_days) > 1 and stdev(late_days) > SEMI_MONTHLY_DAY_STDEV_MAX:
        return None

    day_early = round(mean(early_days))
    day_late = round(mean(late_days))
    if day_late - day_early < SEMI_MONTHLY_MIN_DAY_GAP:
        return None

    stats = _amount_stats(amounts, min(12, len(amounts)))
    if not stats:
        return None
    avg_amount, is_income, is_subscription = stats

    last_date = dates[-1]
    next_date = _next_semi_monthly(day_early, day_late)

    return {
        "type": "income" if is_income else "expense",
        "cadence": "semi_monthly",
        "expected_amount": round(avg_amount, 2),
        "expected_day": day_early,
        "expected_day_2": day_late,
        "next_expected_date": next_date.strftime("%Y-%m-%d"),
        "last_seen_date": last_date.strftime("%Y-%m-%d"),
        "avg_amount": round(avg_amount, 2),
        "occurrence_count": len(dates),
        "is_subscription": is_subscription,
    }


def _check_cadence(dates: list[datetime], amounts: list[float], cadence: str) -> dict | None:
    """Check if transactions follow a specific cadence."""
    cfg = CADENCE_CONFIG[cadence]
    min_interval, max_interval = cfg["range"]
    min_occurrences = cfg["min_occurrences"]

    intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
    matching = [d for d in intervals if min_interval <= d <= max_interval]

    if len(matching) < min_occurrences - 1:
        return None

    if len(matching) < len(intervals) * 0.5:
        return None

    sample_size = 12 if cadence == "biweekly" else 6
    stats = _amount_stats(amounts, sample_size)
    if not stats:
        return None
    avg_amount, is_income, is_subscription = stats

    last_date = dates[-1]
    expected_day = last_date.day

    if cadence == "biweekly":
        next_date = _next_biweekly(last_date)
    elif cadence == "monthly":
        next_date = _next_monthly(last_date, expected_day)
    else:
        next_date = _next_annual(last_date)

    return {
        "type": "income" if is_income else "expense",
        "cadence": cadence,
        "expected_amount": round(avg_amount, 2),
        "expected_day": expected_day,
        "expected_day_2": None,
        "next_expected_date": next_date.strftime("%Y-%m-%d"),
        "last_seen_date": last_date.strftime("%Y-%m-%d"),
        "avg_amount": round(avg_amount, 2),
        "occurrence_count": len(dates),
        "is_subscription": is_subscription,
    }


def _next_biweekly(last_date: datetime) -> datetime:
    """Calculate the next biweekly occurrence after today."""
    today = datetime.now()
    candidate = last_date + timedelta(days=14)
    while candidate.date() <= today.date():
        candidate += timedelta(days=14)
    return candidate


def _next_monthly(last_date: datetime, day: int) -> datetime:
    """Calculate the next monthly occurrence after today."""
    today = datetime.now()
    year, month = today.year, today.month

    try:
        candidate = today.replace(day=min(day, 28))
    except ValueError:
        candidate = today.replace(day=28)

    if candidate <= today:
        month += 1
        if month > 12:
            month = 1
            year += 1
        try:
            candidate = candidate.replace(year=year, month=month, day=min(day, 28))
        except ValueError:
            candidate = candidate.replace(year=year, month=month, day=28)

    return candidate


def _day_in_month(year: int, month: int, day: int) -> datetime:
    last_day = calendar.monthrange(year, month)[1]
    return datetime(year, month, min(day, last_day))


def _next_semi_monthly(day_early: int, day_late: int) -> datetime:
    """Next charge date after today for a semi-monthly pattern."""
    today = datetime.now().date()
    y, m = today.year, today.month
    candidates: list[datetime] = []
    for offset in range(0, 4):
        month = m + offset
        year = y + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        candidates.append(_day_in_month(year, month, day_early))
        candidates.append(_day_in_month(year, month, day_late))
    future = sorted(d for d in candidates if d.date() > today)
    return future[0] if future else _day_in_month(y, m, day_late)


def _next_annual(last_date: datetime) -> datetime:
    """Calculate the next annual occurrence after today."""
    today = datetime.now()
    candidate = last_date.replace(year=today.year)
    if candidate.date() <= today.date():
        candidate = candidate.replace(year=today.year + 1)
    return candidate


def _get_existing_recurring(conn) -> list[dict]:
    rows = conn.execute("SELECT * FROM recurring_items").fetchall()
    return [dict(r) for r in rows]


def _get_cancelled_payees(conn) -> set[str]:
    rows = conn.execute(
        "SELECT id, payee_name FROM recurring_items WHERE status IN ('cancelled', 'archived')"
    ).fetchall()
    result = {r["payee_name"].lower() for r in rows}
    for row in rows:
        aliases = conn.execute(
            "SELECT payee_name FROM recurring_item_aliases WHERE recurring_id = ?",
            (row["id"],),
        ).fetchall()
        result.update(a["payee_name"].lower() for a in aliases)
    return result


def _update_existing(conn, item: dict):
    """Update an existing recurring item with fresh detection data."""
    conn.execute("""
        UPDATE recurring_items
        SET avg_amount = ?, occurrence_count = ?,
            last_seen_date = ?, next_expected_date = ?,
            expected_amount = ?, expected_day = ?, expected_day_2 = ?,
            cadence = ?, updated_at = ?
        WHERE LOWER(payee_name) = LOWER(?)
    """, (
        item["avg_amount"], item["occurrence_count"],
        item["last_seen_date"], item["next_expected_date"],
        item["expected_amount"], item["expected_day"], item.get("expected_day_2"),
        item["cadence"],
        _now_utc(), item["payee_name"],
    ))


def _insert_new(conn, item: dict):
    """Insert a newly detected recurring item."""
    now = _now_utc()
    conn.execute("""
        INSERT INTO recurring_items
            (payee_name, payee_pattern, type, cadence, expected_amount,
             expected_day, expected_day_2, next_expected_date, confirmed, include_in_sts,
             last_seen_date, avg_amount, occurrence_count, is_subscription,
             status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?, ?, ?, 'active', ?, ?)
    """, (
        item["payee_name"], item["payee_name"], item["type"], item["cadence"],
        item["expected_amount"], item["expected_day"], item.get("expected_day_2"),
        item["next_expected_date"],
        item["last_seen_date"], item["avg_amount"], item["occurrence_count"],
        1 if item.get("is_subscription") else 0,
        now, now,
    ))
