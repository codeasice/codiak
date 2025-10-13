import streamlit as st
import os
import json
from datetime import datetime, date
from typing import Dict, List, Any

# Import ynab only when needed to avoid import errors
try:
    import ynab
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

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
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False

def load_data_from_file(filename: str) -> Dict[str, Any]:
    """Load data from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return {}

def render():
    """Main render function for the YNAB Export Data tool."""
    st.title("📥 YNAB Data Export")
    st.write("Export all YNAB data to a JSON file for use by other tools.")

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

    # File name input
    st.subheader("📁 Export Settings")

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
        if st.button("📥 Export Data", type="primary"):
            with st.spinner("Fetching all YNAB data..."):
                try:
                    # Fetch all data
                    data = fetch_all_ynab_data(budget_id, configuration)

                    # Save to file
                    if save_data_to_file(data, filename):
                        st.success(f"✅ **Data exported successfully!**")
                        st.write(f"📁 **File saved as:** `{filename}`")

                        # Show summary
                        metadata = data.get('metadata', {})
                        st.write("**Export Summary:**")
                        st.write(f"• **Budgets:** {metadata.get('total_budgets', 0)}")
                        st.write(f"• **Categories:** {metadata.get('total_categories', 0)}")
                        st.write(f"• **Transactions:** {metadata.get('total_transactions', 0)}")
                        st.write(f"• **Accounts:** {metadata.get('total_accounts', 0)}")
                        st.write(f"• **Export Time:** {metadata.get('export_timestamp', 'Unknown')}")

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

    # Show existing files
    st.subheader("📋 Existing Export Files")

    # Look for existing YNAB export files
    json_files = [f for f in os.listdir('.') if f.startswith('ynab_data_') and f.endswith('.json')]

    if json_files:
        st.write(f"Found {len(json_files)} existing export files:")

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
                    except:
                        st.caption(f"Exported: {export_time}")

                st.markdown("---")

            except Exception as e:
                st.write(f"**{file}** (Error reading: {e})")
                st.markdown("---")
    else:
        st.info("No existing export files found. Create your first export above!")

    # Help section
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Exports ALL YNAB data for a selected budget to a JSON file
        - Includes budgets, categories, transactions, and accounts
        - Creates a complete snapshot of your YNAB data

        **What's included in the export:**
        - **Budgets**: All budget information and settings
        - **Categories**: All categories with their groups and metadata
        - **Transactions**: All transactions with full details
        - **Accounts**: All accounts with balances and settings
        - **Metadata**: Export timestamp and summary statistics

        **How to use the exported data:**
        - Other YNAB tools can load this data instead of making API calls
        - Useful for offline analysis or when API rate limits are hit
        - Provides consistent data snapshot across all tools

        **File format:**
        - Standard JSON format
        - Human-readable with proper indentation
        - Includes all transaction details and metadata
        """)

if __name__ == "__main__":
    render()
