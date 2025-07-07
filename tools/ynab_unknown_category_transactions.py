import streamlit as st
import ynab
import os
from ynab.api.transactions_api import TransactionsApi
from ynab.api.budgets_api import BudgetsApi
from ynab.api.categories_api import CategoriesApi
from collections import defaultdict

def render():
    ynab_api_key = os.getenv('YNAB_API_KEY')

    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

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
            # Use session state to store unknown transactions and grouped data
            if 'ynab_unknown_txns' not in st.session_state:
                st.session_state['ynab_unknown_txns'] = None
                st.session_state['ynab_unknown_grouped'] = None
                st.session_state['ynab_unknown_budget_id'] = None

            fetch_clicked = st.button("Fetch Unknown Category Transactions")
            should_fetch = (
                fetch_clicked or
                st.session_state['ynab_unknown_txns'] is None or
                st.session_state['ynab_unknown_budget_id'] != selected_budget_id
            )
            if should_fetch:
                with st.spinner("Fetching transactions..."):
                    api_instance = TransactionsApi(api_client)
                    categories_api = CategoriesApi(api_client)
                    # Fetch categories and build mapping
                    categories_response = categories_api.get_categories(selected_budget_id)
                    category_mapping = {}
                    for group in categories_response.data.category_groups:
                        for cat in group.categories:
                            category_mapping[cat.id] = cat.name
                    # Fetch transactions
                    response = api_instance.get_transactions(selected_budget_id)
                    transactions = response.data.transactions

                    unknown_transactions = [
                        t for t in transactions if t.category_id not in category_mapping
                    ]

                    from collections import defaultdict
                    grouped = defaultdict(list)
                    for t in unknown_transactions:
                        name = t.payee_name or t.memo or "(No Name)"
                        grouped[name].append(t)

                    st.session_state['ynab_unknown_txns'] = unknown_transactions
                    st.session_state['ynab_unknown_grouped'] = grouped
                    st.session_state['ynab_unknown_budget_id'] = selected_budget_id
            else:
                unknown_transactions = st.session_state['ynab_unknown_txns']
                grouped = st.session_state['ynab_unknown_grouped']

            if unknown_transactions is not None:
                st.success(f"Found {len(unknown_transactions)} transactions with unknown category!")

                sort_option = st.selectbox(
                    "Sort groups by:",
                    ["Payee/Description (A-Z)", "# of Transactions (Most First)"]
                )
                if sort_option == "Payee/Description (A-Z)":
                    group_keys = sorted(grouped.keys(), key=lambda n: n.lower())
                else:
                    group_keys = sorted(grouped.keys(), key=lambda n: len(grouped[n]), reverse=True)

                for name in group_keys:
                    txns = grouped[name]
                    with st.expander(f"{name} ({len(txns)})", expanded=False):
                        for transaction in sorted(txns, key=lambda t: t.var_date):
                            st.write(f"{transaction.var_date} | {transaction.amount / 1000.0}")

    except ynab.ApiException as e:
        st.error(f"Error: {e.reason}")