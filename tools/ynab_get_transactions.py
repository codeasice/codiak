import streamlit as st
import os
import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_transactions_from_db(budget_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get transactions from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query with optional budget filter
    query = """
        SELECT t.id, t.date, t.amount, t.memo, t.cleared, t.approved,
               t.account_id, t.account_name, t.payee_id, t.payee_name,
               t.category_id, t.category_name, t.transfer_account_id,
               c.name as category_name_from_cat, c.category_group_name,
               p.name as payee_name_from_payees
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        LEFT JOIN ynab_payees p ON t.payee_id = p.id
        WHERE t.deleted = 0
    """

    params = []
    if budget_id:
        # Filter by budget if we can determine it from accounts
        query += " AND EXISTS (SELECT 1 FROM ynab_account ya WHERE ya.ynab_account_id = t.account_id AND ya.budget_id = ?)"
        params.append(budget_id)

    query += " ORDER BY t.date DESC, t.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    transactions_data = cursor.fetchall()

    transactions = []
    for txn in transactions_data:
        # Use joined category name if available, fallback to stored name
        category_name = txn[13] if txn[13] else (txn[11] if txn[11] else '❓ Uncategorized')

        # Use joined payee name if available, fallback to stored name
        payee_name = txn[15] if txn[15] else (txn[9] if txn[9] else 'Unknown Payee')

        transactions.append({
            'id': txn[0],
            'date': txn[1],
            'amount': txn[2],
            'memo': txn[3],
            'cleared': txn[4],
            'approved': bool(txn[5]),
            'account_id': txn[6],
            'account_name': txn[7],
            'payee_id': txn[8],
            'payee_name': payee_name,
            'category_id': txn[10],
            'category_name': category_name,
            'transfer_account_id': txn[12],
            'category_group_name': txn[14]
        })

    conn.close()
    return transactions

def get_budgets_from_db() -> List[Dict[str, Any]]:
    """Get budgets from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, last_modified_on FROM ynab_budgets")
    budgets_data = cursor.fetchall()

    budgets = []
    for budget in budgets_data:
        budgets.append({
            'id': budget[0],
            'name': budget[1],
            'last_modified_on': budget[2]
        })

    conn.close()
    return budgets

def render():
    st.title("💳 Transactions")
    st.write("View your YNAB transactions from the database.")

    # Check if database exists
    if not os.path.exists('accounts.db'):
        st.error("❌ **Database not found**")
        st.markdown("""
        The accounts.db file doesn't exist. Please:

        1. **Create the database** using the account management tools
        2. **Import YNAB data** using the YNAB Export Data tool
        """)
        return

    # Check if YNAB tables exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ynab_%'")
    ynab_tables = cursor.fetchall()
    conn.close()

    if not ynab_tables:
        st.error("❌ **No YNAB tables found in database**")
        st.markdown("""
        No YNAB tables found in the database. Please:

        1. **Import YNAB data** using the YNAB Export Data tool
        2. **Or use the live API** version of this tool
        """)
        return

    st.success(f"✅ **Found YNAB tables in database** ({len(ynab_tables)} tables)")

    # Get budgets for selection
    budgets = get_budgets_from_db()

    if not budgets:
        st.warning("No budgets found in database. Please import YNAB data first.")
        return

    # Budget selection
    budget_options = {budget['name']: budget['id'] for budget in budgets}
    selected_budget_name = st.selectbox(
        "Select a budget:",
        options=list(budget_options.keys()),
        help="Choose which budget's transactions to view"
    )

    selected_budget_id = budget_options[selected_budget_name]

    # Transaction limit
    col1, col2 = st.columns([1, 1])
    with col1:
        limit = st.number_input(
            "Number of transactions to show:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Limit the number of transactions displayed"
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        load_transactions = st.button("📊 Load Transactions from Database", type="primary")

    # Move the transaction loading logic outside of columns
    if load_transactions:
        with st.spinner("Loading transactions from database..."):
            try:
                transactions = get_transactions_from_db(selected_budget_id, limit)

                if not transactions:
                    st.warning("No transactions found for this budget.")
                    return

                st.success(f"✅ **Loaded {len(transactions)} transactions!**")

                # Display transactions summary
                st.subheader("📋 Transactions Summary")

                # Create summary metrics
                col1, col2, col3, col4 = st.columns(4)

                total_amount = sum(txn['amount'] for txn in transactions)
                cleared_count = len([txn for txn in transactions if txn['cleared']])
                approved_count = len([txn for txn in transactions if txn['approved']])
                unique_payees = len(set(txn['payee_name'] for txn in transactions if txn['payee_name']))

                with col1:
                    st.metric("Total Amount", f"${total_amount/1000:.2f}")
                with col2:
                    st.metric("Cleared", cleared_count)
                with col3:
                    st.metric("Approved", approved_count)
                with col4:
                    st.metric("Unique Payees", unique_payees)

                # Create transactions table
                table_data = []
                for txn in transactions:
                    # Format amount with proper sign
                    amount_display = f"${txn['amount']/1000:.2f}"
                    if txn['amount'] < 0:
                        amount_display = f"-${abs(txn['amount'])/1000:.2f}"

                    # Format date
                    try:
                        date_obj = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
                        date_display = date_obj.strftime('%Y-%m-%d')
                    except:
                        date_display = txn['date']

                    table_data.append({
                        'Date': date_display,
                        'Payee': txn['payee_name'],
                        'Amount': amount_display,
                        'Category': txn['category_name'],
                        'Account': txn['account_name'],
                        'Memo': txn['memo'] or '',
                        'Cleared': '✅' if txn['cleared'] else '❌',
                        'Approved': '✅' if txn['approved'] else '❌'
                    })

                if table_data:
                    df = pd.DataFrame(table_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No transactions found.")

            except Exception as e:
                st.error(f"❌ **Error loading transactions**: {str(e)}")

    # Data source information
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Loads YNAB transactions from the SQLite database
        - Shows transaction details with proper formatting
        - Displays summary metrics and transaction counts
        - Provides filtering by budget and transaction limit

        **Data Source:**
        - **SQLite Database**: Reads from ynab_transactions, ynab_categories, and ynab_payees tables
        - **No API calls**: Faster loading and no rate limits
        - **Offline capable**: Works without internet connection

        **Requirements:**
        - Database must contain YNAB data (imported via YNAB Export Data tool)
        - YNAB tables must exist in the database

        **Transaction Information Displayed:**
        - Transaction date and amount
        - Payee and category names (with proper joins)
        - Account information
        - Memo and status (cleared/approved)
        - Summary metrics and counts
        """)