"""Paycheck configuration — stores gross pay, deductions, and take-home from pay stub."""
from api.models.dragon_keeper.db import get_db

DEDUCTION_CATEGORIES = ['taxes', 'benefits', 'retirement', 'other']
_CONFIG_ID = 1


def get_paycheck_config() -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM paycheck_config WHERE id = ?", (_CONFIG_ID,)
        ).fetchone()
        if not row:
            return None

        items = conn.execute(
            "SELECT * FROM paycheck_deduction_items WHERE paycheck_config_id = ? ORDER BY sort_order",
            (_CONFIG_ID,)
        ).fetchall()

        deductions: dict[str, list] = {cat: [] for cat in DEDUCTION_CATEGORIES}
        for item in items:
            cat = item["category"]
            if cat in deductions:
                deductions[cat].append({
                    "id": item["id"],
                    "name": item["name"],
                    "amount": item["amount"],
                    "sort_order": item["sort_order"],
                })

        return {
            "id": row["id"],
            "gross_amount": row["gross_amount"],
            "take_home_amount": row["take_home_amount"],
            "effective_date": row["effective_date"],
            "notes": row["notes"],
            "deductions": deductions,
        }
    finally:
        conn.close()


def upsert_paycheck_config(
    gross_amount: float,
    take_home_amount: float,
    effective_date: str,
    notes: str | None,
    deduction_items: list[dict],
) -> dict:
    from api.models.dragon_keeper.db import _now_utc
    conn = get_db()
    try:
        now = _now_utc()
        existing = conn.execute(
            "SELECT id FROM paycheck_config WHERE id = ?", (_CONFIG_ID,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE paycheck_config
                SET gross_amount = ?, take_home_amount = ?, effective_date = ?,
                    notes = ?, updated_at = ?
                WHERE id = ?
            """, (gross_amount, take_home_amount, effective_date, notes, now, _CONFIG_ID))
        else:
            conn.execute("""
                INSERT INTO paycheck_config (id, gross_amount, take_home_amount, effective_date, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (_CONFIG_ID, gross_amount, take_home_amount, effective_date, notes, now, now))

        conn.execute(
            "DELETE FROM paycheck_deduction_items WHERE paycheck_config_id = ?", (_CONFIG_ID,)
        )
        for item in deduction_items:
            conn.execute("""
                INSERT INTO paycheck_deduction_items (paycheck_config_id, category, name, amount, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (_CONFIG_ID, item["category"], item["name"], item["amount"], item.get("sort_order", 0)))

        conn.commit()
        return get_paycheck_config()
    finally:
        conn.close()
