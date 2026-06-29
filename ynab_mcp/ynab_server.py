"""
Codiak YNAB MCP Server
======================
Exposes YNAB and local account data from dragon_keeper.db as MCP tools.

Usage:
    python -m ynab_mcp.ynab_server

Environment:
    YNAB_API_KEY    Required for sync_ynab()
"""
from typing import Optional
from fastmcp import FastMCP

from api.models.dragon_keeper.db import (
    get_db,
    get_budget_info,
    get_category_groups,
    get_categories,
    get_category,
    get_transactions,
    get_transaction,
    get_payees_with_stats,
    get_payee_with_stats,
    get_account_balances,
    get_balance_snapshot_history,
)

mcp = FastMCP(
    name="Codiak YNAB",
    instructions=(
        "Access YNAB budget data from a local SQLite database. "
        "All monetary amounts are in dollars. "
        "Use sync_ynab() to pull fresh data from the YNAB API into the local database."
    ),
)


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

@mcp.tool()
def sync_ynab(budget_id: Optional[str] = None, flush_queue: bool = True) -> dict:
    """
    Pull fresh data from the YNAB API into the local database, then optionally
    push any approved categorizations back to YNAB.

    Syncs accounts, categories, payees, and transactions (delta-aware —
    only fetches changes since the last sync). Also runs the categorization
    pipeline and takes a balance snapshot after syncing.

    Requires the YNAB_API_KEY environment variable to be set.

    Args:
        budget_id:   The YNAB budget UUID to sync. If omitted, uses the
                     budget stored from the last sync, or the first available budget.
        flush_queue: If True (default), also push any pending approved
                     categorizations back to YNAB after syncing.
    """
    from api.services.dragon_keeper.sync_engine import run_sync, SyncError
    from api.services.dragon_keeper.write_back import process_write_back_queue
    try:
        result = run_sync(budget_id=budget_id)
        if flush_queue:
            result["write_back"] = process_write_back_queue()
        return result
    except SyncError as e:
        return {"error": e.code, "detail": e.detail}


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------

@mcp.tool()
def set_payee_category(payee_name: str, category_name: str) -> dict:
    """
    Assign a category to all transactions for a given payee, creating or updating
    a categorization rule so future transactions are handled automatically.

    Example: set_payee_category("Mr. Ricos", "Dining Out")

    - Resolves the category by name (case-insensitive, partial match allowed).
    - Creates or updates an exact-match rule for the payee.
    - Retroactively updates all existing transactions for that payee.
    - Enqueues write-back so YNAB is updated on the next sync.

    Args:
        payee_name:    The payee name as it appears in YNAB (e.g. "Mr. Ricos").
        category_name: The category to assign (e.g. "Dining Out").
    """
    from api.services.dragon_keeper.rules_management import set_payee_category as _set
    return _set(payee_name=payee_name, category_name=category_name)


@mcp.tool()
def recategorize_by_payee(
    payee: str,
    new_category: str,
    current_category: Optional[str] = None,
) -> dict:
    """
    Bulk recategorize all transactions matching a payee pattern (partial match)
    and create or update a rule so future transactions are handled automatically.

    Args:
        payee:            Payee name or partial match (e.g. "Ricos" matches "Mr. Ricos").
        new_category:     Target category name (e.g. "Dining Out").
        current_category: Optional — only change transactions currently in this category.
    """
    from api.services.dragon_keeper.keeper_tools import tool_recategorize_by_payee
    return tool_recategorize_by_payee(payee, new_category, current_category)


@mcp.tool()
def correct_transaction(transaction_id: str, category_name: str) -> dict:
    """
    Correct a single transaction's category and enqueue write-back to YNAB.

    Args:
        transaction_id: The YNAB transaction UUID.
        category_name:  The correct category name (fuzzy match supported).
    """
    from api.services.dragon_keeper.keeper_tools import tool_correct_transaction
    return tool_correct_transaction(transaction_id, category_name)


@mcp.tool()
def approve_transactions(transaction_ids: list[str]) -> dict:
    """
    Approve one or more pending categorization suggestions, applying their
    suggested categories and enqueueing write-back to YNAB.

    Args:
        transaction_ids: List of transaction UUIDs to approve.
    """
    from api.services.dragon_keeper.keeper_tools import tool_approve_transactions
    return tool_approve_transactions(transaction_ids)


@mcp.tool()
def get_pending_categorizations() -> dict:
    """Get all transactions currently awaiting categorization review."""
    from api.services.dragon_keeper.keeper_tools import tool_get_pending_categorizations
    return tool_get_pending_categorizations()


@mcp.tool()
def query_spending(
    payee: Optional[str] = None,
    category: Optional[str] = None,
    days: int = 30,
) -> dict:
    """
    Look up spending totals and recent transactions.

    Args:
        payee:    Partial payee name to filter by.
        category: Partial category name to filter by.
        days:     Days to look back (default 30, use 0 for all time).
    """
    from api.services.dragon_keeper.keeper_tools import tool_query_spending
    return tool_query_spending(payee, category, days)


@mcp.tool()
def get_spending_breakdown(days: int = 30) -> dict:
    """
    Get the top spending categories for a time period.

    Args:
        days: Number of days to look back (default 30).
    """
    from api.services.dragon_keeper.keeper_tools import tool_get_spending_breakdown
    return tool_get_spending_breakdown(days)


@mcp.tool()
def generate_debrief() -> dict:
    """Generate a financial debrief: safe-to-spend, weekly spending, streak, and queue status."""
    from api.services.dragon_keeper.keeper_tools import tool_generate_debrief
    return tool_generate_debrief()


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

@mcp.tool()
def get_budget() -> dict:
    """Get the active YNAB budget ID stored from the last sync."""
    conn = get_db()
    try:
        result = get_budget_info(conn)
        if result is None:
            return {"error": "No budget found. Run sync_ynab() first."}
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@mcp.tool()
def get_category_groups_tool(include_hidden: bool = False) -> list[dict]:
    """
    List all YNAB category groups.

    Args:
        include_hidden: If True, include hidden/inactive groups.
    """
    conn = get_db()
    try:
        return get_category_groups(conn, include_hidden=include_hidden)
    finally:
        conn.close()


@mcp.tool()
def get_categories_tool(include_hidden: bool = False) -> list[dict]:
    """
    List all YNAB categories with current budget amounts.

    Returns each category's budgeted amount, activity (spending), and
    remaining balance for the current month. Amounts are in dollars.

    Args:
        include_hidden: If True, include hidden/inactive categories.
    """
    conn = get_db()
    try:
        return get_categories(conn, include_hidden=include_hidden)
    finally:
        conn.close()


@mcp.tool()
def get_category_tool(category_id: str) -> dict:
    """
    Get details for a single YNAB category by ID.

    Args:
        category_id: The YNAB category UUID.
    """
    conn = get_db()
    try:
        result = get_category(conn, category_id)
        if result is None:
            return {"error": f"Category '{category_id}' not found."}
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@mcp.tool()
def get_transactions_tool(
    limit: int = 50,
    since_date: Optional[str] = None,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    payee_id: Optional[str] = None,
) -> list[dict]:
    """
    Get YNAB transactions, optionally filtered.

    Args:
        limit:       Max transactions to return (default 50, max 500).
        since_date:  Only return transactions on or after this date (YYYY-MM-DD).
        account_id:  Filter to a specific account ID.
        category_id: Filter to a specific category ID.
        payee_id:    Filter to a specific payee ID.
    """
    conn = get_db()
    try:
        return get_transactions(
            conn,
            limit=limit,
            since_date=since_date,
            account_id=account_id,
            category_id=category_id,
            payee_id=payee_id,
        )
    finally:
        conn.close()


@mcp.tool()
def get_transaction_tool(transaction_id: str) -> dict:
    """
    Get a single YNAB transaction by ID.

    Args:
        transaction_id: The YNAB transaction UUID.
    """
    conn = get_db()
    try:
        result = get_transaction(conn, transaction_id)
        if result is None:
            return {"error": f"Transaction '{transaction_id}' not found."}
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Payees
# ---------------------------------------------------------------------------

@mcp.tool()
def get_payees_tool(limit: int = 200) -> list[dict]:
    """
    List YNAB payees sorted by transaction count, with summary stats.

    Returns each payee's total spend, transaction count, and date range.

    Args:
        limit: Max payees to return (default 200).
    """
    conn = get_db()
    try:
        return get_payees_with_stats(conn, limit=limit)
    finally:
        conn.close()


@mcp.tool()
def get_payee_tool(payee_id: str) -> dict:
    """
    Get detailed stats for a single YNAB payee, including category breakdown.

    Args:
        payee_id: The YNAB payee UUID.
    """
    conn = get_db()
    try:
        result = get_payee_with_stats(conn, payee_id)
        if result is None:
            return {"error": f"Payee '{payee_id}' not found."}
        return result
    finally:
        conn.close()


@mcp.tool()
def get_payee_transactions_tool(
    payee_id: str,
    limit: int = 50,
    since_date: Optional[str] = None,
) -> list[dict]:
    """
    Get transactions for a specific YNAB payee.

    Args:
        payee_id:   The YNAB payee UUID.
        limit:      Max transactions to return (default 50).
        since_date: Only return transactions on or after this date (YYYY-MM-DD).
    """
    conn = get_db()
    try:
        return get_transactions(conn, payee_id=payee_id, limit=limit, since_date=since_date)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Accounts & Balances
# ---------------------------------------------------------------------------

@mcp.tool()
def get_account_balances_tool() -> list[dict]:
    """List all open YNAB accounts with current balances in dollars."""
    conn = get_db()
    try:
        return get_account_balances(conn)
    finally:
        conn.close()


@mcp.tool()
def get_balances() -> dict:
    """Get all account balances and the current safe-to-spend amount in one call."""
    from api.services.dragon_keeper.keeper_tools import tool_get_balances
    return tool_get_balances()


@mcp.tool()
def get_account_balance_history_tool(account_id: Optional[str] = None) -> list[dict]:
    """
    Get balance snapshot history, newest first.

    Args:
        account_id: If provided, return history for a single account only.
                    If omitted, return snapshots for all accounts.
    """
    conn = get_db()
    try:
        return get_balance_snapshot_history(conn, account_id=account_id)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
