"""Budget service — all categories with 52-week weekly spend data, averages, and targets."""
import logging
from collections import defaultdict
from api.models.dragon_keeper.db import get_db, get_setting, set_setting, _now_utc
from api.services.dragon_keeper.paycheck_tracer import get_current_period_remaining

logger = logging.getLogger("dragon_keeper.budget")

PERIODS = 52
INCOME_SETTING_KEY = "budget_per_period_income"


def _get_cancelled_by_category(conn) -> dict[str, list[str]]:
    rows = conn.execute("""
        SELECT ri.payee_name, t.category_id, COUNT(*) as cnt
        FROM recurring_items ri
        JOIN transactions t ON LOWER(t.payee_name) = LOWER(ri.payee_name)
        WHERE ri.status = 'cancelled' AND t.deleted = 0 AND t.category_id IS NOT NULL
        GROUP BY ri.payee_name, t.category_id
        ORDER BY ri.payee_name, cnt DESC
    """).fetchall()

    seen_payees: set[str] = set()
    by_cat: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        payee = r["payee_name"]
        if payee not in seen_payees:
            seen_payees.add(payee)
            by_cat[r["category_id"]].append(payee)
    return by_cat


def _get_all_categories(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT c.id as category_id, c.name as category_name, cg.name as group_name
        FROM categories c
        JOIN category_groups cg ON c.category_group_id = cg.id
        WHERE c.hidden = 0 AND cg.hidden = 0
        ORDER BY cg.name, c.name
    """).fetchall()
    return [dict(r) for r in rows]


def _get_spending_periods(conn, periods: int) -> list[dict]:
    rows = conn.execute("""
        SELECT c.id as category_id,
               date(t.date, 'weekday 0', '-6 days') as period_start,
               SUM(ABS(t.amount)) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        JOIN category_groups cg ON c.category_group_id = cg.id
        WHERE t.deleted = 0 AND t.transfer_account_id IS NULL
        AND t.amount < 0
        AND t.date >= date('now', ?)
        AND c.hidden = 0 AND cg.hidden = 0
        GROUP BY c.id, period_start
        ORDER BY c.id, period_start
    """, (f"-{periods * 7} days",)).fetchall()
    return [dict(r) for r in rows]


def _get_targets(conn) -> dict[str, float]:
    rows = conn.execute("SELECT category_id, amount FROM budget_targets").fetchall()
    return {r["category_id"]: r["amount"] for r in rows}


def _default_income() -> float:
    try:
        paycheck = get_current_period_remaining()
        amount = paycheck.get("paycheck_amount", 0.0) or 0.0
        return round(amount / 2, 2)
    except Exception:
        return 0.0


def get_per_period_income() -> float:
    conn = get_db()
    try:
        stored = get_setting(conn, INCOME_SETTING_KEY)
        if stored is not None:
            return float(stored)
        return _default_income()
    finally:
        conn.close()


def set_per_period_income(amount: float) -> None:
    conn = get_db()
    try:
        set_setting(conn, INCOME_SETTING_KEY, str(round(amount, 2)))
        conn.commit()
    finally:
        conn.close()


def upsert_budget_target(category_id: str, amount: float | None) -> None:
    conn = get_db()
    try:
        if amount is None:
            conn.execute("DELETE FROM budget_targets WHERE category_id = ?", (category_id,))
        else:
            conn.execute("""
                INSERT INTO budget_targets (category_id, amount, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(category_id) DO UPDATE SET amount = excluded.amount, updated_at = excluded.updated_at
            """, (category_id, round(amount, 2), _now_utc()))
        conn.commit()
    finally:
        conn.close()


def get_budget() -> dict:
    conn = get_db()
    try:
        all_cats = _get_all_categories(conn)
        spend_rows = _get_spending_periods(conn, PERIODS)
        cancelled_by_cat = _get_cancelled_by_category(conn)
        targets = _get_targets(conn)
        stored_income = get_setting(conn, INCOME_SETTING_KEY)
    finally:
        conn.close()

    per_period_income = float(stored_income) if stored_income is not None else _default_income()

    all_periods = sorted({r["period_start"] for r in spend_rows})

    spend_by_cat: dict[str, dict[str, float]] = defaultdict(dict)
    for r in spend_rows:
        spend_by_cat[r["category_id"]][r["period_start"]] = round(r["total"], 2)

    categories = []
    for cat in all_cats:
        cid = cat["category_id"]
        existing = spend_by_cat.get(cid, {})
        periods_list = [
            {"period_start": ps, "total": round(existing.get(ps, 0.0), 2)}
            for ps in all_periods
        ]
        grand_total = round(sum(p["total"] for p in periods_list), 2)
        active_weeks = sum(1 for p in periods_list if p["total"] > 0)
        weekly_avg = round(grand_total / PERIODS, 2) if grand_total > 0 else 0.0

        if len(periods_list) >= 2:
            prev = periods_list[-2]["total"]
            curr = periods_list[-1]["total"]
            delta_pct = round((curr - prev) / prev * 100, 1) if prev > 0 else (0.0 if curr == 0 else 100.0)
        else:
            delta_pct = 0.0

        categories.append({
            "category_id": cid,
            "category_name": cat["category_name"],
            "group_name": cat["group_name"],
            "periods": periods_list,
            "grand_total": grand_total,
            "weekly_avg": weekly_avg,
            "active_weeks": active_weeks,
            "delta_pct": delta_pct,
            "has_activity": active_weeks > 0,
            "cancelled_subscriptions": cancelled_by_cat.get(cid, []),
            "budget_target": targets.get(cid),
        })

    return {
        "categories": categories,
        "per_period_income": per_period_income,
    }
