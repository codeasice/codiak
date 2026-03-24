"""Rule preview and bulk reclassification service."""
from api.models.dragon_keeper.db import (
    get_db, preview_rule_matches, bulk_reclassify, enqueue_write_back,
)


def preview_matches(
    payee_pattern: str,
    match_type: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> dict:
    conn = get_db()
    try:
        return preview_rule_matches(conn, payee_pattern, match_type, min_amount, max_amount)
    finally:
        conn.close()


def reclassify_transactions(
    payee_pattern: str,
    match_type: str,
    category_id: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> dict:
    conn = get_db()
    try:
        count = bulk_reclassify(conn, payee_pattern, match_type, category_id, min_amount, max_amount)
        if count > 0:
            _enqueue_all_matching(conn, payee_pattern, match_type, category_id, min_amount, max_amount)
        conn.commit()
        return {"reclassified_count": count}
    finally:
        conn.close()


def _enqueue_all_matching(
    conn,
    payee_pattern: str,
    match_type: str,
    category_id: str,
    min_amount: float | None,
    max_amount: float | None,
) -> None:
    """Enqueue write-back entries for every transaction that was just reclassified."""
    if match_type == "exact":
        where = "payee_name = ?"
        params: list = [payee_pattern]
    elif match_type == "starts_with":
        where = "payee_name LIKE ?"
        params = [payee_pattern + "%"]
    else:
        where = "payee_name LIKE ?"
        params = ["%" + payee_pattern + "%"]

    amount_clauses: list[str] = []
    if min_amount is not None:
        amount_clauses.append("ABS(amount) >= ?")
        params.append(min_amount)
    if max_amount is not None:
        amount_clauses.append("ABS(amount) <= ?")
        params.append(max_amount)

    full_where = f"{where} AND deleted = 0 AND transfer_account_id IS NULL AND category_id = ?"
    params.append(category_id)
    if amount_clauses:
        full_where += " AND " + " AND ".join(amount_clauses)

    rows = conn.execute(
        f"SELECT id FROM transactions WHERE {full_where}", params
    ).fetchall()
    for row in rows:
        enqueue_write_back(conn, row["id"], category_id)
