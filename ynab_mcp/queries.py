"""
Pure SQL query functions for the YNAB MCP server.

All monetary YNAB amounts are returned in dollars (converted from milliunits).
Local account amounts are returned in dollars (converted from cents).
Amounts stored as integers in the DB:
  - YNAB tables: milliunits → divide by 1000
  - account/balance_snapshot: cents → divide by 100
"""
from typing import Optional
from ynab_mcp.db import get_db


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------

def get_budgets() -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, last_modified_on, first_month, last_month,
               currency_format_iso_code, currency_format_currency_symbol
        FROM ynab_budgets
        ORDER BY name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Category Groups & Categories
# ---------------------------------------------------------------------------

def get_category_groups() -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, updated_at
        FROM ynab_category_groups
        ORDER BY name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories(include_hidden: bool = False) -> list[dict]:
    conn = get_db()
    query = """
        SELECT id, name, category_group_id, category_group_name, full_name,
               hidden, note,
               ROUND(budgeted / 1000.0, 2) as budgeted,
               ROUND(activity / 1000.0, 2) as activity,
               ROUND(balance / 1000.0, 2) as balance,
               goal_type, goal_target_month,
               ROUND(COALESCE(goal_target, 0) / 1000.0, 2) as goal_target,
               goal_percentage_complete
        FROM ynab_categories
        WHERE deleted = 0
    """
    if not include_hidden:
        query += " AND hidden = 0"
    query += " ORDER BY category_group_name, name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category(category_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("""
        SELECT id, name, category_group_id, category_group_name, full_name,
               hidden, note,
               ROUND(budgeted / 1000.0, 2) as budgeted,
               ROUND(activity / 1000.0, 2) as activity,
               ROUND(balance / 1000.0, 2) as balance,
               goal_type, goal_target_month,
               ROUND(COALESCE(goal_target, 0) / 1000.0, 2) as goal_target,
               goal_percentage_complete
        FROM ynab_categories
        WHERE id = ? AND deleted = 0
    """, (category_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def get_transactions(
    budget_id: Optional[str] = None,
    limit: int = 50,
    since_date: Optional[str] = None,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    payee_id: Optional[str] = None,
) -> list[dict]:
    conn = get_db()

    query = """
        SELECT
            t.id, t.date,
            ROUND(t.amount / 1000.0, 2) as amount,
            t.memo, t.cleared, t.approved, t.flag_color, t.flag_name,
            t.account_id, t.account_name,
            t.payee_id,
            COALESCE(p.name, t.payee_name, 'Unknown') as payee_name,
            t.category_id,
            COALESCE(c.name, t.category_name, 'Uncategorized') as category_name,
            COALESCE(c.category_group_name, '') as category_group_name,
            t.transfer_account_id
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        LEFT JOIN ynab_payees p ON t.payee_id = p.id
        WHERE t.deleted = 0
    """
    params: list = []

    if budget_id:
        query += """
            AND EXISTS (
                SELECT 1 FROM ynab_account ya
                WHERE ya.ynab_account_id = t.account_id AND ya.budget_id = ?
            )
        """
        params.append(budget_id)
    if since_date:
        query += " AND t.date >= ?"
        params.append(since_date)
    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if payee_id:
        query += " AND t.payee_id = ?"
        params.append(payee_id)

    query += " ORDER BY t.date DESC, t.id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction(transaction_id: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("""
        SELECT
            t.id, t.date,
            ROUND(t.amount / 1000.0, 2) as amount,
            t.memo, t.cleared, t.approved, t.flag_color, t.flag_name,
            t.account_id, t.account_name,
            t.payee_id,
            COALESCE(p.name, t.payee_name, 'Unknown') as payee_name,
            t.category_id,
            COALESCE(c.name, t.category_name, 'Uncategorized') as category_name,
            COALESCE(c.category_group_name, '') as category_group_name,
            t.transfer_account_id
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        LEFT JOIN ynab_payees p ON t.payee_id = p.id
        WHERE t.id = ? AND t.deleted = 0
    """, (transaction_id,)).fetchone()

    if not row:
        conn.close()
        return None

    txn = dict(row)

    # Attach subtransactions if any
    subs = conn.execute("""
        SELECT id,
               ROUND(amount / 1000.0, 2) as amount,
               memo, payee_id, payee_name, category_id, category_name,
               transfer_account_id
        FROM ynab_subtransactions
        WHERE transaction_id = ? AND deleted = 0
        ORDER BY id
    """, (transaction_id,)).fetchall()
    txn["subtransactions"] = [dict(s) for s in subs]

    conn.close()
    return txn


# ---------------------------------------------------------------------------
# Payees
# ---------------------------------------------------------------------------

def get_payees(limit: int = 200) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT
            p.id, p.name, p.notes,
            COUNT(t.id) as transaction_count,
            ROUND(SUM(t.amount) / 1000.0, 2) as total_amount,
            MIN(t.date) as first_transaction,
            MAX(t.date) as last_transaction,
            COUNT(DISTINCT t.category_id) as unique_categories
        FROM ynab_payees p
        LEFT JOIN ynab_transactions t ON p.id = t.payee_id AND t.deleted = 0
        WHERE p.deleted = 0
        GROUP BY p.id, p.name, p.notes
        ORDER BY transaction_count DESC, p.name ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_payee(payee_id: str) -> Optional[dict]:
    conn = get_db()

    row = conn.execute("""
        SELECT
            p.id, p.name, p.notes,
            COUNT(t.id) as transaction_count,
            ROUND(SUM(t.amount) / 1000.0, 2) as total_amount,
            ROUND(AVG(t.amount) / 1000.0, 2) as avg_amount,
            ROUND(MIN(t.amount) / 1000.0, 2) as min_amount,
            ROUND(MAX(t.amount) / 1000.0, 2) as max_amount,
            MIN(t.date) as first_transaction,
            MAX(t.date) as last_transaction,
            COUNT(DISTINCT t.category_id) as unique_categories,
            COUNT(DISTINCT t.account_id) as unique_accounts
        FROM ynab_payees p
        LEFT JOIN ynab_transactions t ON p.id = t.payee_id AND t.deleted = 0
        WHERE p.id = ? AND p.deleted = 0
        GROUP BY p.id, p.name, p.notes
    """, (payee_id,)).fetchone()

    if not row:
        conn.close()
        return None

    payee = dict(row)

    # Category breakdown
    cats = conn.execute("""
        SELECT
            COALESCE(c.name, t.category_name, 'Uncategorized') as category_name,
            COALESCE(c.category_group_name, 'Unknown') as category_group,
            COUNT(*) as transaction_count,
            ROUND(SUM(t.amount) / 1000.0, 2) as total_amount
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        WHERE t.payee_id = ? AND t.deleted = 0
        GROUP BY t.category_id, category_name, category_group
        ORDER BY transaction_count DESC
    """, (payee_id,)).fetchall()
    payee["category_breakdown"] = [dict(c) for c in cats]

    conn.close()
    return payee


# ---------------------------------------------------------------------------
# YNAB Accounts
# ---------------------------------------------------------------------------

def get_ynab_accounts(budget_id: Optional[str] = None) -> list[dict]:
    conn = get_db()
    query = """
        SELECT
            ya.ynab_account_id as id, ya.name, ya.type, ya.on_budget,
            ya.closed, ya.note, ya.budget_id,
            ROUND(ya.balance / 1000.0, 2) as balance,
            ROUND(ya.cleared_balance / 1000.0, 2) as cleared_balance,
            ROUND(ya.uncleared_balance / 1000.0, 2) as uncleared_balance,
            ya.direct_import_linked, ya.direct_import_in_error,
            ya.last_reconciled_at
        FROM ynab_account ya
        WHERE ya.deleted = 0
    """
    params: list = []
    if budget_id:
        query += " AND ya.budget_id = ?"
        params.append(budget_id)
    query += " ORDER BY ya.on_budget DESC, ya.name"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Local Accounts & Balances
# ---------------------------------------------------------------------------

def get_local_accounts() -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, parent_id, type, side, currency,
               institution, notes,
               ROUND(COALESCE(apr_bps, 0) / 100.0, 4) as apr_percent,
               ROUND(COALESCE(credit_limit_cents, 0) / 100.0, 2) as credit_limit
        FROM account
        ORDER BY type, name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_balances(account_id: Optional[str] = None) -> list[dict]:
    conn = get_db()
    query = """
        SELECT
            bs.account_id, a.name as account_name, a.type as account_type,
            a.currency, a.institution,
            bs.as_of_date,
            ROUND(bs.amount_cents / 100.0, 2) as balance,
            bs.source, bs.notes
        FROM balance_snapshot bs
        JOIN account a ON bs.account_id = a.id
        WHERE bs.as_of_date = (
            SELECT MAX(as_of_date)
            FROM balance_snapshot bs2
            WHERE bs2.account_id = bs.account_id
        )
    """
    params: list = []
    if account_id:
        query += " AND bs.account_id = ?"
        params.append(account_id)
    query += " ORDER BY a.type, a.name"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_balance_history(account_id: str) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT
            bs.as_of_date,
            ROUND(bs.amount_cents / 100.0, 2) as balance,
            bs.source, bs.notes
        FROM balance_snapshot bs
        WHERE bs.account_id = ?
        ORDER BY bs.as_of_date DESC
    """, (account_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
