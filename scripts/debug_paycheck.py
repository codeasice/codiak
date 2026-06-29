"""Debug paycheck next-date calculation."""
from datetime import datetime, timedelta

from api.models.dragon_keeper.db import get_db
from api.services.dragon_keeper.paycheck_tracer import trace_paycheck, _estimate_next_paycheck

conn = get_db()
try:
    income_rows = conn.execute("""
        SELECT id, payee_name, cadence, expected_amount, last_seen_date,
               next_expected_date, confirmed, occurrence_count
        FROM recurring_items WHERE type = 'income'
        ORDER BY last_seen_date DESC
    """).fetchall()
    print("=== Income recurring items ===")
    for r in income_rows:
        print(dict(r))

    result = trace_paycheck()
    src = result.get("income_source")
    print("\n=== trace_paycheck default source ===")
    print(src)

    current = next((p for p in result.get("periods", []) if p.get("is_current")), None)
    print("\n=== Current period ===")
    if current:
        for k in ["period_start", "period_end", "paycheck_amount", "period_end_is_estimate"]:
            print(f"  {k}: {current[k]}")

    if src:
        payee = src["payee_name"]
        txns = conn.execute("""
            SELECT date, amount FROM transactions
            WHERE payee_name = ? AND amount > 0 AND deleted = 0
            AND transfer_account_id IS NULL
            ORDER BY date DESC LIMIT 8
        """, (payee,)).fetchall()
        print(f"\n=== Last paycheck txns for {payee!r} ===")
        for t in txns:
            print(f"  {t['date']}  ${t['amount']:,.2f}")

        if txns:
            last = txns[0]["date"]
            cadence = src["cadence"]
            est = _estimate_next_paycheck(
                dict(conn.execute("SELECT * FROM recurring_items WHERE id = ?", (src["id"],)).fetchone()),
                last,
                sorted({t["date"] for t in txns}, reverse=True),
            )
            today = datetime.now().strftime("%Y-%m-%d")
            print(f"\n=== Next date estimate ===")
            print(f"  today: {today}")
            print(f"  last paycheck: {last}")
            print(f"  cadence: {cadence}")
            print(f"  _estimate_next_paycheck: {est}")
            # correct biweekly advance
            d = datetime.strptime(last, "%Y-%m-%d")
            candidate = d + timedelta(days=14)
            while candidate.date() <= datetime.now().date():
                candidate += timedelta(days=14)
            print(f"  _next_biweekly style: {candidate.strftime('%Y-%m-%d')}")

            # intervals between recent paychecks
            dates = sorted({t["date"] for t in txns}, reverse=True)
            if len(dates) >= 2:
                print("\n=== Intervals between recent paychecks (days) ===")
                sorted_asc = sorted(dates)
                for i in range(1, len(sorted_asc)):
                    d1 = datetime.strptime(sorted_asc[i-1], "%Y-%m-%d")
                    d2 = datetime.strptime(sorted_asc[i], "%Y-%m-%d")
                    print(f"  {sorted_asc[i-1]} -> {sorted_asc[i]}: {(d2-d1).days}d")
finally:
    conn.close()
