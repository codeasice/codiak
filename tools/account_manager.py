import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import os

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

def get_account_balances(account_id: str = None) -> List[Dict[str, Any]]:
    """Get balance snapshots for accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if account_id:
        cursor.execute("""
            SELECT bs.account_id, bs.as_of_date, bs.amount_cents, bs.source, bs.notes,
                   a.name, a.type, a.currency
            FROM balance_snapshot bs
            JOIN account a ON bs.account_id = a.id
            WHERE bs.account_id = ?
            ORDER BY bs.as_of_date DESC
        """, (account_id,))
    else:
        cursor.execute("""
            SELECT bs.account_id, bs.as_of_date, bs.amount_cents, bs.source, bs.notes,
                   a.name, a.type, a.currency
            FROM balance_snapshot bs
            JOIN account a ON bs.account_id = a.id
            ORDER BY bs.as_of_date DESC, a.name
        """)

    balances = []
    for row in cursor.fetchall():
        balances.append({
            'account_id': row[0],
            'as_of_date': row[1],
            'amount_cents': row[2],
            'source': row[3],
            'notes': row[4],
            'account_name': row[5],
            'account_type': row[6],
            'currency': row[7]
        })

    conn.close()
    return balances

def get_latest_balances() -> List[Dict[str, Any]]:
    """Get the latest balance for each account."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bs.account_id, bs.as_of_date, bs.amount_cents, bs.source, bs.notes,
               a.name, a.type, a.currency, a.side
        FROM balance_snapshot bs
        JOIN account a ON bs.account_id = a.id
        WHERE bs.as_of_date = (
            SELECT MAX(as_of_date)
            FROM balance_snapshot bs2
            WHERE bs2.account_id = bs.account_id
        )
        ORDER BY a.type, a.name
    """)

    balances = []
    for row in cursor.fetchall():
        balances.append({
            'account_id': row[0],
            'as_of_date': row[1],
            'amount_cents': row[2],
            'source': row[3],
            'notes': row[4],
            'account_name': row[5],
            'account_type': row[6],
            'currency': row[7],
            'side': row[8]
        })

    conn.close()
    return balances

def add_account(id: str, name: str, parent_id: str, account_type: str,
                side: str, currency: str, institution: str = None,
                notes: str = None, apr_bps: int = None):
    """Add a new account to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO account (id, name, parent_id, type, side, currency, institution, notes, apr_bps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, name, parent_id, account_type, side, currency, institution, notes, apr_bps))

        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        st.error(f"Account ID '{id}' already exists!")
        return False
    except Exception as e:
        st.error(f"Error adding account: {str(e)}")
        return False
    finally:
        conn.close()

def add_balance_snapshot(account_id: str, as_of_date: str, amount_cents: int,
                        source: str = 'manual', notes: str = None):
    """Add a new balance snapshot."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR REPLACE INTO balance_snapshot (account_id, as_of_date, amount_cents, source, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (account_id, as_of_date, amount_cents, source, notes))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding balance snapshot: {str(e)}")
        return False
    finally:
        conn.close()

def format_amount(amount_cents: int, currency: str = 'USD') -> str:
    """Format amount in cents to currency string."""
    amount = amount_cents / 100.0
    if currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def render():
    st.title("💰 Account Management Tool")
    st.markdown("Manage your financial accounts and track balances over time.")

    # Check if database exists
    if not os.path.exists('accounts.db'):
        st.error("accounts.db not found! Please ensure the database file exists.")
        st.stop()

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page:", [
        "📊 Account Overview",
        "➕ Add Account",
        "💰 Add Balance",
        "📈 Balance History",
        "🔍 Account Details"
    ])

    if page == "📊 Account Overview":
        render_account_overview()
    elif page == "➕ Add Account":
        render_add_account()
    elif page == "💰 Add Balance":
        render_add_balance()
    elif page == "📈 Balance History":
        render_balance_history()
    elif page == "🔍 Account Details":
        render_account_details()

def render_account_overview():
    """Render the account overview page."""
    st.header("Account Overview")

    # Get all accounts
    accounts = get_accounts()

    if not accounts:
        st.info("No accounts found. Add some accounts to get started!")
        return

    # Get latest balances
    balances = get_latest_balances()
    balance_dict = {b['account_id']: b for b in balances}

    # Group accounts by type
    by_type = {}
    for account in accounts:
        account_type = account['type']
        if account_type not in by_type:
            by_type[account_type] = []
        by_type[account_type].append(account)

    # Calculate totals
    total_by_type = {}
    grand_total = 0
    accounts_with_balances = 0

    for account_type, type_accounts in by_type.items():
        type_total = 0
        for account in type_accounts:
            if account['id'] in balance_dict:
                balance = balance_dict[account['id']]
                amount = balance['amount_cents']
                if account['side'] == 'credit':
                    amount = -amount  # Credit accounts are liabilities, so negative for net worth
                type_total += amount
                accounts_with_balances += 1
        total_by_type[account_type] = type_total
        grand_total += type_total

    # Display summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Accounts", len(accounts))

    with col2:
        st.metric("With Balances", accounts_with_balances)

    with col3:
        st.metric("Account Types", len(by_type))

    with col4:
        st.metric("Net Worth", format_amount(int(grand_total)))

    st.markdown("---")

    # Display accounts organized by type, parent, and leaf accounts
    st.subheader("📊 Account Structure by Type and Parent")

    # Group accounts by type first
    accounts_by_type = {}
    for account in accounts:
        account_type = account['type']
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = []
        accounts_by_type[account_type].append(account)

    # Display each account type
    for account_type in sorted(accounts_by_type.keys()):
        type_accounts = accounts_by_type[account_type]

        # Calculate type total
        type_total = 0
        for account in type_accounts:
            if account['id'] in balance_dict:
                balance = balance_dict[account['id']]
                amount = balance['amount_cents']
                if account['side'] == 'credit':
                    amount = -amount
                type_total += amount

        # Type header
        st.markdown(f"### 🏷️ {account_type} - {format_amount(int(type_total))}")

        # Group by parent within this type
        parent_groups = {}
        root_accounts = []

        for account in type_accounts:
            if account['parent_id']:
                if account['parent_id'] not in parent_groups:
                    parent_groups[account['parent_id']] = []
                parent_groups[account['parent_id']].append(account)
            else:
                root_accounts.append(account)

        # Skip root accounts - don't display them

        # Display parent groups
        for parent_id in sorted(parent_groups.keys()):
            # Find parent account info
            parent_account = next((acc for acc in accounts if acc['id'] == parent_id), None)
            if not parent_account:
                continue

            parent_name = parent_account['name']
            children = parent_groups[parent_id]

            # Calculate parent total
            parent_total = 0
            for child in children:
                if child['id'] in balance_dict:
                    balance = balance_dict[child['id']]
                    amount = balance['amount_cents']
                    if child['side'] == 'credit':
                        amount = -amount
                    parent_total += amount

            # Parent subheader
            st.markdown(f"#### 📂 {parent_name} - {format_amount(int(parent_total))}")

            # Create table for leaf accounts under this parent
            leaf_table_data = []
            for account in sorted(children, key=lambda x: x['name']):
                balance_info = balance_dict.get(account['id'])
                row_data = {
                    'Account Name': account['name'],
                    'APR': f"{account['apr_bps'] / 100:.2f}%" if account['apr_bps'] else 'N/A',
                    'Credit Limit': f"${account['credit_limit_cents'] / 100:,.2f}" if account.get('credit_limit_cents') else 'N/A',
                    'Notes': account['notes'] or 'N/A'
                }

                if balance_info:
                    amount = balance_info['amount_cents']
                    if account['side'] == 'credit':
                        amount = -amount
                    row_data.update({
                        'Current Balance': format_amount(amount, account['currency']),
                        'Balance Date': balance_info['as_of_date']
                    })
                else:
                    row_data.update({
                        'Current Balance': 'No balance recorded',
                        'Balance Date': 'N/A'
                    })

                leaf_table_data.append(row_data)

            if leaf_table_data:
                df = pd.DataFrame(leaf_table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

    # Also show grouped view for quick reference
    st.markdown("---")
    st.subheader("📊 Summary by Account Type")

    for account_type, type_accounts in by_type.items():
        with st.expander(f"{account_type} ({len(type_accounts)} accounts) - {format_amount(int(total_by_type[account_type]))}"):
            for account in type_accounts:
                balance_info = balance_dict.get(account['id'])

                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{account['name']}** ({account['id']})")
                with col2:
                    if balance_info:
                        amount = balance_info['amount_cents']
                        if account['side'] == 'credit':
                            amount = -amount
                        st.write(format_amount(amount, account['currency']))
                    else:
                        st.write("No balance")
                with col3:
                    if balance_info:
                        st.write(f"As of: {balance_info['as_of_date']}")
                    else:
                        st.write("N/A")
                with col4:
                    if balance_info:
                        st.write(f"({balance_info['source']})")
                    else:
                        st.write("N/A")

def render_add_account():
    """Render the add account page."""
    st.header("Add New Account")

    with st.form("add_account_form"):
        col1, col2 = st.columns(2)

        with col1:
            account_id = st.text_input("Account ID*", help="Unique identifier (e.g., 'cash.checking')")
            account_name = st.text_input("Account Name*", help="Display name (e.g., 'Checking Account')")
            parent_id = st.text_input("Parent ID", help="Parent account ID for hierarchy (optional)")
            account_type = st.selectbox("Account Type*", ["ASSET", "LIABILITY", "INVESTMENT"])

        with col2:
            side = st.selectbox("Side*", ["debit", "credit"],
                              help="debit for assets, credit for liabilities")
            currency = st.text_input("Currency*", value="USD")
            institution = st.text_input("Institution", help="Bank or financial institution")
            apr_bps = st.number_input("APR (basis points)", min_value=0, max_value=10000,
                                     help="Annual percentage rate in basis points (100 = 1%)")

        notes = st.text_area("Notes", help="Additional notes about this account")

        submitted = st.form_submit_button("Add Account")

        if submitted:
            if not account_id or not account_name or not account_type or not side or not currency:
                st.error("Please fill in all required fields (marked with *)")
            else:
                success = add_account(
                    id=account_id,
                    name=account_name,
                    parent_id=parent_id if parent_id else None,
                    account_type=account_type,
                    side=side,
                    currency=currency,
                    institution=institution if institution else None,
                    notes=notes if notes else None,
                    apr_bps=apr_bps if apr_bps > 0 else None
                )

                if success:
                    st.success(f"Account '{account_name}' added successfully!")
                    st.rerun()

def render_add_balance():
    """Render the add balance page."""
    st.header("Add Balance Snapshot")

    # Get accounts for selection
    accounts = get_accounts()
    if not accounts:
        st.warning("No accounts found. Please add some accounts first.")
        return

    with st.form("add_balance_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Account selection
            account_options = {f"{acc['name']} ({acc['id']})": acc['id'] for acc in accounts}
            selected_account_display = st.selectbox("Account*", list(account_options.keys()))
            selected_account_id = account_options[selected_account_display]

            as_of_date = st.date_input("As of Date*", value=date.today())
            amount_dollars = st.number_input("Amount (dollars)*", min_value=0.0, step=0.01,
                                           help="Enter amount in dollars (will be converted to cents)")

        with col2:
            source = st.selectbox("Source", ["manual", "api:coinbase", "api:bank", "import"],
                                help="How this balance was obtained")
            notes = st.text_area("Notes", help="Additional notes about this balance")

        submitted = st.form_submit_button("Add Balance")

        if submitted:
            if not selected_account_id or not as_of_date or amount_dollars is None:
                st.error("Please fill in all required fields (marked with *)")
            else:
                amount_cents = int(amount_dollars * 100)
                success = add_balance_snapshot(
                    account_id=selected_account_id,
                    as_of_date=as_of_date.isoformat(),
                    amount_cents=amount_cents,
                    source=source,
                    notes=notes if notes else None
                )

                if success:
                    st.success(f"Balance of {format_amount(amount_cents)} added for {selected_account_display}!")
                    st.rerun()

def render_balance_history():
    """Render the balance history page."""
    st.header("Balance History")

    # Get accounts for filtering
    accounts = get_accounts()
    if not accounts:
        st.warning("No accounts found. Please add some accounts first.")
        return

    # Account filter
    account_options = {f"{acc['name']} ({acc['id']})": acc['id'] for acc in accounts}
    account_options["All Accounts"] = None

    selected_account_display = st.selectbox("Filter by Account", list(account_options.keys()))
    selected_account_id = account_options[selected_account_display]

    # Get balances
    balances = get_account_balances(selected_account_id)

    if not balances:
        st.info("No balance history found.")
        return

    # Convert to DataFrame for better display
    df_data = []
    for balance in balances:
        df_data.append({
            'Account': balance['account_name'],
            'Date': balance['as_of_date'],
            'Amount': format_amount(balance['amount_cents'], balance['currency']),
            'Source': balance['source'],
            'Notes': balance['notes'] or ''
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)

    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"balance_history_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def render_account_details():
    """Render the account details page."""
    st.header("Account Details")

    # Get accounts for selection
    accounts = get_accounts()
    if not accounts:
        st.warning("No accounts found. Please add some accounts first.")
        return

    # Account selection
    account_options = {f"{acc['name']} ({acc['id']})": acc for acc in accounts}
    selected_account_display = st.selectbox("Select Account", list(account_options.keys()))
    selected_account = account_options[selected_account_display]

    # Display account details
    st.subheader(f"Account Details: {selected_account['name']}")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**ID:** {selected_account['id']}")
        st.write(f"**Type:** {selected_account['type']}")
        st.write(f"**Side:** {selected_account['side']}")
        st.write(f"**Currency:** {selected_account['currency']}")

    with col2:
        st.write(f"**Institution:** {selected_account['institution'] or 'N/A'}")
        st.write(f"**Parent ID:** {selected_account['parent_id'] or 'N/A'}")
        st.write(f"**APR:** {selected_account['apr_bps'] / 100 if selected_account['apr_bps'] else 'N/A'}%")
        st.write(f"**Notes:** {selected_account['notes'] or 'N/A'}")

    # Show balance history for this account
    st.subheader("Balance History")
    balances = get_account_balances(selected_account['id'])

    if balances:
        # Create a simple chart
        import matplotlib.pyplot as plt

        dates = [datetime.strptime(b['as_of_date'], '%Y-%m-%d') for b in balances]
        amounts = [b['amount_cents'] / 100.0 for b in balances]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, amounts, marker='o')
        ax.set_title(f"Balance History - {selected_account['name']}")
        ax.set_ylabel("Amount ($)")
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)

        st.pyplot(fig)

        # Show latest balance
        latest = balances[0]
        st.metric("Latest Balance", format_amount(latest['amount_cents'], latest['currency']),
                 f"As of {latest['as_of_date']}")
    else:
        st.info("No balance history found for this account.")

if __name__ == "__main__":
    render()
