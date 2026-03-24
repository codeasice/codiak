"""Recurring transaction detection — identifies subscriptions, bills, and paychecks from history."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, stdev
from api.models.dragon_keeper.db import get_db, _now_utc

logger = logging.getLogger("dragon_keeper.recurring_detection")

CADENCE_CONFIG = {
    "biweekly": {"range": (12, 16), "min_occurrences": 4},
    "monthly":  {"range": (25, 35), "min_occurrences": 3},
    "annual":   {"range": (350, 380), "min_occurrences": 2},
}
AMOUNT_TOLERANCE = 0.15


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
        existing_payees = {r["payee_name"].lower() for r in existing}

        detected = []
        for payee, txns in by_payee.items():
            result = _analyze_payee(payee, txns)
            if result:
                detected.append(result)

        new_count = 0
        updated_count = 0
        items = []

        for item in detected:
            if item["payee_name"].lower() in existing_payees:
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

    for cadence in ("biweekly", "monthly", "annual"):
        cfg = CADENCE_CONFIG[cadence]
        if len(dates) >= cfg["min_occurrences"]:
            result = _check_cadence(dates, amounts, cadence)
            if result:
                return {**result, "payee_name": payee}

    return None


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
    avg_amount = mean(abs(a) for a in amounts[-sample_size:])
    if len(amounts) >= 3:
        recent_amounts = [abs(a) for a in amounts[-sample_size:]]
        if avg_amount > 0:
            amount_cv = stdev(recent_amounts) / avg_amount if len(recent_amounts) > 1 else 0
            if amount_cv > AMOUNT_TOLERANCE * 2:
                return None

    is_income = mean(amounts[-sample_size:]) > 0
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
        "next_expected_date": next_date.strftime("%Y-%m-%d"),
        "last_seen_date": last_date.strftime("%Y-%m-%d"),
        "avg_amount": round(avg_amount, 2),
        "occurrence_count": len(dates),
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


def _update_existing(conn, item: dict):
    """Update an existing recurring item with fresh detection data."""
    conn.execute("""
        UPDATE recurring_items
        SET avg_amount = ?, occurrence_count = ?,
            last_seen_date = ?, next_expected_date = ?, updated_at = ?
        WHERE LOWER(payee_name) = LOWER(?)
    """, (
        item["avg_amount"], item["occurrence_count"],
        item["last_seen_date"], item["next_expected_date"],
        _now_utc(), item["payee_name"],
    ))


def _insert_new(conn, item: dict):
    """Insert a newly detected recurring item."""
    now = _now_utc()
    conn.execute("""
        INSERT INTO recurring_items
            (payee_name, payee_pattern, type, cadence, expected_amount,
             expected_day, next_expected_date, confirmed, include_in_sts,
             last_seen_date, avg_amount, occurrence_count, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?, ?, ?, ?)
    """, (
        item["payee_name"], item["payee_name"], item["type"], item["cadence"],
        item["expected_amount"], item["expected_day"], item["next_expected_date"],
        item["last_seen_date"], item["avg_amount"], item["occurrence_count"],
        now, now,
    ))
