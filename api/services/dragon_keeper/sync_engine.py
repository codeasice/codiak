"""YNAB sync engine — fetches data from YNAB API and stores in local SQLite."""
import os
import logging
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
import ynab

from api.models.dragon_keeper.db import (
    get_db, upsert_accounts, upsert_category_groups, upsert_categories,
    upsert_payees, upsert_transactions, get_setting, set_setting,
    update_sync_state, log_sync_event,
)
from api.services.dragon_keeper.rate_limiter import ynab_limiter

load_dotenv()

logger = logging.getLogger("dragon_keeper.sync")

YNAB_API_KEY_ENV = "YNAB_API_KEY"


class SyncError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


def _get_ynab_config() -> ynab.Configuration:
    api_key = os.getenv(YNAB_API_KEY_ENV)
    if not api_key:
        raise SyncError("YNAB_API_KEY_MISSING", "YNAB_API_KEY environment variable is not set.")
    return ynab.Configuration(access_token=api_key)


def _rate_limited_call(fn, *args, **kwargs) -> Any:
    if not ynab_limiter.wait_and_acquire(timeout=30.0):
        raise SyncError(
            "YNAB_RATE_LIMITED",
            f"Rate limit exceeded. {ynab_limiter.remaining} requests remaining.",
        )
    return fn(*args, **kwargs)


def _millis_to_dollars(milliunit: int | None) -> float:
    if milliunit is None:
        return 0.0
    return round(milliunit / 1000.0, 2)


def _enum_val(enum_obj) -> str | None:
    """Extract the string value from a YNAB SDK enum object."""
    if enum_obj is None:
        return None
    if hasattr(enum_obj, "value"):
        return str(enum_obj.value)
    return str(enum_obj)


def discover_budgets() -> list[dict]:
    config = _get_ynab_config()
    with ynab.ApiClient(config) as client:
        api = ynab.api.budgets_api.BudgetsApi(client)
        resp = _rate_limited_call(api.get_budgets)
        return [{"id": str(b.id), "name": b.name} for b in resp.data.budgets]


def run_sync(budget_id: str | None = None) -> dict:
    """Run a full or delta sync from YNAB. Returns a summary dict."""
    conn = get_db()
    try:
        config = _get_ynab_config()

        if not budget_id:
            budget_id = get_setting(conn, "ynab_budget_id")

        if not budget_id:
            budgets = discover_budgets()
            if not budgets:
                raise SyncError("NO_BUDGETS", "No budgets found in your YNAB account.")
            budget_id = budgets[0]["id"]

        set_setting(conn, "ynab_budget_id", budget_id)
        log_sync_event(conn, None, "sync_started", f"budget_id={budget_id}")

        sk_str = get_setting(conn, "ynab_server_knowledge")
        server_knowledge = int(sk_str) if sk_str else None

        with ynab.ApiClient(config) as client:
            # --- Accounts ---
            accounts_api = ynab.api.accounts_api.AccountsApi(client)
            accounts_resp = _rate_limited_call(accounts_api.get_accounts, budget_id)
            accounts_data = [
                {
                    "id": str(a.id),
                    "budget_id": budget_id,
                    "name": a.name,
                    "type": _enum_val(a.type) or "unknown",
                    "on_budget": int(a.on_budget) if a.on_budget else 0,
                    "closed": int(a.closed) if a.closed else 0,
                    "balance": _millis_to_dollars(a.balance),
                    "cleared_balance": _millis_to_dollars(a.cleared_balance),
                    "uncleared_balance": _millis_to_dollars(a.uncleared_balance),
                    "note": a.note,
                    "deleted": int(a.deleted) if a.deleted else 0,
                }
                for a in accounts_resp.data.accounts
            ]
            upsert_accounts(conn, accounts_data)
            logger.info("Synced %d accounts", len(accounts_data))

            # --- Categories ---
            categories_api = ynab.api.categories_api.CategoriesApi(client)
            cats_resp = _rate_limited_call(categories_api.get_categories, budget_id)
            groups_data = []
            cats_data = []
            for group in cats_resp.data.category_groups:
                groups_data.append({
                    "id": str(group.id),
                    "name": group.name,
                    "hidden": int(group.hidden) if group.hidden else 0,
                    "deleted": int(group.deleted) if group.deleted else 0,
                })
                for cat in group.categories:
                    cats_data.append({
                        "id": str(cat.id),
                        "category_group_id": str(group.id),
                        "name": cat.name,
                        "hidden": int(cat.hidden) if cat.hidden else 0,
                        "budgeted": _millis_to_dollars(cat.budgeted),
                        "activity": _millis_to_dollars(cat.activity),
                        "balance": _millis_to_dollars(cat.balance),
                        "goal_type": _enum_val(cat.goal_type),
                        "goal_target": _millis_to_dollars(cat.goal_target) if cat.goal_target else None,
                        "goal_target_month": cat.goal_target_month,
                        "goal_percentage_complete": cat.goal_percentage_complete,
                        "note": cat.note,
                        "deleted": int(cat.deleted) if cat.deleted else 0,
                    })
            upsert_category_groups(conn, groups_data)
            upsert_categories(conn, cats_data)
            logger.info("Synced %d groups, %d categories", len(groups_data), len(cats_data))

            # --- Payees ---
            payees_api = ynab.api.payees_api.PayeesApi(client)
            payees_resp = _rate_limited_call(payees_api.get_payees, budget_id)
            payees_data = [
                {
                    "id": str(p.id),
                    "name": p.name or "Unknown",
                    "deleted": int(p.deleted) if p.deleted else 0,
                }
                for p in payees_resp.data.payees
            ]
            upsert_payees(conn, payees_data)
            logger.info("Synced %d payees", len(payees_data))

            # --- Transactions (delta-aware) ---
            transactions_api = ynab.api.transactions_api.TransactionsApi(client)
            kwargs = {}
            if server_knowledge is not None:
                kwargs["last_knowledge_of_server"] = server_knowledge
            txns_resp = _rate_limited_call(
                transactions_api.get_transactions, budget_id, **kwargs,
            )

            txns_data = [
                {
                    "id": str(t.id),
                    "account_id": str(t.account_id),
                    "date": t.var_date.isoformat() if hasattr(t.var_date, "isoformat") else str(t.var_date),
                    "amount": _millis_to_dollars(t.amount),
                    "payee_id": str(t.payee_id) if t.payee_id else None,
                    "payee_name": t.payee_name,
                    "category_id": str(t.category_id) if t.category_id else None,
                    "category_name": t.category_name,
                    "memo": t.memo,
                    "cleared": _enum_val(t.cleared) or "uncleared",
                    "approved": int(t.approved) if t.approved else 0,
                    "transfer_account_id": str(t.transfer_account_id) if t.transfer_account_id else None,
                    "deleted": int(t.deleted) if t.deleted else 0,
                }
                for t in txns_resp.data.transactions
            ]
            upsert_transactions(conn, txns_data)
            new_sk = txns_resp.data.server_knowledge
            set_setting(conn, "ynab_server_knowledge", str(new_sk))
            logger.info("Synced %d transactions, server_knowledge=%s", len(txns_data), new_sk)

        # Per-account sync state
        account_txn_counts: dict[str, int] = {}
        for t in txns_data:
            aid = t["account_id"]
            account_txn_counts[aid] = account_txn_counts.get(aid, 0) + 1

        for a in accounts_data:
            txn_count = account_txn_counts.get(a["id"], 0)
            update_sync_state(conn, a["id"], "success", txn_count)

        log_sync_event(
            conn, None, "sync_completed",
            f"accounts={len(accounts_data)} categories={len(cats_data)} "
            f"payees={len(payees_data)} transactions={len(txns_data)}",
        )
        conn.commit()

        try:
            from api.services.dragon_keeper.categorization import run_categorization_pipeline
            cat_result = run_categorization_pipeline()
            logger.info("Post-sync categorization: %s", cat_result)
        except Exception as e:
            logger.warning("Post-sync categorization failed: %s", e)

        is_delta = server_knowledge is not None
        return {
            "status": "success",
            "sync_type": "delta" if is_delta else "full",
            "budget_id": budget_id,
            "accounts_synced": len(accounts_data),
            "categories_synced": len(cats_data),
            "category_groups_synced": len(groups_data),
            "payees_synced": len(payees_data),
            "transactions_synced": len(txns_data),
            "server_knowledge": new_sk,
            "synced_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    except SyncError:
        conn.rollback()
        raise
    except ynab.ApiException as e:
        conn.rollback()
        log_sync_event(conn, None, "sync_failed", str(e))
        conn.commit()
        status_code = getattr(e, "status", 500)
        if status_code == 429:
            raise SyncError("YNAB_RATE_LIMITED", "YNAB rate limit exceeded. Try again later.")
        raise SyncError(
            "YNAB_API_ERROR",
            f"YNAB API error (HTTP {status_code}): {e.reason if hasattr(e, 'reason') else str(e)}",
        )
    except Exception as e:
        conn.rollback()
        logger.error("Sync failed: %s", e)
        raise SyncError("SYNC_FAILED", f"Unexpected sync error: {e}")
    finally:
        conn.close()
