"""Chart data services — balance trends, category timelines, spending flows."""
import logging
from collections import defaultdict
from api.models.dragon_keeper.db import get_db

logger = logging.getLogger("dragon_keeper.charts")


def get_balance_history(days: int = 90) -> dict:
    """Get daily balance totals for trend chart."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT snapshot_date, checking_total, credit_total, savings_total, net_worth
            FROM balance_daily_totals
            ORDER BY snapshot_date DESC
            LIMIT ?
        """, (days,)).fetchall()

        points = [dict(r) for r in reversed(rows)]
        return {"points": points, "count": len(points)}
    finally:
        conn.close()


def get_category_timeline(category_id: str, periods: int = 12) -> dict:
    """Get monthly spending for a single category."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                strftime('%Y-%m', date) as month,
                SUM(ABS(amount)) as total,
                COUNT(*) as txn_count
            FROM transactions
            WHERE category_id = ?
            AND amount < 0 AND deleted = 0 AND transfer_account_id IS NULL
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
        """, (category_id, periods)).fetchall()

        points = [{"month": r["month"], "total": round(r["total"], 2), "txn_count": r["txn_count"]}
                  for r in reversed(rows)]

        cat_row = conn.execute(
            "SELECT name, category_group_id FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        cat_name = cat_row["name"] if cat_row else "Unknown"

        return {"category_id": category_id, "category_name": cat_name, "points": points}
    finally:
        conn.close()


def get_spending_flow(month: str | None = None, min_amount: float = 10.0,
                      max_groups: int = 15, max_categories: int = 25,
                      max_payees: int = 30) -> dict:
    """Build Group → Category → Payee spending flow data for Sankey diagram.

    Args:
        month: YYYY-MM format, or None for current month
        min_amount: minimum flow amount to include
        max_groups/categories/payees: cap node counts for readability
    """
    conn = get_db()
    try:
        if not month:
            row = conn.execute("SELECT strftime('%Y-%m', 'now') as m").fetchone()
            month = row["m"]

        date_start = f"{month}-01"
        # End of month
        parts = month.split("-")
        y, m = int(parts[0]), int(parts[1])
        if m == 12:
            date_end = f"{y + 1}-01-01"
        else:
            date_end = f"{y}-{m + 1:02d}-01"

        rows = conn.execute("""
            SELECT t.payee_name, t.amount, t.category_id,
                   COALESCE(c.name, t.category_name) as category_name,
                   c.category_group_id, cg.name as group_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE t.date >= ? AND t.date < ?
            AND t.amount < 0 AND t.deleted = 0
            AND t.transfer_account_id IS NULL
            AND t.payee_name IS NOT NULL AND t.payee_name != ''
        """, (date_start, date_end)).fetchall()

        group_totals: dict[str, float] = defaultdict(float)
        category_totals: dict[str, float] = defaultdict(float)
        payee_totals: dict[str, float] = defaultdict(float)

        # group_name -> category_name -> amount
        group_cat_flows: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # category_name -> payee_name -> amount
        cat_payee_flows: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # Track which group each category belongs to
        cat_to_group: dict[str, str] = {}

        for r in rows:
            amt = abs(r["amount"])
            payee = r["payee_name"]
            cat_name = r["category_name"] or "Uncategorized"
            grp_name = r["group_name"] or "Ungrouped"

            group_totals[grp_name] += amt
            category_totals[cat_name] += amt
            payee_totals[payee] += amt
            group_cat_flows[grp_name][cat_name] += amt
            cat_payee_flows[cat_name][payee] += amt
            cat_to_group[cat_name] = grp_name

        # Top N by total
        top_groups = sorted(group_totals.keys(), key=lambda x: group_totals[x], reverse=True)[:max_groups]
        top_categories = sorted(category_totals.keys(), key=lambda x: category_totals[x], reverse=True)[:max_categories]
        top_payees = sorted(payee_totals.keys(), key=lambda x: payee_totals[x], reverse=True)[:max_payees]

        top_categories_set = set(top_categories)
        top_payees_set = set(top_payees)

        # Build nodes
        nodes = []
        node_index: dict[str, int] = {}

        for g in top_groups:
            node_index[f"group:{g}"] = len(nodes)
            nodes.append({"id": f"group:{g}", "name": g, "column": 0, "total": round(group_totals[g], 2)})
        for c in top_categories:
            node_index[f"cat:{c}"] = len(nodes)
            nodes.append({"id": f"cat:{c}", "name": c, "column": 1, "total": round(category_totals[c], 2)})
        for p in top_payees:
            node_index[f"payee:{p}"] = len(nodes)
            nodes.append({"id": f"payee:{p}", "name": p, "column": 2, "total": round(payee_totals[p], 2)})

        # Build links
        links = []

        for grp in top_groups:
            for cat, amt in group_cat_flows[grp].items():
                if cat in top_categories_set and amt >= min_amount:
                    links.append({
                        "source": node_index[f"group:{grp}"],
                        "target": node_index[f"cat:{cat}"],
                        "value": round(amt, 2),
                    })

        for cat in top_categories:
            for payee, amt in cat_payee_flows[cat].items():
                if payee in top_payees_set and amt >= min_amount:
                    links.append({
                        "source": node_index[f"cat:{cat}"],
                        "target": node_index[f"payee:{payee}"],
                        "value": round(amt, 2),
                    })

        total_spending = sum(abs(r["amount"]) for r in rows)

        # Available months
        month_rows = conn.execute("""
            SELECT DISTINCT strftime('%Y-%m', date) as m
            FROM transactions
            WHERE amount < 0 AND deleted = 0 AND transfer_account_id IS NULL
            ORDER BY m DESC LIMIT 24
        """).fetchall()
        available_months = [r["m"] for r in month_rows]

        return {
            "month": month,
            "total_spending": round(total_spending, 2),
            "transaction_count": len(rows),
            "nodes": nodes,
            "links": links,
            "available_months": available_months,
        }
    finally:
        conn.close()
