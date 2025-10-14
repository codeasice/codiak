import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_accounts() -> List[Dict[str, Any]]:
    """Get all accounts from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, parent_id, type, side, currency, institution, notes, apr_bps, credit_limit_cents
        FROM account
        ORDER BY type, name
    """)

    accounts = []
    for row in cursor.fetchall():
        accounts.append({
            'id': row[0],
            'name': row[1],
            'parent_id': row[2],
            'type': row[3],
            'side': row[4],
            'currency': row[5],
            'institution': row[6],
            'notes': row[7],
            'apr_bps': row[8],
            'credit_limit_cents': row[9]
        })

    conn.close()
    return accounts

def get_account_by_id(account_id: str) -> Dict[str, Any]:
    """Get a specific account by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, parent_id, type, side, currency, institution, notes, apr_bps, credit_limit_cents
        FROM account
        WHERE id = ?
    """, (account_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'name': row[1],
            'parent_id': row[2],
            'type': row[3],
            'side': row[4],
            'currency': row[5],
            'institution': row[6],
            'notes': row[7],
            'apr_bps': row[8],
            'credit_limit_cents': row[9]
        }
    return None

def update_account(account_id: str, updates: Dict[str, Any]) -> bool:
    """Update an account with new values."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        set_clauses = []
        values = []

        for key, value in updates.items():
            if key != 'id':  # Don't update the ID
                set_clauses.append(f"{key} = ?")
                values.append(value)

        if not set_clauses:
            conn.close()
            return False

        values.append(account_id)
        query = f"UPDATE account SET {', '.join(set_clauses)} WHERE id = ?"

        cursor.execute(query, values)
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error updating account: {e}")
        return False

def delete_account(account_id: str) -> bool:
    """Delete an account."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if account has children
        cursor.execute("SELECT COUNT(*) FROM account WHERE parent_id = ?", (account_id,))
        child_count = cursor.fetchone()[0]

        if child_count > 0:
            st.error(f"Cannot delete account '{account_id}' - it has {child_count} child account(s). Delete children first.")
            conn.close()
            return False

        # Check if account has balance snapshots
        cursor.execute("SELECT COUNT(*) FROM balance_snapshot WHERE account_id = ?", (account_id,))
        balance_count = cursor.fetchone()[0]

        if balance_count > 0:
            st.warning(f"Account '{account_id}' has {balance_count} balance snapshot(s). These will be deleted.")

        # Delete balance snapshots first (foreign key constraint)
        cursor.execute("DELETE FROM balance_snapshot WHERE account_id = ?", (account_id,))

        # Delete the account
        cursor.execute("DELETE FROM account WHERE id = ?", (account_id,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Error deleting account: {e}")
        return False

def render():
    """Main render function for the Account Manager tool."""
    st.title("🏦 Account Manager")
    st.write("List, view, and edit your financial accounts.")

    # Check if database exists
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        st.error(f"❌ **Database Error**: {e}")
        return

    # Get all accounts
    accounts = get_accounts()

    if not accounts:
        st.info("No accounts found. Add some accounts to get started!")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Accounts", len(accounts))

    with col2:
        account_types = len(set(acc['type'] for acc in accounts))
        st.metric("Account Types", account_types)

    with col3:
        accounts_with_parents = len([acc for acc in accounts if acc['parent_id']])
        st.metric("With Parents", accounts_with_parents)

    with col4:
        root_accounts = len([acc for acc in accounts if not acc['parent_id']])
        st.metric("Root Accounts", root_accounts)

    st.markdown("---")

    # Account selection and editing
    st.subheader("📝 Edit Account")

    # Account selection dropdown
    account_options = {}
    for account in accounts:
        display_name = f"{account['name']} ({account['type']})"
        if account['parent_id']:
            parent_account = next((acc for acc in accounts if acc['id'] == account['parent_id']), None)
            if parent_account:
                display_name += f" - Parent: {parent_account['name']}"
        account_options[display_name] = account['id']

    selected_account_display = st.selectbox(
        "Select account to edit:",
        options=list(account_options.keys()),
        key="account_select"
    )

    selected_account_id = account_options[selected_account_display]
    selected_account = get_account_by_id(selected_account_id)

    if selected_account:
        st.markdown("---")

        # Account details form
        with st.form("edit_account_form"):
            st.write(f"**Editing: {selected_account['name']}**")

            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Account Name", value=selected_account['name'])
                new_type = st.selectbox(
                    "Account Type",
                    options=["ASSET", "LIABILITY", "INVESTMENT", "EQUITY"],
                    index=["ASSET", "LIABILITY", "INVESTMENT", "EQUITY"].index(selected_account['type'])
                )
                new_side = st.selectbox(
                    "Account Side",
                    options=["debit", "credit"],
                    index=["debit", "credit"].index(selected_account['side'])
                )
                new_currency = st.text_input("Currency", value=selected_account['currency'] or "USD")

            with col2:
                # Parent selection
                parent_options = {None: "No Parent"}
                for account in accounts:
                    if account['id'] != selected_account_id:  # Can't be parent of itself
                        parent_options[account['id']] = f"{account['name']} ({account['type']})"

                current_parent = selected_account['parent_id']
                parent_display_options = list(parent_options.keys())
                parent_display_values = list(parent_options.values())

                try:
                    current_parent_index = parent_display_options.index(current_parent)
                except ValueError:
                    current_parent_index = 0

                new_parent_id = st.selectbox(
                    "Parent Account",
                    options=parent_display_options,
                    index=current_parent_index,
                    format_func=lambda x: parent_options[x]
                )

                new_institution = st.text_input("Institution", value=selected_account['institution'] or "")
                new_notes = st.text_area("Notes", value=selected_account['notes'] or "")

            # Financial details
            st.write("**Financial Details**")
            col3, col4 = st.columns(2)

            with col3:
                current_apr = selected_account['apr_bps'] / 100 if selected_account['apr_bps'] else 0.0
                new_apr = st.number_input(
                    "APR (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=current_apr,
                    step=0.01,
                    format="%.2f"
                )

            with col4:
                current_limit = selected_account['credit_limit_cents'] / 100 if selected_account['credit_limit_cents'] else 0.0
                new_limit = st.number_input(
                    "Credit Limit ($)",
                    min_value=0.0,
                    value=current_limit,
                    step=100.0,
                    format="%.2f"
                )

            # Submit buttons
            col5, col6, col7 = st.columns([1, 1, 1])

            with col5:
                update_clicked = st.form_submit_button("💾 Update Account", type="primary")

            with col6:
                delete_clicked = st.form_submit_button("🗑️ Delete Account", type="secondary")

            # Handle form submissions
            if update_clicked:
                updates = {
                    'name': new_name,
                    'type': new_type,
                    'side': new_side,
                    'currency': new_currency,
                    'parent_id': new_parent_id,
                    'institution': new_institution if new_institution else None,
                    'notes': new_notes if new_notes else None,
                    'apr_bps': int(new_apr * 100) if new_apr > 0 else None,
                    'credit_limit_cents': int(new_limit * 100) if new_limit > 0 else None
                }

                if update_account(selected_account_id, updates):
                    st.success("✅ Account updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update account")

            if delete_clicked:
                if delete_account(selected_account_id):
                    st.success("✅ Account deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete account")

    st.markdown("---")

    # Account list view
    st.subheader("📋 All Accounts")

    # Create dataframe for display
    df_data = []
    for account in accounts:
        parent_name = "None"
        if account['parent_id']:
            parent_account = next((acc for acc in accounts if acc['id'] == account['parent_id']), None)
            if parent_account:
                parent_name = parent_account['name']

        df_data.append({
            'ID': account['id'],
            'Name': account['name'],
            'Type': account['type'],
            'Side': account['side'],
            'Currency': account['currency'],
            'Parent': parent_name,
            'Institution': account['institution'] or 'N/A',
            'APR (%)': f"{account['apr_bps'] / 100:.2f}" if account['apr_bps'] else 'N/A',
            'Credit Limit': f"${account['credit_limit_cents'] / 100:,.2f}" if account['credit_limit_cents'] else 'N/A',
            'Notes': account['notes'] or 'N/A'
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Help section
    with st.expander("ℹ️ About Account Manager"):
        st.markdown("""
        **What this tool does:**

        - **List all accounts**: View all your financial accounts in a table
        - **Edit account details**: Update account information, hierarchy, and financial details
        - **Delete accounts**: Remove accounts (with safety checks)
        - **Manage hierarchy**: Set parent-child relationships between accounts

        **Account Types:**

        - **ASSET**: Things you own (checking, savings, investments)
        - **LIABILITY**: Things you owe (credit cards, loans, mortgages)
        - **INVESTMENT**: Investment accounts (401k, IRA, brokerage)
        - **EQUITY**: Owner's equity accounts

        **Account Sides:**

        - **Debit**: Assets and expenses (increases with debits)
        - **Credit**: Liabilities and income (increases with credits)

        **Safety Features:**

        - Cannot delete accounts that have children
        - Warns about deleting accounts with balance history
        - Prevents setting account as its own parent
        """)

if __name__ == "__main__":
    render()