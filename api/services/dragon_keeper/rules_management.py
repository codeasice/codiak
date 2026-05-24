"""Rules management service – CRUD for categorization rules."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    get_all_rules_with_categories,
    get_rule_by_id,
    create_rule,
    update_rule,
    delete_rule,
    enqueue_write_back,
)

logger = logging.getLogger("dragon_keeper.rules_management")


def list_rules() -> list[dict]:
    conn = get_db()
    try:
        return get_all_rules_with_categories(conn)
    finally:
        conn.close()


def create_new_rule(
    payee_pattern: str,
    match_type: str,
    category_id: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> dict:
    conn = get_db()
    try:
        new_id = create_rule(
            conn,
            payee_pattern=payee_pattern,
            match_type=match_type,
            category_id=category_id,
            min_amount=min_amount,
            max_amount=max_amount,
            confidence=1.0,
            source="manual",
        )
        conn.commit()
        rule = get_rule_by_id(conn, new_id)
        logger.info("Created rule %s for pattern '%s'", new_id, payee_pattern)
        return rule  # type: ignore[return-value]
    finally:
        conn.close()


def update_existing_rule(
    rule_id: int,
    payee_pattern: str,
    match_type: str,
    category_id: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> dict:
    conn = get_db()
    try:
        update_rule(
            conn,
            rule_id=rule_id,
            payee_pattern=payee_pattern,
            match_type=match_type,
            category_id=category_id,
            min_amount=min_amount,
            max_amount=max_amount,
            confidence=1.0,
        )
        conn.commit()
        rule = get_rule_by_id(conn, rule_id)
        logger.info("Updated rule %s", rule_id)
        return rule  # type: ignore[return-value]
    finally:
        conn.close()


def delete_existing_rule(rule_id: int) -> dict:
    """Delete a rule and return its data (for undo)."""
    conn = get_db()
    try:
        rule = get_rule_by_id(conn, rule_id)
        if not rule:
            raise ValueError(f"Rule {rule_id} not found")
        delete_rule(conn, rule_id)
        conn.commit()
        logger.info("Deleted rule %s", rule_id)
        return rule
    finally:
        conn.close()


def set_payee_category(payee_name: str, category_name: str) -> dict:
    """
    Resolve a natural-language correction like "Mr. Ricos → Dining Out":
    1. Find the category by name (case-insensitive, partial match allowed).
    2. Create or update an exact-match rule for the payee.
    3. Retroactively apply the category to all existing transactions for that payee.
    4. Enqueue write-back for each affected transaction.
    Returns a summary dict.
    """
    conn = get_db()
    try:
        # Resolve category name → id
        cat_row = conn.execute("""
            SELECT c.id, c.name, cg.name as group_name
            FROM categories c
            LEFT JOIN category_groups cg ON c.category_group_id = cg.id
            WHERE LOWER(c.name) = LOWER(?) AND c.deleted = 0
        """, (category_name,)).fetchone()

        if not cat_row:
            cat_row = conn.execute("""
                SELECT c.id, c.name, cg.name as group_name
                FROM categories c
                LEFT JOIN category_groups cg ON c.category_group_id = cg.id
                WHERE LOWER(c.name) LIKE LOWER(?) AND c.deleted = 0
                LIMIT 1
            """, (f"%{category_name}%",)).fetchone()

        if not cat_row:
            return {"error": f"Category '{category_name}' not found. Check the name and try again."}

        category_id = cat_row["id"]
        category_display = f"{cat_row['group_name']} > {cat_row['name']}" if cat_row["group_name"] else cat_row["name"]

        # Verify transactions exist before doing anything
        txns = conn.execute("""
            SELECT id FROM transactions
            WHERE LOWER(payee_name) = LOWER(?) AND deleted = 0
        """, (payee_name,)).fetchall()

        if not txns:
            return {"error": f"No transactions found for payee '{payee_name}'. Rule not created."}

        # Create or update rule (replace any existing exact rule for this payee)
        existing_rule = conn.execute("""
            SELECT id FROM categorization_rules
            WHERE LOWER(payee_pattern) = LOWER(?) AND match_type = 'exact'
            LIMIT 1
        """, (payee_name,)).fetchone()

        if existing_rule:
            update_rule(
                conn,
                rule_id=existing_rule["id"],
                payee_pattern=payee_name,
                match_type="exact",
                category_id=category_id,
                min_amount=None,
                max_amount=None,
                confidence=1.0,
            )
            rule_action = "updated"
        else:
            create_rule(
                conn,
                payee_pattern=payee_name,
                match_type="exact",
                category_id=category_id,
                min_amount=None,
                max_amount=None,
                confidence=1.0,
                source="manual",
            )
            rule_action = "created"

        for txn in txns:
            conn.execute("""
                UPDATE transactions
                SET category_id = ?,
                    categorization_status = 'approved',
                    suggestion_source = 'manual'
                WHERE id = ?
            """, (category_id, txn["id"]))
            enqueue_write_back(conn, txn["id"], category_id)

        conn.commit()
        logger.info(
            "set_payee_category: payee='%s' → category='%s', rule=%s, txns=%d",
            payee_name, category_display, rule_action, len(txns),
        )
        return {
            "category": category_display,
            "category_id": category_id,
            "rule": rule_action,
            "transactions_updated": len(txns),
            "write_back_queued": len(txns),
        }
    finally:
        conn.close()


def restore_rule(
    payee_pattern: str,
    match_type: str,
    category_id: str,
    min_amount: float | None = None,
    max_amount: float | None = None,
    confidence: float = 1.0,
    source: str = "manual",
    times_applied: int = 0,
) -> dict:
    """Re-create a previously deleted rule with its original metadata."""
    conn = get_db()
    try:
        new_id = create_rule(
            conn,
            payee_pattern=payee_pattern,
            match_type=match_type,
            category_id=category_id,
            min_amount=min_amount,
            max_amount=max_amount,
            confidence=confidence,
            source=source,
        )
        if times_applied:
            conn.execute(
                "UPDATE categorization_rules SET times_applied = ? WHERE id = ?",
                (times_applied, new_id),
            )
        conn.commit()
        rule = get_rule_by_id(conn, new_id)
        logger.info("Restored rule as %s (pattern '%s')", new_id, payee_pattern)
        return rule  # type: ignore[return-value]
    finally:
        conn.close()
