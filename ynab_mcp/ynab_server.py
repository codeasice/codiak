"""
Codiak YNAB MCP Server
======================
Exposes YNAB and local account data from accounts.db as MCP tools.

Usage:
    python -m ynab_mcp.ynab_server

Environment:
    CODIAK_DB_PATH  Path to accounts.db (default: ./accounts.db)

Install dependency:
    pip install fastmcp
"""
from typing import Optional
from fastmcp import FastMCP

from ynab_mcp import queries

mcp = FastMCP(
    name="Codiak YNAB",
    instructions=(
        "Access YNAB budget data from a local SQLite database. "
        "All monetary amounts are in dollars. "
        "Use get_budgets() first to discover available budget IDs. "
        "The database is read-only — use the Streamlit app to import or modify data."
    ),
)


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

@mcp.tool()
def get_budgets() -> list[dict]:
    """List all YNAB budgets stored in the local database."""
    return queries.get_budgets()


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@mcp.tool()
def get_category_groups() -> list[dict]:
    """List all YNAB category groups."""
    return queries.get_category_groups()


@mcp.tool()
def get_categories(include_hidden: bool = False) -> list[dict]:
    """
    List all YNAB categories with current budget amounts.

    Returns each category's budgeted amount, activity (spending), and
    remaining balance for the current month. Amounts are in dollars.

    Args:
        include_hidden: If True, include hidden/inactive categories.
    """
    return queries.get_categories(include_hidden=include_hidden)


@mcp.tool()
def get_category(category_id: str) -> Optional[dict]:
    """
    Get details for a single YNAB category by ID.

    Args:
        category_id: The YNAB category UUID.
    """
    result = queries.get_category(category_id)
    if result is None:
        return {"error": f"Category '{category_id}' not found."}
    return result


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@mcp.tool()
def get_transactions(
    budget_id: Optional[str] = None,
    limit: int = 50,
    since_date: Optional[str] = None,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    payee_id: Optional[str] = None,
) -> list[dict]:
    """
    Get YNAB transactions, optionally filtered.

    Args:
        budget_id:   Filter to a specific budget (UUID from get_budgets).
        limit:       Max transactions to return (default 50, max 500).
        since_date:  Only return transactions on or after this date (YYYY-MM-DD).
        account_id:  Filter to a specific YNAB account UUID.
        category_id: Filter to a specific category UUID.
        payee_id:    Filter to a specific payee UUID.
    """
    limit = min(limit, 500)
    return queries.get_transactions(
        budget_id=budget_id,
        limit=limit,
        since_date=since_date,
        account_id=account_id,
        category_id=category_id,
        payee_id=payee_id,
    )


@mcp.tool()
def get_transaction(transaction_id: str) -> Optional[dict]:
    """
    Get a single YNAB transaction by ID, including any split subtransactions.

    Args:
        transaction_id: The YNAB transaction UUID.
    """
    result = queries.get_transaction(transaction_id)
    if result is None:
        return {"error": f"Transaction '{transaction_id}' not found."}
    return result


# ---------------------------------------------------------------------------
# Payees
# ---------------------------------------------------------------------------

@mcp.tool()
def get_payees(limit: int = 200) -> list[dict]:
    """
    List YNAB payees sorted by transaction count, with summary stats.

    Returns each payee's total spend, transaction count, date range, and
    number of unique categories used.

    Args:
        limit: Max payees to return (default 200).
    """
    return queries.get_payees(limit=limit)


@mcp.tool()
def get_payee(payee_id: str) -> Optional[dict]:
    """
    Get detailed stats for a single YNAB payee, including category breakdown.

    Args:
        payee_id: The YNAB payee UUID.
    """
    result = queries.get_payee(payee_id)
    if result is None:
        return {"error": f"Payee '{payee_id}' not found."}
    return result


@mcp.tool()
def get_payee_transactions(
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
    return queries.get_transactions(
        payee_id=payee_id,
        limit=limit,
        since_date=since_date,
    )


# ---------------------------------------------------------------------------
# YNAB Accounts
# ---------------------------------------------------------------------------

@mcp.tool()
def get_ynab_accounts(budget_id: Optional[str] = None) -> list[dict]:
    """
    List YNAB accounts with current balances.

    Args:
        budget_id: Filter to a specific budget UUID (from get_budgets).
                   If omitted, returns accounts across all budgets.
    """
    return queries.get_ynab_accounts(budget_id=budget_id)


# ---------------------------------------------------------------------------
# Local Accounts & Balances
# ---------------------------------------------------------------------------

@mcp.tool()
def get_local_accounts() -> list[dict]:
    """
    List local (non-YNAB) accounts with their hierarchy and APR info.

    These are accounts managed in the Codiak account system, which may
    be linked to YNAB accounts. Includes asset, liability, and investment
    accounts. APR is returned as a percentage (e.g. 24.99 = 24.99%).
    """
    return queries.get_local_accounts()


@mcp.tool()
def get_account_balances(account_id: Optional[str] = None) -> list[dict]:
    """
    Get the most recent balance snapshot for each local account.

    Args:
        account_id: If provided, return balance history for a single account.
                    If omitted, return the latest balance for every account.
    """
    return queries.get_account_balances(account_id=account_id)


@mcp.tool()
def get_account_balance_history(account_id: str) -> list[dict]:
    """
    Get full balance history for a single local account, newest first.

    Args:
        account_id: The local account ID (from get_local_accounts).
    """
    return queries.get_account_balance_history(account_id)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
