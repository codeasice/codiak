import streamlit as st
import ynab
import os
from ynab.api.transactions_api import TransactionsApi
from ynab.api.budgets_api import BudgetsApi

def render():
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
            if st.button("Fetch Transactions"):
                with st.spinner("Fetching transactions..."):
                    with ynab.ApiClient(configuration) as api_client:
                        api_instance = TransactionsApi(api_client)
                        response = api_instance.get_transactions(selected_budget_id)
                        transactions = response.data.transactions

                        st.success(f"Found {len(transactions)} transactions!")
                        for transaction in transactions:
                            st.write(f"- {transaction.var_date} | {transaction.payee_name} | {transaction.amount / 1000.0}")

    except ynab.ApiException as e:
        st.error(f"Error: {e.reason}")