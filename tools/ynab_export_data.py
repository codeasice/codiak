import streamlit as st
import os
import json
import sqlite3
from datetime import datetime, date
from typing import Dict, Any

# Import ynab only when needed to avoid import errors
try:
    import ynab
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_ynab_client():
    """Get configured YNAB API client."""
    if not YNAB_AVAILABLE:
        st.error("YNAB module not available. Please install it with: pip install ynab")
        st.stop()

    ynab_api_key = os.getenv('YNAB_API_KEY')
    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    configuration = ynab.Configuration(access_token=ynab_api_key)
    return configuration

def get_budget_selection():
    """Get budget selection from user."""
    configuration = get_ynab_client()

    with ynab.ApiClient(configuration) as api_client:
        budgets_api = ynab.api.budgets_api.BudgetsApi(api_client)
        budgets_response = budgets_api.get_budgets()

        budgets = budgets_response.data.budgets
        budget_names = [budget.name for budget in budgets]
        selected_budget_name = st.selectbox("Select a budget", budget_names)
        selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]
        return selected_budget_id, configuration, selected_budget_name

def fetch_all_ynab_data(budget_id: str, configuration) -> Dict[str, Any]:
    """Fetch all YNAB data for a budget."""
    with ynab.ApiClient(configuration) as api_client:
        # Fetch budgets
        budgets_api = ynab.api.budgets_api.BudgetsApi(api_client)
        budgets_response = budgets_api.get_budgets()

        # Fetch categories
        categories_api = ynab.api.categories_api.CategoriesApi(api_client)
        categories_response = categories_api.get_categories(budget_id)

        # Fetch transactions
        transactions_api = ynab.api.transactions_api.TransactionsApi(api_client)
        transactions_response = transactions_api.get_transactions(budget_id)

        # Fetch accounts
        accounts_api = ynab.api.accounts_api.AccountsApi(api_client)
        accounts_response = accounts_api.get_accounts(budget_id)

        return {
            'budgets': [
                {
                    'id': budget.id,
                    'name': budget.name,
                    'last_modified_on': budget.last_modified_on.isoformat() if budget.last_modified_on else None,
                    'first_month': budget.first_month,
                    'last_month': budget.last_month,
                    'date_format': convert_datetime_to_string(budget.date_format.__dict__) if budget.date_format else None,
                    'currency_format': convert_datetime_to_string(budget.currency_format.__dict__) if budget.currency_format else None
                }
                for budget in budgets_response.data.budgets
            ],
            'categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'category_group_id': cat.category_group_id,
                    'category_group_name': group.name,
                    'hidden': cat.hidden,
                    'original_category_group_id': cat.original_category_group_id,
                    'note': cat.note,
                    'budgeted': cat.budgeted,
                    'activity': cat.activity,
                    'balance': cat.balance,
                    'goal_type': cat.goal_type,
                    'goal_creation_month': cat.goal_creation_month,
                    'goal_target': cat.goal_target,
                    'goal_target_month': cat.goal_target_month,
                    'goal_percentage_complete': cat.goal_percentage_complete,
                    'deleted': cat.deleted
                }
                for group in categories_response.data.category_groups
                for cat in group.categories
            ],
            'transactions': [
                {
                    'id': txn.id,
                    'date': txn.var_date.isoformat() if hasattr(txn.var_date, 'isoformat') else str(txn.var_date),
                    'amount': txn.amount,
                    'memo': txn.memo,
                    'cleared': txn.cleared,
                    'approved': txn.approved,
                    'flag_color': txn.flag_color,
                    'flag_name': txn.flag_name,
                    'account_id': txn.account_id,
                    'account_name': txn.account_name,
                    'payee_id': txn.payee_id,
                    'payee_name': txn.payee_name,
                    'category_id': txn.category_id,
                    'category_name': txn.category_name,
                    'transfer_account_id': txn.transfer_account_id,
                    'transfer_transaction_id': txn.transfer_transaction_id,
                    'matched_transaction_id': txn.matched_transaction_id,
                    'import_id': txn.import_id,
                    'import_payee_name': txn.import_payee_name,
                    'import_payee_name_original': txn.import_payee_name_original,
                    'debt_transaction_type': txn.debt_transaction_type,
                    'deleted': txn.deleted,
                    'subtransactions': [
                        {
                            'id': sub.id,
                            'transaction_id': sub.transaction_id,
                            'amount': sub.amount,
                            'memo': sub.memo,
                            'payee_id': sub.payee_id,
                            'payee_name': sub.payee_name,
                            'category_id': sub.category_id,
                            'category_name': sub.category_name,
                            'transfer_account_id': sub.transfer_account_id,
                            'deleted': sub.deleted
                        }
                        for sub in txn.subtransactions
                    ] if hasattr(txn, 'subtransactions') and txn.subtransactions else []
                }
                for txn in transactions_response.data.transactions
            ],
            'accounts': [
                {
                    'id': account.id,
                    'name': account.name,
                    'type': account.type,
                    'on_budget': account.on_budget,
                    'closed': account.closed,
                    'note': account.note,
                    'balance': account.balance,
                    'cleared_balance': account.cleared_balance,
                    'uncleared_balance': account.uncleared_balance,
                    'transfer_payee_id': account.transfer_payee_id,
                    'direct_import_linked': account.direct_import_linked,
                    'direct_import_in_error': account.direct_import_in_error,
                    'last_reconciled_at': account.last_reconciled_at.isoformat() if account.last_reconciled_at else None,
                    'debt_interest_rates': convert_datetime_to_string(account.debt_interest_rates) if account.debt_interest_rates else None,
                    'debt_minimum_payments': convert_datetime_to_string(account.debt_minimum_payments) if account.debt_minimum_payments else None,
                    'debt_escrow_amounts': convert_datetime_to_string(account.debt_escrow_amounts) if account.debt_escrow_amounts else None,
                    'deleted': account.deleted
                }
                for account in accounts_response.data.accounts
            ],
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'budget_id': budget_id,
                'total_budgets': len(budgets_response.data.budgets),
                'total_categories': sum(len(group.categories) for group in categories_response.data.category_groups),
                'total_transactions': len(transactions_response.data.transactions),
                'total_accounts': len(accounts_response.data.accounts),
                'ynab_api_version': '1.0'  # You can update this as needed
            }
        }

def convert_datetime_to_string(obj):
    """Recursively convert datetime and date objects to strings for JSON serialization."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    else:
        return obj

def save_data_to_file(data: Dict[str, Any], filename: str) -> bool:
    """Save data to JSON file."""
    try:
        # Convert all datetime objects to strings
        json_data = convert_datetime_to_string(data)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, OSError) as e:
        st.error(f"Error saving file: {e}")
        return False

def load_data_from_file(filename: str) -> Dict[str, Any]:
    """Load data from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, OSError, json.JSONDecodeError) as e:
        st.error(f"Error loading file: {e}")
        return {}

def import_ynab_data_to_db(data: Dict[str, Any], budget_id: str) -> bool:
    """Import YNAB data directly into SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing YNAB data
        ynab_tables = ['ynab_transactions', 'ynab_subtransactions', 'ynab_categories',
                       'ynab_category_groups', 'ynab_payees', 'ynab_account', 'ynab_budgets']

        for table in ynab_tables:
            cursor.execute(f"DELETE FROM {table}")

        # Import budgets
        for budget in data.get('budgets', []):
            cursor.execute("""
                INSERT INTO ynab_budgets (
                    id, name, last_modified_on, first_month, last_month,
                    date_format_format, currency_format_iso_code,
                    currency_format_example_format, currency_format_decimal_digits,
                    currency_format_decimal_separator, currency_format_symbol_first,
                    currency_format_group_separator, currency_format_currency_symbol,
                    currency_format_display_symbol, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget['id'],
                budget['name'],
                budget.get('last_modified_on'),
                budget.get('first_month'),
                budget.get('last_month'),
                budget.get('date_format', {}).get('format'),
                budget.get('currency_format', {}).get('iso_code'),
                budget.get('currency_format', {}).get('example_format'),
                budget.get('currency_format', {}).get('decimal_digits'),
                budget.get('currency_format', {}).get('decimal_separator'),
                budget.get('currency_format', {}).get('symbol_first'),
                budget.get('currency_format', {}).get('group_separator'),
                budget.get('currency_format', {}).get('currency_symbol'),
                budget.get('currency_format', {}).get('display_symbol'),
                datetime.now().isoformat()
            ))

        # Import categories and category groups
        category_groups = set()
        for category in data.get('categories', []):
            # Track category groups
            category_groups.add((category['category_group_id'], category['category_group_name']))

            cursor.execute("""
                INSERT INTO ynab_categories (
                    id, name, category_group_id, category_group_name, full_name,
                    hidden, original_category_group_id, note, budgeted, activity,
                    balance, goal_type, goal_creation_month, goal_target,
                    goal_target_month, goal_percentage_complete, deleted, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                category['id'],
                category['name'],
                category['category_group_id'],
                category['category_group_name'],
                category.get('full_name'),
                category.get('hidden', False),
                category.get('original_category_group_id'),
                category.get('note'),
                category.get('budgeted', 0),
                category.get('activity', 0),
                category.get('balance', 0),
                category.get('goal_type'),
                category.get('goal_creation_month'),
                category.get('goal_target', 0),
                category.get('goal_target_month'),
                category.get('goal_percentage_complete'),
                category.get('deleted', False),
                datetime.now().isoformat()
            ))

        # Import category groups
        for group_id, group_name in category_groups:
            cursor.execute("""
                INSERT INTO ynab_category_groups (
                    id, name, updated_at
                ) VALUES (?, ?, ?)
            """, (group_id, group_name, datetime.now().isoformat()))

        # Import transactions and payees
        payees = set()
        for transaction in data.get('transactions', []):
            # Track payees
            if transaction.get('payee_id') and transaction.get('payee_name'):
                payees.add((transaction['payee_id'], transaction['payee_name']))

            cursor.execute("""
                INSERT INTO ynab_transactions (
                    id, date, amount, memo, cleared, approved, flag_color, flag_name,
                    account_id, account_name, payee_id, payee_name, category_id,
                    category_name, transfer_account_id, transfer_transaction_id,
                    matched_transaction_id, import_id, import_payee_name,
                    import_payee_name_original, debt_transaction_type, deleted, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction['id'],
                transaction['date'],
                transaction['amount'],
                transaction.get('memo'),
                transaction.get('cleared'),
                transaction.get('approved', False),
                transaction.get('flag_color'),
                transaction.get('flag_name'),
                transaction['account_id'],
                transaction['account_name'],
                transaction.get('payee_id'),
                transaction.get('payee_name'),
                transaction.get('category_id'),
                transaction.get('category_name'),
                transaction.get('transfer_account_id'),
                transaction.get('transfer_transaction_id'),
                transaction.get('matched_transaction_id'),
                transaction.get('import_id'),
                transaction.get('import_payee_name'),
                transaction.get('import_payee_name_original'),
                transaction.get('debt_transaction_type'),
                transaction.get('deleted', False),
                datetime.now().isoformat()
            ))

            # Import subtransactions
            for subtransaction in transaction.get('subtransactions', []):
                cursor.execute("""
                    INSERT INTO ynab_subtransactions (
                        id, transaction_id, amount, memo, payee_id, payee_name,
                        category_id, category_name, transfer_account_id, deleted, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    subtransaction['id'],
                    subtransaction['transaction_id'],
                    subtransaction['amount'],
                    subtransaction.get('memo'),
                    subtransaction.get('payee_id'),
                    subtransaction.get('payee_name'),
                    subtransaction.get('category_id'),
                    subtransaction.get('category_name'),
                    subtransaction.get('transfer_account_id'),
                    subtransaction.get('deleted', False),
                    datetime.now().isoformat()
                ))

        # Import payees
        for payee_id, payee_name in payees:
            cursor.execute("""
                INSERT INTO ynab_payees (
                    id, name, updated_at
                ) VALUES (?, ?, ?)
            """, (payee_id, payee_name, datetime.now().isoformat()))

        # Import accounts
        for account in data.get('accounts', []):
            cursor.execute("""
                INSERT INTO ynab_account (
                    budget_id, ynab_account_id, name, type, on_budget, closed, note,
                    balance, cleared_balance, uncleared_balance, transfer_payee_id,
                    direct_import_linked, direct_import_in_error, last_reconciled_at,
                    deleted, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget_id,  # Use the budget_id from the function parameter
                account['id'],
                account['name'],
                account['type'],
                account['on_budget'],
                account['closed'],
                account.get('note'),
                account['balance'],
                account['cleared_balance'],
                account['uncleared_balance'],
                account.get('transfer_payee_id'),
                account.get('direct_import_linked', False),
                account.get('direct_import_in_error', False),
                account.get('last_reconciled_at'),
                account.get('deleted', False),
                datetime.now().isoformat()
            ))

        # Create balance snapshots for linked accounts
        cursor.execute("""
            SELECT a.id as account_id, a.name as account_name, a.side, a.currency,
                   ya.balance as ynab_balance, ya.cleared_balance, ya.uncleared_balance
            FROM account a
            JOIN account_link_ynab al ON a.id = al.account_id
            JOIN ynab_account ya ON al.ynab_account_id = ya.ynab_account_id
            WHERE ya.budget_id = ?
        """, (budget_id,))

        linked_accounts = cursor.fetchall()

        for linked_account in linked_accounts:
            account_id = linked_account[0]
            account_name = linked_account[1]
            account_side = linked_account[2]
            account_currency = linked_account[3]
            ynab_balance = linked_account[4]
            cleared_balance = linked_account[5]
            uncleared_balance = linked_account[6]

            # Convert YNAB balance to cents (YNAB uses millidollars, we use cents)
            balance_cents = int(ynab_balance / 10)  # Convert millidollars to cents

            # Adjust balance based on account side (credit accounts show negative balances)
            if account_side == 'credit':
                balance_cents = -balance_cents

            # Create balance snapshot
            cursor.execute("""
                INSERT INTO balance_snapshot (
                    account_id, amount_cents, as_of_date, source, notes
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                account_id,
                balance_cents,
                datetime.now().strftime('%Y-%m-%d'),
                'YNAB Import',
                f'Imported from YNAB account: {account_name} (Cleared: ${cleared_balance/1000:.2f}, Uncleared: ${uncleared_balance/1000:.2f})'
            ))

        conn.commit()
        conn.close()
        return True

    except (sqlite3.Error, IOError) as e:
        st.error(f"Error importing data to database: {e}")
        return False

def get_ynab_data_from_db() -> Dict[str, Any]:
    """Get YNAB data from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get budgets
    cursor.execute("SELECT * FROM ynab_budgets")
    budgets_data = cursor.fetchall()
    budgets = []
    for budget in budgets_data:
        budgets.append({
            'id': budget[0],
            'name': budget[1],
            'last_modified_on': budget[2],
            'first_month': budget[3],
            'last_month': budget[4],
            'date_format': {'format': budget[5]} if budget[5] else None,
            'currency_format': {
                'iso_code': budget[6],
                'example_format': budget[7],
                'decimal_digits': budget[8],
                'decimal_separator': budget[9],
                'symbol_first': budget[10],
                'group_separator': budget[11],
                'currency_symbol': budget[12],
                'display_symbol': budget[13]
            } if budget[6] else None
        })

    # Get categories
    cursor.execute("SELECT * FROM ynab_categories")
    categories_data = cursor.fetchall()
    categories = []
    for cat in categories_data:
        categories.append({
            'id': cat[0],
            'name': cat[1],
            'category_group_id': cat[2],
            'category_group_name': cat[3],
            'full_name': cat[4],
            'hidden': bool(cat[5]),
            'original_category_group_id': cat[6],
            'note': cat[7],
            'budgeted': cat[8],
            'activity': cat[9],
            'balance': cat[10],
            'goal_type': cat[11],
            'goal_creation_month': cat[12],
            'goal_target': cat[13],
            'goal_target_month': cat[14],
            'goal_percentage_complete': cat[15],
            'deleted': bool(cat[16])
        })

    # Get transactions
    cursor.execute("SELECT * FROM ynab_transactions")
    transactions_data = cursor.fetchall()
    transactions = []
    for txn in transactions_data:
        transactions.append({
            'id': txn[0],
            'date': txn[1],
            'amount': txn[2],
            'memo': txn[3],
            'cleared': txn[4],
            'approved': bool(txn[5]),
            'flag_color': txn[6],
            'flag_name': txn[7],
            'account_id': txn[8],
            'account_name': txn[9],
            'payee_id': txn[10],
            'payee_name': txn[11],
            'category_id': txn[12],
            'category_name': txn[13],
            'transfer_account_id': txn[14],
            'transfer_transaction_id': txn[15],
            'matched_transaction_id': txn[16],
            'import_id': txn[17],
            'import_payee_name': txn[18],
            'import_payee_name_original': txn[19],
            'debt_transaction_type': txn[20],
            'deleted': bool(txn[21]),
            'subtransactions': []  # Subtransactions would need separate query
        })

    # Get accounts
    cursor.execute("SELECT * FROM ynab_accounts")
    accounts_data = cursor.fetchall()
    accounts = []
    for account in accounts_data:
        accounts.append({
            'id': account[0],
            'name': account[1],
            'type': account[2],
            'on_budget': bool(account[3]),
            'closed': bool(account[4]),
            'note': account[5],
            'balance': account[6],
            'cleared_balance': account[7],
            'uncleared_balance': account[8],
            'transfer_payee_id': account[9],
            'direct_import_linked': bool(account[10]),
            'direct_import_in_error': bool(account[11]),
            'last_reconciled_at': account[12],
            'debt_interest_rates': account[13],
            'debt_minimum_payments': account[14],
            'debt_escrow_amounts': account[15],
            'deleted': bool(account[16])
        })

    conn.close()

    return {
        'budgets': budgets,
        'categories': categories,
        'transactions': transactions,
        'accounts': accounts,
        'metadata': {
            'export_timestamp': datetime.now().isoformat(),
            'budget_id': budgets[0]['id'] if budgets else None,
            'total_budgets': len(budgets),
            'total_categories': len(categories),
            'total_transactions': len(transactions),
            'total_accounts': len(accounts),
            'data_source': 'sqlite_database'
        }
    }

def render():
    """Main render function for the YNAB Export Data tool."""
    st.title("📥 YNAB Data Export")
    st.write("Export live YNAB data to JSON files or directly to the database.")

    # Check API key
    if not os.getenv('YNAB_API_KEY'):
        st.error("❌ **YNAB API Key Missing**")
        st.markdown("""
        Your YNAB API key is not configured. Please:

        1. **Get your API key** from [YNAB Developer Settings](https://app.youneedabudget.com/settings/developer)
        2. **Add it to your environment** or create a `.env` file with:
           ```
           YNAB_API_KEY=your_api_key_here
           ```
        3. **Restart the application**
        """)
        return

    # Get budget selection
    try:
        budget_id, configuration, budget_name = get_budget_selection()
    except Exception as e:
        st.error(f"❌ **Error loading budgets**: {str(e)}")
        return

    st.write(f"📊 Selected budget: **{budget_name}**")

    # Export destination selection
    st.subheader("📁 Export Destination")
    export_destination = st.radio(
        "Choose export destination:",
        ["📄 JSON File", "🗄️ SQLite Database"],
        index=0,
        help="Export to a JSON file or directly import into the SQLite database"
    )

    if export_destination == "🗄️ SQLite Database":
        # Check if database exists
        if not os.path.exists('accounts.db'):
            st.error("❌ **Database not found**")
            st.markdown("""
            The accounts.db file doesn't exist. Please:

            1. **Create the database** using the account management tools
            2. **Or export to JSON File** instead
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

            1. **Create YNAB tables** using the database tools
            2. **Or export to JSON File** instead
            """)
            return

        st.success(f"✅ **Found YNAB tables in database** ({len(ynab_tables)} tables)")

        # Show database summary
        conn = get_db_connection()
        cursor = conn.cursor()

        st.write("📊 **Current Database Summary:**")
        for table in ynab_tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            st.write(f"• **{table_name}**: {count:,} records")

        conn.close()

        # Database import options
        st.subheader("🗄️ Database Import Settings")

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Import Options:**")
            st.write("• **Replace existing data**: All YNAB tables will be cleared and repopulated")
            st.write("• **Fresh data**: Always pulls the latest data from YNAB API")
            st.write("• **Complete import**: Includes budgets, categories, transactions, and accounts")

        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("🗄️ Import to Database", type="primary"):
                with st.spinner("Fetching live YNAB data and importing to database..."):
                    try:
                        # Fetch all data from live API
                        data = fetch_all_ynab_data(budget_id, configuration)

                        # Import to database
                        success = import_ynab_data_to_db(data, budget_id)

                        if success:
                            st.success("✅ **Data imported to database successfully!**")

                            # Show summary
                            metadata = data.get('metadata', {})
                            st.write("**Import Summary:**")
                            st.write(f"• **Budgets:** {metadata.get('total_budgets', 0)}")
                            st.write(f"• **Categories:** {metadata.get('total_categories', 0)}")
                            st.write(f"• **Transactions:** {metadata.get('total_transactions', 0)}")
                            st.write(f"• **Accounts:** {metadata.get('total_accounts', 0)}")
                            st.write(f"• **Import Time:** {metadata.get('export_timestamp', 'Unknown')}")
                            st.write("• **Data Source:** Live YNAB API")

                            # Show balance snapshots created
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                SELECT COUNT(*) FROM balance_snapshot
                                WHERE source = 'YNAB Import' AND as_of_date = ?
                            """, (datetime.now().strftime('%Y-%m-%d'),))
                            balance_snapshots_count = cursor.fetchone()[0]
                            st.write(f"• **Balance Snapshots Created:** {balance_snapshots_count}")
                            conn.close()

                            # Show updated database summary
                            conn = get_db_connection()
                            cursor = conn.cursor()

                            st.write("📊 **Updated Database Summary:**")
                            for table in ynab_tables:
                                table_name = table[0]
                                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                                count = cursor.fetchone()[0]
                                st.write(f"• **{table_name}**: {count:,} records")

                            conn.close()
                        else:
                            st.error("❌ **Failed to import data to database**")

                    except Exception as e:
                        st.error(f"❌ **Error importing data**: {str(e)}")

    else:
        # JSON file export (original functionality)
        st.subheader("📄 JSON File Export Settings")

        col1, col2 = st.columns([3, 1])
        with col1:
            filename = st.text_input(
                "Export filename",
                value=f"ynab_data_{budget_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                help="Filename for the exported JSON data"
            )
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("📥 Export to JSON", type="primary"):
                with st.spinner("Fetching live YNAB data..."):
                    try:
                        # Fetch all data from live API
                        data = fetch_all_ynab_data(budget_id, configuration)

                        # Save to file
                        if save_data_to_file(data, filename):
                            st.success("✅ **Data exported to JSON successfully!**")
                            st.write(f"📁 **File saved as:** `{filename}`")

                            # Show summary
                            metadata = data.get('metadata', {})
                            st.write("**Export Summary:**")
                            st.write(f"• **Budgets:** {metadata.get('total_budgets', 0)}")
                            st.write(f"• **Categories:** {metadata.get('total_categories', 0)}")
                            st.write(f"• **Transactions:** {metadata.get('total_transactions', 0)}")
                            st.write(f"• **Accounts:** {metadata.get('total_accounts', 0)}")
                            st.write(f"• **Export Time:** {metadata.get('export_timestamp', 'Unknown')}")
                            st.write("• **Data Source:** Live YNAB API")

                            # Offer download
                            with open(filename, 'r', encoding='utf-8') as f:
                                file_content = f.read()

                            st.download_button(
                                label="📥 Download JSON File",
                                data=file_content,
                                file_name=filename,
                                mime="application/json"
                            )
                        else:
                            st.error("❌ **Failed to save data to file**")

                    except Exception as e:
                        st.error(f"❌ **Error exporting data**: {str(e)}")

    # Show existing JSON files
    st.subheader("📋 Existing JSON Export Files")

    # Look for existing YNAB export files
    json_files = [f for f in os.listdir('.') if f.startswith('ynab_data_') and f.endswith('.json')]

    if json_files:
        st.write(f"Found {len(json_files)} existing JSON export files:")

        for file in sorted(json_files, reverse=True):  # Show newest first
            try:
                # Load file to show metadata
                data = load_data_from_file(file)
                metadata = data.get('metadata', {})

                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.write(f"**{file}**")
                with col2:
                    st.write(f"📊 {metadata.get('total_transactions', 0)} txns")
                with col3:
                    st.write(f"📂 {metadata.get('total_categories', 0)} cats")
                with col4:
                    if st.button("📥 Download", key=f"download_{file}"):
                        with open(file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        st.download_button(
                            label="📥 Download",
                            data=file_content,
                            file_name=file,
                            mime="application/json",
                            key=f"dl_{file}"
                        )

                # Show export timestamp
                export_time = metadata.get('export_timestamp', 'Unknown')
                if export_time != 'Unknown':
                    try:
                        export_dt = datetime.fromisoformat(export_time)
                        st.caption(f"Exported: {export_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except ValueError:
                        st.caption(f"Exported: {export_time}")

                st.markdown("---")

            except (IOError, OSError, json.JSONDecodeError) as e:
                st.write(f"**{file}** (Error reading: {e})")
                st.markdown("---")
    else:
        st.info("No existing JSON export files found. Create your first export above!")

    # Help section
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Always fetches LIVE data from YNAB API (never cached)
        - Exports ALL YNAB data for a selected budget
        - Includes budgets, categories, transactions, and accounts
        - Creates a complete snapshot of your current YNAB data

        **Export Destinations:**
        - **JSON File**: Creates a downloadable JSON file for offline use
        - **SQLite Database**: Directly imports data into your local database and creates balance snapshots for linked accounts

        **What's included in the export:**
        - **Budgets**: All budget information and settings
        - **Categories**: All categories with their groups and metadata
        - **Transactions**: All transactions with full details
        - **Accounts**: All accounts with balances and settings
        - **Balance Snapshots**: For accounts linked to YNAB accounts, creates balance_snapshot records
        - **Metadata**: Export timestamp and summary statistics

        **How to use the exported data:**
        - **JSON files**: Other YNAB tools can load this data instead of making API calls
        - **Database**: Other tools can query the database directly for faster access
        - **Offline analysis**: Useful when API rate limits are hit or for offline work
        - **Data backup**: Provides consistent data snapshot across all tools

        **File format:**
        - Standard JSON format
        - Human-readable with proper indentation
        - Includes all transaction details and metadata
        """)

if __name__ == "__main__":
    render()
