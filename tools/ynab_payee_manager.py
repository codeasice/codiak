import streamlit as st
import os
import pandas as pd
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import re

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_payees_from_db(search_term: str = "", limit: int = 100) -> List[Dict[str, Any]]:
    """Get payees from SQLite database with optional search filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query with optional search filter
    query = """
        SELECT
            p.id,
            p.name,
            p.notes,
            COUNT(t.id) as transaction_count,
            SUM(t.amount) as total_amount,
            MIN(t.date) as first_transaction,
            MAX(t.date) as last_transaction,
            COUNT(DISTINCT t.category_id) as unique_categories
        FROM ynab_payees p
        LEFT JOIN ynab_transactions t ON p.id = t.payee_id AND t.deleted = 0
        WHERE p.deleted = 0
    """

    params = []
    if search_term:
        query += " AND p.name LIKE ?"
        params.append(f"%{search_term}%")

    query += """
        GROUP BY p.id, p.name, p.notes
        ORDER BY transaction_count DESC, p.name ASC
        LIMIT ?
    """
    params.append(limit)

    cursor.execute(query, params)
    payees_data = cursor.fetchall()

    payees = []
    for payee in payees_data:
        payees.append({
            'id': payee[0],
            'name': payee[1],
            'notes': payee[2] or '',
            'transaction_count': payee[3] or 0,
            'total_amount': payee[4] or 0,
            'first_transaction': payee[5],
            'last_transaction': payee[6],
            'unique_categories': payee[7] or 0
        })

    conn.close()
    return payees

def get_payee_transactions(payee_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get transactions for a specific payee."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            t.id, t.date, t.amount, t.memo, t.cleared, t.approved,
            t.account_id, t.account_name, t.category_id, t.category_name,
            c.name as category_name_from_cat, c.category_group_name
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        WHERE t.payee_id = ? AND t.deleted = 0
        ORDER BY t.date DESC, t.id DESC
        LIMIT ?
    """

    cursor.execute(query, (payee_id, limit))
    transactions_data = cursor.fetchall()

    transactions = []
    for txn in transactions_data:
        # Use joined category name if available, fallback to stored name
        category_name = txn[10] if txn[10] else (txn[9] if txn[9] else '❓ Uncategorized')

        transactions.append({
            'id': txn[0],
            'date': txn[1],
            'amount': txn[2],
            'memo': txn[3],
            'cleared': txn[4],
            'approved': bool(txn[5]),
            'account_id': txn[6],
            'account_name': txn[7],
            'category_id': txn[8],
            'category_name': category_name,
            'category_group_name': txn[11]
        })

    conn.close()
    return transactions

def get_payee_summary(payee_id: str) -> Dict[str, Any]:
    """Get summary statistics for a specific payee."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get basic payee info including notes
    cursor.execute("SELECT name, notes FROM ynab_payees WHERE id = ?", (payee_id,))
    payee_data = cursor.fetchone()
    payee_name = payee_data[0]
    payee_notes = payee_data[1] or ''

    # Get transaction summary
    query = """
        SELECT
            COUNT(*) as total_transactions,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount,
            COUNT(DISTINCT category_id) as unique_categories,
            COUNT(DISTINCT account_id) as unique_accounts,
            MIN(date) as first_transaction,
            MAX(date) as last_transaction
        FROM ynab_transactions
        WHERE payee_id = ? AND deleted = 0
    """

    cursor.execute(query, (payee_id,))
    summary_data = cursor.fetchone()

    # Get category breakdown
    category_query = """
        SELECT
            COALESCE(c.name, t.category_name, '❓ Uncategorized') as category_name,
            COALESCE(c.category_group_name, 'Unknown') as category_group,
            COUNT(*) as transaction_count,
            SUM(t.amount) as total_amount
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        WHERE t.payee_id = ? AND t.deleted = 0
        GROUP BY t.category_id, COALESCE(c.name, t.category_name), COALESCE(c.category_group_name, 'Unknown')
        ORDER BY transaction_count DESC
    """

    cursor.execute(category_query, (payee_id,))
    category_data = cursor.fetchall()

    conn.close()

    return {
        'id': payee_id,
        'name': payee_name,
        'notes': payee_notes,
        'total_transactions': summary_data[0] or 0,
        'total_amount': summary_data[1] or 0,
        'avg_amount': summary_data[2] or 0,
        'min_amount': summary_data[3] or 0,
        'max_amount': summary_data[4] or 0,
        'unique_categories': summary_data[5] or 0,
        'unique_accounts': summary_data[6] or 0,
        'first_transaction': summary_data[7],
        'last_transaction': summary_data[8],
        'category_breakdown': [
            {
                'category_name': cat[0],
                'category_group': cat[1],
                'transaction_count': cat[2],
                'total_amount': cat[3]
            }
            for cat in category_data
        ]
    }

def update_payee_notes(payee_id: str, notes: str) -> bool:
    """Update notes for a specific payee."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE ynab_payees SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (notes, payee_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating payee notes: {e}")
        return False
    finally:
        conn.close()

def render():
    """Main render function for the YNAB Payee Manager tool."""
    st.title("🏪 YNAB Payee Manager")
    st.write("Browse and analyze payees with filtering and transaction details.")

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

    # Search and filter controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input(
            "🔍 Search payees:",
            placeholder="Enter payee name to filter...",
            help="Filter payees by name (case-insensitive)"
        )

    with col2:
        limit = st.number_input(
            "Show limit:",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            help="Maximum number of payees to display"
        )

    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer
        load_payees = st.button("📊 Load Payees", type="primary")

    # Load and display payees
    if load_payees or search_term:
        with st.spinner("Loading payees from database..."):
            try:
                payees = get_payees_from_db(search_term, limit)

                if not payees:
                    st.warning("No payees found matching your criteria.")
                    return

                st.success(f"✅ **Found {len(payees)} payees!**")

                # Display payees summary
                st.subheader("📋 Payees Summary")

                # Create summary metrics
                col1, col2, col3, col4 = st.columns(4)

                total_transactions = sum(p['transaction_count'] for p in payees)
                total_amount = sum(p['total_amount'] for p in payees)
                avg_transactions = total_transactions / len(payees) if payees else 0
                payees_with_transactions = len([p for p in payees if p['transaction_count'] > 0])

                with col1:
                    st.metric("Total Payees", len(payees))
                with col2:
                    st.metric("Total Transactions", total_transactions)
                with col3:
                    st.metric("Total Amount", f"${total_amount/1000:.2f}")
                with col4:
                    st.metric("Avg Transactions/Payee", f"{avg_transactions:.1f}")

                # Create payees table
                table_data = []
                for payee in payees:
                    # Format amount with proper sign
                    amount_display = f"${payee['total_amount']/1000:.2f}"
                    if payee['total_amount'] < 0:
                        amount_display = f"-${abs(payee['total_amount'])/1000:.2f}"

                    # Format dates
                    first_date = payee['first_transaction'] or 'N/A'
                    last_date = payee['last_transaction'] or 'N/A'

                    if first_date != 'N/A':
                        try:
                            first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass

                    if last_date != 'N/A':
                        try:
                            last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass

                    # Show notes preview (first 50 chars)
                    notes_preview = payee['notes'][:50] + "..." if len(payee['notes']) > 50 else payee['notes']
                    notes_display = notes_preview if payee['notes'] else "No notes"

                    table_data.append({
                        'Name': payee['name'],
                        'Notes': notes_display,
                        'Transactions': payee['transaction_count'],
                        'Total Amount': amount_display,
                        'Categories': payee['unique_categories'],
                        'First Transaction': first_date,
                        'Last Transaction': last_date,
                        'Actions': f"View Details"
                    })

                if table_data:
                    df = pd.DataFrame(table_data)

                    # Add clickable rows for payee details
                    for idx, row in df.iterrows():
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 2, 1, 1, 1, 1, 1, 1])

                        with col1:
                            st.write(f"**{row['Name']}**")

                        with col2:
                            st.write(f"_{row['Notes']}_")

                        with col3:
                            st.write(f"{row['Transactions']}")

                        with col4:
                            st.write(row['Total Amount'])

                        with col5:
                            st.write(f"{row['Categories']}")

                        with col6:
                            st.write(row['First Transaction'])

                        with col7:
                            st.write(row['Last Transaction'])

                        with col8:
                            if st.button("🔍 View", key=f"view_{payees[idx]['id']}"):
                                st.session_state.selected_payee_id = payees[idx]['id']
                                st.session_state.selected_payee_name = payees[idx]['name']
                                st.rerun()

                else:
                    st.info("No payees found.")

            except Exception as e:
                st.error(f"❌ **Error loading payees**: {str(e)}")

    # Payee details section
    if 'selected_payee_id' in st.session_state:
        st.write("---")
        st.subheader(f"🔍 Payee Details: {st.session_state.selected_payee_name}")

        with st.spinner("Loading payee details..."):
            try:
                # Get payee summary
                summary = get_payee_summary(st.session_state.selected_payee_id)

                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Transactions", summary['total_transactions'])
                with col2:
                    st.metric("Total Amount", f"${summary['total_amount']/1000:.2f}")
                with col3:
                    st.metric("Average Amount", f"${summary['avg_amount']/1000:.2f}")
                with col4:
                    st.metric("Unique Categories", summary['unique_categories'])

                # Notes section
                st.subheader("📝 Notes")
                notes_key = f"notes_{summary['id']}"

                # Initialize notes in session state if not present
                if notes_key not in st.session_state:
                    st.session_state[notes_key] = summary['notes']

                # Notes text area
                new_notes = st.text_area(
                    "Payee Notes:",
                    value=st.session_state[notes_key],
                    height=100,
                    key=f"notes_textarea_{summary['id']}",
                    help="Add notes about this payee (e.g., business type, location, etc.)"
                )

                # Update notes button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾 Save Notes", key=f"save_notes_{summary['id']}"):
                        if update_payee_notes(summary['id'], new_notes):
                            st.session_state[notes_key] = new_notes
                            st.success("✅ Notes saved successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save notes")

                with col2:
                    if st.button("🔄 Reset Notes", key=f"reset_notes_{summary['id']}"):
                        st.session_state[notes_key] = summary['notes']
                        st.rerun()

                # Amount range
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Min Amount", f"${summary['min_amount']/1000:.2f}")
                with col2:
                    st.metric("Max Amount", f"${summary['max_amount']/1000:.2f}")

                # Date range
                col1, col2 = st.columns(2)
                with col1:
                    first_date = summary['first_transaction']
                    if first_date:
                        try:
                            first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass
                    st.metric("First Transaction", first_date or 'N/A')

                with col2:
                    last_date = summary['last_transaction']
                    if last_date:
                        try:
                            last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass
                    st.metric("Last Transaction", last_date or 'N/A')

                # Category breakdown
                st.subheader("📊 Category Breakdown")
                if summary['category_breakdown']:
                    category_data = []
                    for cat in summary['category_breakdown']:
                        amount_display = f"${cat['total_amount']/1000:.2f}"
                        if cat['total_amount'] < 0:
                            amount_display = f"-${abs(cat['total_amount'])/1000:.2f}"

                        category_data.append({
                            'Category': cat['category_name'],
                            'Group': cat['category_group'],
                            'Transactions': cat['transaction_count'],
                            'Total Amount': amount_display
                        })

                    cat_df = pd.DataFrame(category_data)
                    st.dataframe(cat_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No category data available.")

                # Recent transactions
                st.subheader("💳 Recent Transactions")
                transactions = get_payee_transactions(st.session_state.selected_payee_id, 20)

                if transactions:
                    transaction_data = []
                    for txn in transactions:
                        amount_display = f"${txn['amount']/1000:.2f}"
                        if txn['amount'] < 0:
                            amount_display = f"-${abs(txn['amount'])/1000:.2f}"

                        date_display = txn['date']
                        try:
                            date_display = datetime.fromisoformat(txn['date'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                        except:
                            pass

                        transaction_data.append({
                            'Date': date_display,
                            'Amount': amount_display,
                            'Category': txn['category_name'],
                            'Account': txn['account_name'],
                            'Memo': txn['memo'] or '',
                            'Cleared': '✅' if txn['cleared'] else '❌',
                            'Approved': '✅' if txn['approved'] else '❌'
                        })

                    txn_df = pd.DataFrame(transaction_data)
                    st.dataframe(txn_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No transactions found for this payee.")

                # Close button
                if st.button("❌ Close Details"):
                    del st.session_state.selected_payee_id
                    del st.session_state.selected_payee_name
                    st.rerun()

            except Exception as e:
                st.error(f"❌ **Error loading payee details**: {str(e)}")

    # Data source information
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Browse all payees in your YNAB budget with search filtering
        - View detailed statistics for each payee
        - See transaction history and category breakdowns
        - Analyze spending patterns by payee

        **Features:**
        - **Search filtering**: Find payees by name
        - **Transaction counts**: See how many transactions per payee
        - **Amount totals**: View total spending per payee
        - **Category analysis**: See which categories each payee uses
        - **Date ranges**: First and last transaction dates
        - **Recent transactions**: View latest transactions for selected payee

        **Data Source:**
        - **SQLite Database**: Reads from ynab_payees, ynab_transactions, and ynab_categories tables
        - **No API calls**: Faster loading and no rate limits
        - **Offline capable**: Works without internet connection

        **Requirements:**
        - Database must contain YNAB data (imported via YNAB Export Data tool)
        - YNAB tables must exist in the database
        """)
