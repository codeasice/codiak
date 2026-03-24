"""Write-back processor — pushes approved categorizations to YNAB."""
import os
import logging
from dotenv import load_dotenv

import ynab
from ynab.models.put_transaction_wrapper import PutTransactionWrapper
from ynab.models.existing_transaction import ExistingTransaction

from api.models.dragon_keeper.db import get_db, get_setting, _now_utc
from api.services.dragon_keeper.rate_limiter import ynab_limiter

load_dotenv()
logger = logging.getLogger("dragon_keeper.write_back")

MAX_RETRIES = 5


def _get_pending_items(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT id, transaction_id, category_id, retry_count
        FROM write_back_queue
        WHERE status IN ('pending', 'failed')
        AND retry_count < ?
        ORDER BY created_at ASC
    """, (MAX_RETRIES,)).fetchall()
    return [dict(r) for r in rows]


def process_write_back_queue() -> dict:
    """Process pending write-back items, pushing category changes to YNAB."""
    conn = get_db()
    try:
        budget_id = get_setting(conn, "ynab_budget_id")
        if not budget_id:
            return {"processed": 0, "succeeded": 0, "failed": 0, "error": "no_budget_id"}

        api_key = os.getenv("YNAB_API_KEY")
        if not api_key:
            return {"processed": 0, "succeeded": 0, "failed": 0, "error": "no_api_key"}

        items = _get_pending_items(conn)
        if not items:
            return {"processed": 0, "succeeded": 0, "failed": 0}

        config = ynab.Configuration(access_token=api_key)
        succeeded = 0
        failed = 0

        with ynab.ApiClient(config) as client:
            txn_api = ynab.api.transactions_api.TransactionsApi(client)

            for item in items:
                if not ynab_limiter.wait_and_acquire(timeout=10.0):
                    logger.warning("Rate limit reached, stopping write-back")
                    break

                conn.execute(
                    "UPDATE write_back_queue SET status = 'in_progress' WHERE id = ?",
                    (item["id"],)
                )
                conn.commit()

                try:
                    wrapper = PutTransactionWrapper(
                        transaction=ExistingTransaction(category_id=item["category_id"])
                    )
                    txn_api.update_transaction(budget_id, item["transaction_id"], wrapper)

                    conn.execute("""
                        UPDATE write_back_queue
                        SET status = 'completed', completed_at = ?
                        WHERE id = ?
                    """, (_now_utc(), item["id"]))
                    conn.commit()
                    succeeded += 1
                    logger.info("Write-back succeeded for transaction %s", item["transaction_id"])

                except ynab.ApiException as e:
                    retry = item["retry_count"] + 1
                    error_msg = f"HTTP {getattr(e, 'status', '?')}: {getattr(e, 'reason', str(e))}"
                    conn.execute("""
                        UPDATE write_back_queue
                        SET status = 'failed', retry_count = ?, error_message = ?
                        WHERE id = ?
                    """, (retry, error_msg, item["id"]))
                    conn.commit()
                    failed += 1
                    logger.error("Write-back failed for %s: %s", item["transaction_id"], error_msg)

        total = succeeded + failed
        logger.info("Write-back: %d processed, %d succeeded, %d failed", total, succeeded, failed)
        return {"processed": total, "succeeded": succeeded, "failed": failed}
    finally:
        conn.close()


def get_write_back_status() -> dict:
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' AND retry_count < ? THEN 1 ELSE 0 END) as failed_retryable,
                SUM(CASE WHEN status = 'failed' AND retry_count >= ? THEN 1 ELSE 0 END) as failed_permanent
            FROM write_back_queue
        """, (MAX_RETRIES, MAX_RETRIES)).fetchone()
        return {
            "pending": (row["pending"] or 0) if row else 0,
            "in_progress": (row["in_progress"] or 0) if row else 0,
            "completed": (row["completed"] or 0) if row else 0,
            "failed_retryable": (row["failed_retryable"] or 0) if row else 0,
            "failed_permanent": (row["failed_permanent"] or 0) if row else 0,
        }
    finally:
        conn.close()
