"""Rules management service – CRUD for categorization rules."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    get_all_rules_with_categories,
    get_rule_by_id,
    create_rule,
    update_rule,
    delete_rule,
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
