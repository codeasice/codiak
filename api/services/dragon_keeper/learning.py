"""Learning service — auto-creates rules from repeated user corrections."""
import logging
from api.models.dragon_keeper.db import (
    get_db,
    get_correction_count,
    rule_exists,
    create_learned_rule,
    apply_rule_retroactively,
    enqueue_write_back,
    get_manual_review_payees,
    set_manual_review_payees,
)

logger = logging.getLogger("dragon_keeper.learning")

LEARNING_THRESHOLD = 2


def check_and_create_rule(payee_name: str, category_id: str) -> dict | None:
    """Check if we should auto-create a rule based on correction history.
    Returns rule info if created, None otherwise."""
    if not payee_name or not category_id:
        return None

    conn = get_db()
    try:
        if rule_exists(conn, payee_name, category_id):
            return None

        count = get_correction_count(conn, payee_name, category_id)
        if count >= LEARNING_THRESHOLD:
            rule_id = create_learned_rule(conn, payee_name, category_id)
            retroactive_count = apply_rule_retroactively(conn, rule_id, payee_name, category_id)
            if retroactive_count > 0:
                rows = conn.execute(
                    "SELECT id FROM transactions WHERE payee_name = ? AND categorization_status = 'rule_applied' AND suggestion_source = 'rule'",
                    (payee_name,),
                ).fetchall()
                for row in rows:
                    enqueue_write_back(conn, row["id"], category_id)
            conn.commit()
            logger.info(
                "Auto-created rule #%d: '%s' → %s (after %d corrections, %d retroactively applied)",
                rule_id, payee_name, category_id, count, retroactive_count,
            )
            return {
                "rule_id": rule_id,
                "payee_pattern": payee_name,
                "category_id": category_id,
                "source": "learned",
                "corrections_count": count,
                "retroactive_count": retroactive_count,
            }
        return None
    finally:
        conn.close()


def add_manual_review_payee(payee_name: str) -> bool:
    conn = get_db()
    try:
        payees = get_manual_review_payees(conn)
        if payee_name not in payees:
            payees.append(payee_name)
            set_manual_review_payees(conn, payees)
            conn.commit()
            logger.info("Added '%s' to manual review list", payee_name)
            return True
        return False
    finally:
        conn.close()


def remove_manual_review_payee(payee_name: str) -> bool:
    conn = get_db()
    try:
        payees = get_manual_review_payees(conn)
        if payee_name in payees:
            payees.remove(payee_name)
            set_manual_review_payees(conn, payees)
            conn.commit()
            return True
        return False
    finally:
        conn.close()


def get_manual_review_list() -> list[str]:
    conn = get_db()
    try:
        return get_manual_review_payees(conn)
    finally:
        conn.close()
