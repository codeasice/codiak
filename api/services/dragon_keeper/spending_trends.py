"""Spending trends service — reshapes per-category-period data for sparklines."""
import logging
from collections import defaultdict
from api.models.dragon_keeper.db import get_db, get_spending_by_category_periods

logger = logging.getLogger("dragon_keeper.spending_trends")

TOP_N = 8


def get_spending_trends() -> list[dict]:
    conn = get_db()
    try:
        rows = get_spending_by_category_periods(conn, periods=8)
    finally:
        conn.close()

    if not rows:
        return []

    by_cat: dict[str, dict] = defaultdict(lambda: {
        "category_id": "",
        "category_name": "",
        "group_name": "",
        "periods": [],
        "grand_total": 0.0,
    })

    for r in rows:
        cid = r["category_id"]
        entry = by_cat[cid]
        entry["category_id"] = cid
        entry["category_name"] = r["category_name"]
        entry["group_name"] = r["group_name"]
        entry["periods"].append({
            "period_start": r["period_start"],
            "total": round(r["total"], 2),
        })
        entry["grand_total"] += r["total"]

    results = list(by_cat.values())
    for item in results:
        item["grand_total"] = round(item["grand_total"], 2)
        item["periods"].sort(key=lambda p: p["period_start"])

        periods = item["periods"]
        if len(periods) >= 2:
            prev = periods[-2]["total"]
            curr = periods[-1]["total"]
            if prev > 0:
                item["delta_pct"] = round((curr - prev) / prev * 100, 1)
            else:
                item["delta_pct"] = 0.0 if curr == 0 else 100.0
        else:
            item["delta_pct"] = 0.0

    results.sort(key=lambda c: c["grand_total"], reverse=True)
    return results[:TOP_N]
