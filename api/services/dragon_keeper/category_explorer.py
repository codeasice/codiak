"""Category Explorer service — weekly payee breakdown for a single category."""
import logging
from datetime import datetime, timedelta
from api.models.dragon_keeper.db import get_db

logger = logging.getLogger("dragon_keeper.category_explorer")


def _week_start(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")


def get_categories_with_spending() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT category_name, COUNT(*) as txn_count, SUM(ABS(amount)) as total
            FROM transactions
            WHERE amount < 0 AND deleted = 0 AND transfer_account_id IS NULL
              AND category_name IS NOT NULL
            GROUP BY category_name
            ORDER BY total DESC
        """).fetchall()
        return [{"name": r["category_name"], "total": round(r["total"], 2), "count": r["txn_count"]} for r in rows]
    finally:
        conn.close()


def get_category_explorer(category_name: str, weeks: int = 12) -> dict:
    conn = get_db()
    try:
        today = datetime.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        start_date = current_week_start - timedelta(weeks=weeks - 1)

        rows = conn.execute("""
            SELECT date, payee_name, ABS(amount) as amount
            FROM transactions
            WHERE category_name = ?
              AND amount < 0
              AND deleted = 0
              AND transfer_account_id IS NULL
              AND date >= ?
            ORDER BY date
        """, (category_name, start_date.strftime("%Y-%m-%d"))).fetchall()

        DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        week_payee: dict[str, dict[str, float]] = {}
        week_dow: dict[str, dict[str, float]] = {}
        payee_stats: dict[str, dict] = {}

        for r in rows:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
            week = _week_start(r["date"])
            dow = DOW[d.weekday()]
            payee = r["payee_name"] or "Unknown"
            amount = float(r["amount"])

            if week not in week_payee:
                week_payee[week] = {}
            week_payee[week][payee] = round(week_payee[week].get(payee, 0.0) + amount, 2)

            if week not in week_dow:
                week_dow[week] = {}
            week_dow[week][dow] = round(week_dow[week].get(dow, 0.0) + amount, 2)

            if payee not in payee_stats:
                payee_stats[payee] = {"count": 0, "total": 0.0}
            payee_stats[payee]["count"] += 1
            payee_stats[payee]["total"] += amount

        weekly_data = []
        dow_heatmap = []
        for i in range(weeks):
            ws = (start_date + timedelta(weeks=i)).strftime("%Y-%m-%d")
            entry: dict = {"week_start": ws}
            entry.update(week_payee.get(ws, {}))
            weekly_data.append(entry)

            dow_entry: dict = {"week_start": ws}
            for day in DOW:
                dow_entry[day] = round(week_dow.get(ws, {}).get(day, 0.0), 2)
            dow_heatmap.append(dow_entry)

        payee_summary = sorted(
            [
                {
                    "payee_name": payee,
                    "transaction_count": s["count"],
                    "avg_amount": round(s["total"] / s["count"], 2),
                    "total_amount": round(s["total"], 2),
                }
                for payee, s in payee_stats.items()
            ],
            key=lambda x: -x["total_amount"],
        )

        return {
            "category_name": category_name,
            "weekly_data": weekly_data,
            "dow_heatmap": dow_heatmap,
            "payee_summary": payee_summary,
            "all_payees": [p["payee_name"] for p in payee_summary],
        }
    finally:
        conn.close()
