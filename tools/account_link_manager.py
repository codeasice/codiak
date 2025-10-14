import streamlit as st
import sqlite3
from typing import List, Dict, Any

def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect('accounts.db')

def get_unlinked_accounts() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Get accounts that are not currently linked."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all accounts
    cursor.execute("""
        SELECT id, name, type, institution, parent_id
        FROM account
        ORDER BY type, name
    """)

    all_accounts = []
    for row in cursor.fetchall():
        all_accounts.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'institution': row[3],
            'parent_id': row[4]
        })

    # Get all YNAB accounts
    cursor.execute("""
        SELECT budget_id, ynab_account_id, name, type, balance
        FROM ynab_account
        ORDER BY type, name
    """)

    all_ynab_accounts = []
    for row in cursor.fetchall():
        all_ynab_accounts.append({
            'budget_id': row[0],
            'ynab_account_id': row[1],
            'name': row[2],
            'type': row[3],
            'balance': row[4]
        })

    # Get currently linked account IDs
    cursor.execute("SELECT account_id FROM account_link_ynab")
    linked_account_ids = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT ynab_account_id FROM account_link_ynab")
    linked_ynab_ids = {row[0] for row in cursor.fetchall()}

    # Filter to unlinked accounts
    unlinked_accounts = [acc for acc in all_accounts if acc['id'] not in linked_account_ids]
    unlinked_ynab_accounts = [acc for acc in all_ynab_accounts if acc['ynab_account_id'] not in linked_ynab_ids]

    conn.close()
    return unlinked_accounts, unlinked_ynab_accounts

def get_all_accounts() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, type, institution, parent_id
        FROM account
        ORDER BY type, name
    """)

    accounts = []
    for row in cursor.fetchall():
        accounts.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'institution': row[3],
            'parent_id': row[4]
        })

    conn.close()
    return accounts

def get_all_ynab_accounts() -> List[Dict[str, Any]]:
    """Get all YNAB accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT budget_id, ynab_account_id, name, type, balance
        FROM ynab_account
        ORDER BY type, name
    """)

    ynab_accounts = []
    for row in cursor.fetchall():
        ynab_accounts.append({
            'budget_id': row[0],
            'ynab_account_id': row[1],
            'name': row[2],
            'type': row[3],
            'balance': row[4]
        })

    conn.close()
    return ynab_accounts

def get_existing_links() -> List[Dict[str, Any]]:
    """Get all existing account links."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT l.account_id, l.budget_id, l.ynab_account_id,
               a.name as account_name, a.type as account_type,
               y.name as ynab_name, y.type as ynab_type
        FROM account_link_ynab l
        LEFT JOIN account a ON l.account_id = a.id
        LEFT JOIN ynab_account y ON l.ynab_account_id = y.ynab_account_id
        ORDER BY a.name, y.name
    """)

    links = []
    for row in cursor.fetchall():
        links.append({
            'account_id': row[0],
            'budget_id': row[1],
            'ynab_account_id': row[2],
            'account_name': row[3] or 'Unknown Account',
            'account_type': row[4] or 'Unknown',
            'ynab_name': row[5] or 'Unknown YNAB Account',
            'ynab_type': row[6] or 'Unknown'
        })

    conn.close()
    return links

def add_account_link(account_id: str, budget_id: str, ynab_account_id: str) -> bool:
    """Add a new account link."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if link already exists
        cursor.execute("""
            SELECT COUNT(*) FROM account_link_ynab
            WHERE account_id = ? AND ynab_account_id = ?
        """, (account_id, ynab_account_id))

        if cursor.fetchone()[0] > 0:
            conn.close()
            return False  # Link already exists

        # Insert new link
        cursor.execute("""
            INSERT INTO account_link_ynab (account_id, budget_id, ynab_account_id)
            VALUES (?, ?, ?)
        """, (account_id, budget_id, ynab_account_id))

        conn.commit()
        conn.close()
        return True

    except (sqlite3.Error, IOError) as e:
        st.error(f"Error adding link: {e}")
        return False

def delete_account_link(account_id: str, ynab_account_id: str) -> bool:
    """Delete an account link."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM account_link_ynab
            WHERE account_id = ? AND ynab_account_id = ?
        """, (account_id, ynab_account_id))

        conn.commit()
        conn.close()
        return True

    except (sqlite3.Error, IOError) as e:
        st.error(f"Error deleting link: {e}")
        return False

def render():
    """Main render function for the Account Link Manager tool."""
    st.title("🔗 Account Link Manager")
    st.write("Manage links between your local accounts and YNAB accounts.")

    # Check if database exists
    try:
        conn = get_db_connection()
        conn.close()
    except (sqlite3.Error, IOError) as e:
        st.error(f"❌ **Database Error**: {e}")
        return

    # Get all data
    accounts = get_all_accounts()
    ynab_accounts = get_all_ynab_accounts()
    existing_links = get_existing_links()
    unlinked_accounts, unlinked_ynab_accounts = get_unlinked_accounts()

    if not accounts:
        st.error("❌ **No accounts found** in the account table.")
        return

    if not ynab_accounts:
        st.error("❌ **No YNAB accounts found** in the ynab_account table.")
        return

    # Show summary
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Local Accounts", len(accounts))
    with col2:
        st.metric("YNAB Accounts", len(ynab_accounts))
    with col3:
        st.metric("Existing Links", len(existing_links))
    with col4:
        st.metric("Unlinked Local", len(unlinked_accounts))
    with col5:
        st.metric("Unlinked YNAB", len(unlinked_ynab_accounts))

    st.markdown("---")

    # Existing Links Section
    st.subheader("📋 Existing Account Links")

    if existing_links:
        st.write(f"Found {len(existing_links)} existing links:")

        # Create a dataframe for better display
        import pandas as pd

        # Display with delete buttons
        for i, link in enumerate(existing_links):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 1])

            with col1:
                st.write(f"**{link['account_name']}**")
                st.caption(f"{link['account_type']} | {link['account_id']}")

            with col2:
                st.write(f"**{link['ynab_name']}**")
                st.caption(f"{link['ynab_type']} | {link['ynab_account_id'][:8]}...")

            with col3:
                st.write("")  # Spacer

            with col4:
                if st.button("🗑️ Delete", key=f"delete_{i}", help="Delete this link"):
                    if delete_account_link(link['account_id'], link['ynab_account_id']):
                        st.success("✅ Link deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete link")
    else:
        st.info("No existing account links found.")

    st.markdown("---")

    # Add New Link Section
    st.subheader("➕ Add New Account Link")

    # Check if there are unlinked accounts available
    if not unlinked_accounts:
        st.warning("⚠️ **No unlinked local accounts available** - all local accounts are already linked!")
        return

    if not unlinked_ynab_accounts:
        st.warning("⚠️ **No unlinked YNAB accounts available** - all YNAB accounts are already linked!")
        return

    # Get budget ID (assuming all YNAB accounts use the same budget)
    budget_id = unlinked_ynab_accounts[0]['budget_id'] if unlinked_ynab_accounts else None

    if budget_id:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Select Local Account:**")

            # Create account options with better display (only unlinked accounts)
            account_options = {}
            for account in unlinked_accounts:
                display_name = f"{account['name']} ({account['type']})"
                if account['institution']:
                    display_name += f" - {account['institution']}"
                account_options[display_name] = account['id']

            selected_account_display = st.selectbox(
                "Choose local account:",
                options=list(account_options.keys()),
                key="account_select",
                help="Select the local account to link (only unlinked accounts shown)"
            )

            selected_account_id = account_options[selected_account_display]

        with col2:
            st.write("**Select YNAB Account:**")

            # Create YNAB account options (only unlinked accounts)
            ynab_options = {}
            for ynab_account in unlinked_ynab_accounts:
                display_name = f"{ynab_account['name']} ({ynab_account['type']})"
                balance_display = f"${ynab_account['balance']/1000:.2f}" if ynab_account['balance'] else "$0.00"
                display_name += f" - {balance_display}"
                ynab_options[display_name] = ynab_account['ynab_account_id']

            selected_ynab_display = st.selectbox(
                "Choose YNAB account:",
                options=list(ynab_options.keys()),
                key="ynab_select",
                help="Select the YNAB account to link (only unlinked accounts shown)"
            )

            selected_ynab_id = ynab_options[selected_ynab_display]

        # Show preview
        st.write("**Link Preview:**")
        col1, col2, col3 = st.columns([2, 1, 2])

        with col1:
            st.write(f"Local: {selected_account_display}")

        with col2:
            st.write("→")

        with col3:
            st.write(f"YNAB: {selected_ynab_display}")

        # Add button
        if st.button("🔗 Add Link", type="primary"):
            # Check if link already exists
            existing_link_ids = [(link['account_id'], link['ynab_account_id']) for link in existing_links]

            if (selected_account_id, selected_ynab_id) in existing_link_ids:
                st.warning("⚠️ This link already exists!")
            else:
                if add_account_link(selected_account_id, budget_id, selected_ynab_id):
                    st.success("✅ Link added successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add link")

    else:
        st.error("❌ No budget ID found in YNAB accounts")

    # Help section
    with st.expander("ℹ️ About Account Links"):
        st.markdown("""
        **What are Account Links?**

        Account links connect your local account management system with YNAB accounts. This allows:

        - **Data synchronization** between systems
        - **Unified reporting** across both platforms
        - **Balance reconciliation** between local and YNAB data
        - **Transaction matching** and analysis

        **How to use:**

        1. **View existing links** in the table above
        2. **Delete unwanted links** using the delete buttons
        3. **Add new links** by selecting from unlinked accounts only
        4. **Review carefully** before adding links to avoid duplicates

        **Smart Filtering:**

        - **Unlinked accounts only**: Dropdowns only show accounts that aren't already linked
        - **Prevents duplicates**: Can't accidentally create duplicate links
        - **Clear availability**: See exactly which accounts are available for linking

        **Best practices:**

        - Link accounts that represent the same financial instrument
        - Use descriptive account names for easier identification
        - Regularly review and clean up unused links
        - Test links with small transactions first

        **Account Types:**

        - **ASSET** accounts (checking, savings) link to YNAB checking/savings accounts
        - **LIABILITY** accounts (credit cards, loans) link to YNAB creditCard/loan accounts
        """)

    # Debug information
    if st.checkbox("🔧 Show Debug Information"):
        st.subheader("Debug Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Local Accounts:**")
            for account in accounts[:5]:  # Show first 5
                st.write(f"• {account['id']}: {account['name']} ({account['type']})")
            if len(accounts) > 5:
                st.write(f"... and {len(accounts) - 5} more")

        with col2:
            st.write("**YNAB Accounts:**")
            for ynab_account in ynab_accounts[:5]:  # Show first 5
                st.write(f"• {ynab_account['ynab_account_id'][:8]}...: {ynab_account['name']} ({ynab_account['type']})")
            if len(ynab_accounts) > 5:
                st.write(f"... and {len(ynab_accounts) - 5} more")

if __name__ == "__main__":
    render()
