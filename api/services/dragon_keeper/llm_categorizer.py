"""LLM categorizer — tier 2 of the categorization pipeline."""
import os
import re
import json
import logging
from dotenv import load_dotenv

from api.models.dragon_keeper.db import (
    get_db,
    set_llm_suggestion,
    _now_utc,
    get_manual_review_payees,
)

load_dotenv()
logger = logging.getLogger("dragon_keeper.llm_categorizer")

AUTO_APPLY_THRESHOLD = 0.8
BATCH_SIZE = 20
DEFAULT_MAX_TRANSACTIONS = 50
LLM_MODEL = "gpt-4o-mini"
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)


def _extract_uuid(value: str) -> str | None:
    """Extract a UUID from a string that may contain extra text."""
    m = _UUID_RE.search(value)
    return m.group(0) if m else None


def _get_categories(conn) -> list[dict]:
    rows = conn.execute("""
        SELECT c.id, c.name, cg.name as group_name
        FROM categories c
        JOIN category_groups cg ON c.category_group_id = cg.id
        WHERE c.hidden = 0 AND c.deleted = 0 AND cg.hidden = 0 AND cg.deleted = 0
        ORDER BY cg.name, c.name
    """).fetchall()
    return [dict(r) for r in rows]


def _get_pending_for_llm(conn) -> list[dict]:
    """Get transactions that are pending_review and don't already have an LLM suggestion.
    Most recent transactions first so the user sees relevant items categorized first."""
    rows = conn.execute("""
        SELECT id, payee_name, amount, memo
        FROM transactions
        WHERE categorization_status = 'pending_review'
        AND suggestion_source IS NULL
        AND deleted = 0
        ORDER BY date DESC
    """).fetchall()
    return [dict(r) for r in rows]


def _build_prompt(categories: list[dict], transactions: list[dict]) -> tuple[str, str]:
    cat_list = "\n".join(f"{c['id']}  {c['group_name']} > {c['name']}" for c in categories)

    system = f"""You are a financial transaction categorizer.

CATEGORY LIST (one per line, format: UUID  Group > Name):
{cat_list}

For each transaction, pick the best category UUID from the list above.

Respond with a JSON object: {{"suggestions": [...]}}
Each item must have exactly these fields:
- "transaction_id": string (copy the ID exactly)
- "category_id": string (the UUID only, e.g. "dc8b80e8-afa4-43b6-b976-22d3779819ad")
- "confidence": number 0.0-1.0

IMPORTANT: "category_id" must be ONLY the UUID, not the category name."""

    txn_lines = []
    for t in transactions:
        line = f"ID: {t['id']} | Payee: {t['payee_name'] or 'Unknown'} | Amount: ${abs(t['amount']):.2f} | Memo: {t.get('memo') or 'none'}"
        txn_lines.append(line)

    user = "Categorize these transactions:\n\n" + "\n".join(txn_lines)
    return system, user


def _call_llm(system: str, user: str) -> tuple[list[dict], dict]:
    """Call the LLM. Returns (suggestions, usage_info)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, skipping LLM categorization")
        return [], {"skipped": True, "reason": "no_api_key"}

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )

        usage = response.usage
        usage_info = {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

        text = (response.choices[0].message.content or "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "suggestions" in parsed:
            parsed = parsed["suggestions"]
        if not isinstance(parsed, list):
            logger.error("LLM categorization: expected JSON array, got %s", type(parsed).__name__)
            return [], usage_info
        return parsed, usage_info
    except Exception as e:
        logger.error("LLM categorization failed: %s", e)
        return [], {"error": str(e)}


def get_llm_pending_count() -> int:
    """Return count of transactions eligible for LLM processing."""
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM transactions
            WHERE categorization_status = 'pending_review'
            AND suggestion_source IS NULL AND deleted = 0
        """).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def run_llm_categorizer(max_transactions: int | None = None) -> dict:
    """Run LLM categorization on pending transactions.

    Args:
        max_transactions: Cap on how many transactions to process this run.
                          Defaults to DEFAULT_MAX_TRANSACTIONS. Pass 0 for no limit.
    """
    limit = DEFAULT_MAX_TRANSACTIONS if max_transactions is None else max_transactions
    conn = get_db()
    try:
        categories = _get_categories(conn)
        if not categories:
            return {"processed": 0, "auto_applied": 0, "suggested": 0, "error": "no_categories"}

        pending = _get_pending_for_llm(conn)
        manual_payees = set(get_manual_review_payees(conn))
        pending = [
            t for t in pending if (t.get("payee_name") or "") not in manual_payees
        ]

        total_eligible = len(pending)
        if not pending:
            return {"processed": 0, "auto_applied": 0, "suggested": 0,
                    "eligible": 0, "remaining": 0, "api_calls": 0}

        if limit > 0:
            pending = pending[:limit]

        valid_ids = {c["id"] for c in categories}
        batch_txn_ids = set()
        total_auto = 0
        total_suggested = 0
        total_processed = 0
        total_invalid = 0
        invalid_details: list[dict] = []
        total_api_calls = 0
        total_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i:i + BATCH_SIZE]
            batch_txn_ids = {t["id"] for t in batch}
            batch_payees = {t["id"]: t.get("payee_name", "?") for t in batch}
            system, user = _build_prompt(categories, batch)
            suggestions, usage_info = _call_llm(system, user)
            total_api_calls += 1

            if usage_info.get("skipped"):
                return {
                    "processed": 0, "auto_applied": 0, "suggested": 0,
                    "eligible": total_eligible, "remaining": total_eligible,
                    "api_calls": 0, "tokens": total_tokens,
                    "skipped": True, "skip_reason": usage_info.get("reason"),
                }

            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                total_tokens[key] += usage_info.get(key, 0)

            logger.info("LLM batch %d: %d suggestions returned", i // BATCH_SIZE + 1, len(suggestions))

            for s in suggestions:
                tid = s.get("transaction_id", "")
                cid = s.get("category_id", "")
                conf = float(s.get("confidence", 0))

                if not tid or tid not in batch_txn_ids:
                    reason = "unknown_transaction_id"
                    logger.warning("LLM invalid: %s tid=%s", reason, tid[:40])
                    total_invalid += 1
                    invalid_details.append({"reason": reason, "tid": tid[:40], "cid": cid[:40]})
                    continue

                if cid not in valid_ids:
                    extracted = _extract_uuid(cid)
                    if extracted and extracted in valid_ids:
                        cid = extracted
                    else:
                        reason = "unknown_category_id"
                        payee = batch_payees.get(tid, "?")
                        logger.warning("LLM invalid: %s payee=%s cid=%s", reason, payee, cid[:60])
                        total_invalid += 1
                        invalid_details.append({"reason": reason, "payee": payee, "cid": cid[:60]})
                        continue

                if conf >= AUTO_APPLY_THRESHOLD:
                    conn.execute("""
                        UPDATE transactions
                        SET category_id = ?, categorization_status = 'approved',
                            suggested_category_id = ?, suggestion_confidence = ?,
                            suggestion_source = 'llm', updated_at = ?
                        WHERE id = ?
                    """, (cid, cid, conf, _now_utc(), tid))
                    total_auto += 1
                else:
                    set_llm_suggestion(conn, tid, cid, conf)
                    total_suggested += 1
                total_processed += 1

        conn.commit()
        remaining = total_eligible - len(pending)
        logger.info(
            "LLM categorizer: %d processed, %d auto-applied, %d suggested, "
            "%d invalid, %d API calls, %d tokens, %d remaining",
            total_processed, total_auto, total_suggested, total_invalid,
            total_api_calls, total_tokens["total_tokens"], remaining,
        )
        return {
            "processed": total_processed,
            "auto_applied": total_auto,
            "suggested": total_suggested,
            "invalid_suggestions": total_invalid,
            "invalid_details": invalid_details[:20],
            "eligible": total_eligible,
            "remaining": remaining,
            "api_calls": total_api_calls,
            "tokens": total_tokens,
            "batch_size": BATCH_SIZE,
            "max_transactions": limit,
        }
    except Exception as e:
        conn.rollback()
        logger.error("LLM categorizer error: %s", e)
        return {"processed": 0, "auto_applied": 0, "suggested": 0, "error": str(e)}
    finally:
        conn.close()
