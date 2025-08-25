import streamlit as st
import os

# Import ynab only when needed to avoid import errors
try:
    import ynab
    from ynab.api.transactions_api import TransactionsApi
    from ynab.api.budgets_api import BudgetsApi
    from ynab.api.accounts_api import AccountsApi
    from ynab.models.save_transaction_with_optional_fields import SaveTransactionWithOptionalFields
    from ynab.models.post_transactions_wrapper import PostTransactionsWrapper
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

def render():
    if not YNAB_AVAILABLE:
        st.error("YNAB module not available. Please install it with: pip install ynab")
        st.stop()

    ynab_api_key = os.getenv('YNAB_API_KEY')

    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    # 2. Configure API
    configuration = ynab.Configuration(
        access_token = ynab_api_key
    )

    try:
        with ynab.ApiClient(configuration) as api_client:
            budgets_api = BudgetsApi(api_client)
            budgets_response = budgets_api.get_budgets()
            budgets = budgets_response.data.budgets
            budget_names = [budget.name for budget in budgets]
            selected_budget_name = st.selectbox("Select a budget", budget_names)
            selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]

            if selected_budget_id:
                accounts_api = AccountsApi(api_client)
                accounts_response = accounts_api.get_accounts(selected_budget_id)
                accounts = accounts_response.data.accounts
                account_names = [account.name for account in accounts]
                selected_account_name = st.selectbox("Select an account", account_names)
                selected_account_id = [account.id for account in accounts if account.name == selected_account_name][0]

                payee_name = st.text_input("Payee Name")
                amount = st.number_input("Amount (in milliunits, e.g., $12.34 is 12340)", value=0, step=1)
                date = st.date_input("Date")

                if st.button("Create Transaction"):
                    with st.spinner("Creating transaction..."):
                        transactions_api = TransactionsApi(api_client)
                        transaction = SaveTransactionWithOptionalFields(
                            account_id=selected_account_id,
                            date=date.isoformat(),
                            amount=int(amount),
                            payee_name=payee_name,
                            cleared='cleared'
                        )
                        wrapper = PostTransactionsWrapper(transaction=transaction)
                        transactions_api.create_transaction(selected_budget_id, wrapper)
                        st.success("Transaction created successfully!")

    except ynab.ApiException as e:
        st.error(f"Error: {e.reason}")