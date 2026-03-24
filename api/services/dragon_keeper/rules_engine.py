"""Rules engine — tier 1 of the categorization pipeline."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    get_uncategorized_transactions,
    get_categorization_rules,
    apply_rule_to_transaction,
    mark_pending_review,
    get_manual_review_payees,
)

logger = logging.getLogger("dragon_keeper.rules_engine")


def _matches_rule(transaction: dict, rule: dict) -> bool:
    payee = (transaction.get("payee_name") or "").lower()
    pattern = rule["payee_pattern"].lower()

    if rule["match_type"] == "exact":
        if payee != pattern:
            return False
    elif rule["match_type"] == "contains":
        if pattern not in payee:
            return False
    elif rule["match_type"] == "starts_with":
        if not payee.startswith(pattern):
            return False
    else:
        return False

    amount = abs(transaction.get("amount", 0))
    if rule.get("min_amount") is not None and amount < rule["min_amount"]:
        return False
    if rule.get("max_amount") is not None and amount > rule["max_amount"]:
        return False

    return True


def _get_pending_for_reprocess(conn) -> list[dict]:
    """Get pending_review transactions that could benefit from new rules."""
    rows = conn.execute("""
        SELECT id, account_id, date, amount, payee_id, payee_name, memo,
               category_id, categorization_status
        FROM transactions
        WHERE categorization_status = 'pending_review'
        AND deleted = 0
    """).fetchall()
    return [dict(r) for r in rows]


def run_rules_engine(reprocess: bool = False) -> dict:
    """Run rules engine on uncategorized transactions.
    If reprocess=True, also re-check pending_review items against rules."""
    conn = get_db()
    try:
        transactions = get_uncategorized_transactions(conn)
        if reprocess:
            transactions += _get_pending_for_reprocess(conn)
        seen = set()
        transactions = [t for t in transactions if t["id"] not in seen and not seen.add(t["id"])]
        rules = get_categorization_rules(conn)
        manual_payees = set(get_manual_review_payees(conn))

        matched = 0
        unmatched = 0

        for txn in transactions:
            payee_name = txn.get("payee_name") or ""
            if payee_name in manual_payees:
                mark_pending_review(conn, txn["id"])
                unmatched += 1
                continue

            rule_found = False
            for rule in rules:
                if _matches_rule(txn, rule):
                    apply_rule_to_transaction(conn, txn["id"], rule["category_id"], rule["id"])
                    matched += 1
                    rule_found = True
                    break

            if not rule_found:
                mark_pending_review(conn, txn["id"])
                unmatched += 1

        conn.commit()
        logger.info("Rules engine: %d matched, %d unmatched", matched, unmatched)
        return {
            "matched": matched,
            "unmatched": unmatched,
            "total_processed": matched + unmatched,
            "rules_count": len(rules),
        }
    finally:
        conn.close()
